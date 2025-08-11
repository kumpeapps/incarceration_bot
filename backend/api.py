"""
FastAPI Backend for Incarceration Bot Frontend
"""

from datetime import datetime, timedelta
from typing import List, Optional
import os
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import jwt
from passlib.context import CryptContext

# Import existing models
from models.Inmate import Inmate
from models.Monitor import Monitor
from models.MonitorLink import MonitorLink
from models.MonitorInmateLink import MonitorInmateLink
from models.Jail import Jail
from models.User import User
import database_connect as db

app = FastAPI(title="Incarceration Bot API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Helper function to format dates without timezone conversion
def format_date_only(date_obj):
    """Format date object as YYYY-MM-DD string without timezone conversion"""
    if date_obj is None:
        return None
    return date_obj.strftime('%Y-%m-%d') if hasattr(date_obj, 'strftime') else str(date_obj)

# Pydantic models for API
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"

class InmateResponse(BaseModel):
    id: int
    name: str
    race: str
    sex: str
    cell_block: Optional[str]
    arrest_date: Optional[str]
    held_for_agency: Optional[str]
    dob: str
    hold_reasons: str
    is_juvenile: bool
    release_date: str
    in_custody_date: str
    jail_id: str
    
    class Config:
        from_attributes = True

class MonitorResponse(BaseModel):
    id: int
    name: str
    arrest_date: Optional[str]
    release_date: Optional[str]
    arrest_reason: Optional[str]
    arresting_agency: Optional[str]
    jail: Optional[str]
    enable_notifications: int
    notify_method: Optional[str]
    notify_address: str
    
    class Config:
        from_attributes = True

class MonitorCreate(BaseModel):
    name: str
    notify_address: str
    notify_method: str = "pushover"
    enable_notifications: int = 1

class MonitorLinkCreate(BaseModel):
    linked_monitor_id: int
    link_reason: Optional[str] = None

class MonitorInmateLinkCreate(BaseModel):
    inmate_id: int
    is_excluded: bool = False
    link_reason: Optional[str] = None

class MonitorInmateLinkUpdate(BaseModel):
    is_excluded: bool
    link_reason: Optional[str] = None

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    limit: int
    pages: int

class DashboardStats(BaseModel):
    total_inmates: int
    total_active_inmates: int
    total_monitors: int
    total_jails: int
    active_jails: int
    recent_arrests: int
    recent_releases: int

# Database dependency
def get_db():
    session = db.new_session()
    try:
        yield session
    finally:
        session.close()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Authentication endpoints
@app.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user or not user.verify_password(login_data.password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }

@app.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Successfully logged out"}

@app.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user.to_dict()

# Dashboard endpoints
@app.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_inmates = db.query(Inmate).count()
    total_active_inmates = db.query(Inmate).filter(Inmate.release_date == "").count()
    total_monitors = db.query(Monitor).count()
    total_jails = db.query(Jail).count()
    active_jails = db.query(Jail).filter(Jail.active == True).count()
    
    # Mock recent data for now
    recent_arrests = 15
    recent_releases = 8
    
    return DashboardStats(
        total_inmates=total_inmates,
        total_active_inmates=total_active_inmates,
        total_monitors=total_monitors,
        total_jails=total_jails,
        active_jails=active_jails,
        recent_arrests=recent_arrests,
        recent_releases=recent_releases
    )

# Inmates endpoints
@app.get("/inmates")
async def get_inmates(
    page: int = 1,
    limit: int = 50,
    name: Optional[str] = None,
    jail_id: Optional[str] = None,
    current_custody: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print(f"🔥 ENTRY POINT: name='{name}', jail_id='{jail_id}', current_custody={current_custody}")
    from sqlalchemy import text
    
    # Allow showing current custody records without requiring other filters
    # But require at least one search filter for historical data
    print(f"🚨 DEBUG INMATES ENDPOINT: name={name}, jail_id={jail_id}, current_custody={current_custody}")
    print(f"🚨 DEBUG: any([name, jail_id]) = {any([name, jail_id])}")
    
    # If no search filters and not current custody, return empty
    if not any([name, jail_id]) and current_custody is not True:
        print("🚨 DEBUG: Returning empty response - no search filters and not current custody")
        return PaginatedResponse(
            items=[],
            total=0,
            page=page,
            limit=limit,
            pages=0
        )
    
    # Simple query to get all inmates - no grouping needed since data is now clean
    base_query = """
        SELECT * FROM inmates
    """
    
    conditions = []
    params = {}
    
    if name:
        conditions.append("name LIKE :name")
        params['name'] = f"%{name}%"
    if jail_id:
        conditions.append("jail_id = :jail_id")
        params['jail_id'] = jail_id
    if current_custody is True:
        conditions.append("DATE(in_custody_date) = CURDATE()")
    elif current_custody is False:
        conditions.append("DATE(in_custody_date) < CURDATE()")
    
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    
    base_query += " ORDER BY in_custody_date DESC"
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM ({base_query}) as counted"
    total_result = db.execute(text(count_query), params)
    total_row = total_result.fetchone()
    total = total_row.total if total_row else 0
    
    # Get paginated results
    paginated_query = base_query + f" LIMIT {limit} OFFSET {(page - 1) * limit}"
    result = db.execute(text(paginated_query), params)
    
    enhanced_inmates = []
    for row in result:
        # Convert row to dict
        inmate_dict = {
            'id': row.idinmates,
            'name': row.name,
            'race': row.race,
            'sex': row.sex,
            'cell_block': row.cell_block,
            'arrest_date': format_date_only(row.arrest_date),
            'held_for_agency': row.held_for_agency,
            'mugshot': row.mugshot,
            'dob': row.dob,
            'hold_reasons': row.hold_reasons,
            'is_juvenile': row.is_juvenile,
            'release_date': row.release_date,
            'in_custody_date': format_date_only(row.in_custody_date),
            'jail_id': row.jail_id,
            'hide_record': row.hide_record
        }
        
        # Get enhanced info for this person
        enhancement_query = text("""
            SELECT COUNT(*) as total_records,
                   MIN(in_custody_date) as first_booking,
                   MAX(in_custody_date) as latest_booking,
                   GROUP_CONCAT(DISTINCT release_date) as all_releases
            FROM inmates 
            WHERE name = :name AND dob = :dob AND jail_id = :jail_id
        """)
        
        enhancement_result = db.execute(enhancement_query, {
            'name': row.name,
            'dob': row.dob,
            'jail_id': row.jail_id
        })
        enhancement_data = enhancement_result.fetchone()
        
        # Determine actual status with null checks
        if enhancement_data:
            has_release = enhancement_data.all_releases and enhancement_data.all_releases.strip()
            actual_status = 'released' if has_release else 'in_custody'
            
            # Add enhanced fields
            inmate_dict['actual_status'] = actual_status
            inmate_dict['total_records'] = enhancement_data.total_records
            inmate_dict['first_booking_date'] = format_date_only(enhancement_data.first_booking)
        else:
            # Fallback if query fails
            inmate_dict['actual_status'] = 'released' if (row.release_date and row.release_date.strip()) else 'in_custody'
            inmate_dict['total_records'] = 1
            inmate_dict['first_booking_date'] = format_date_only(row.in_custody_date)
        
        enhanced_inmates.append(inmate_dict)
    
    return PaginatedResponse(
        items=enhanced_inmates,
        total=total,
        page=page,
        limit=limit,
        pages=(total + limit - 1) // limit
    )

# Search inmates for linking
@app.get("/inmates/search")
async def search_inmates(
    q: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search inmates by name for linking purposes"""
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    
    # Search by name (case-insensitive)
    inmates = db.query(Inmate).filter(
        Inmate.name.ilike(f"%{q}%")
    ).limit(50).all()
    
    results = []
    for inmate in inmates:
        results.append({
            "id": inmate.id,
            "name": inmate.name,
            "dob": inmate.dob,
            "jail_id": inmate.jail_id,
            "arrest_date": format_date_only(inmate.arrest_date),
            "actual_status": 'released' if (inmate.release_date and inmate.release_date.strip()) else 'in_custody'
        })
    
    return results

@app.get("/inmates/{inmate_id}")
async def get_inmate(
    inmate_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from sqlalchemy import text
    
    # Get the specific inmate
    inmate_query = text("SELECT * FROM inmates WHERE idinmates = :inmate_id")
    result = db.execute(inmate_query, {'inmate_id': inmate_id})
    row = result.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Inmate not found")
    
    # Convert to dict
    inmate_dict = {
        'id': row.idinmates,
        'name': row.name,
        'race': row.race,
        'sex': row.sex,
        'cell_block': row.cell_block,
        'arrest_date': format_date_only(row.arrest_date),
        'held_for_agency': row.held_for_agency,
        'mugshot': row.mugshot,
        'dob': row.dob,
        'hold_reasons': row.hold_reasons,
        'is_juvenile': row.is_juvenile,
        'release_date': row.release_date,
        'in_custody_date': format_date_only(row.in_custody_date),
        'jail_id': row.jail_id,
        'hide_record': row.hide_record
    }
    
    # Get enhanced custody information
    enhancement_query = text("""
        SELECT COUNT(*) as total_records,
               MIN(in_custody_date) as first_booking,
               GROUP_CONCAT(DISTINCT in_custody_date ORDER BY in_custody_date) as all_custody_dates
        FROM inmates 
        WHERE name = :name AND dob = :dob AND jail_id = :jail_id
    """)
    
    enhancement_result = db.execute(enhancement_query, {
        'name': row.name,
        'dob': row.dob,
        'jail_id': row.jail_id
    })
    enhancement_data = enhancement_result.fetchone()
    
    # Always use the individual record's release_date for status determination
    inmate_dict['actual_status'] = 'released' if (row.release_date and row.release_date.strip()) else 'in_custody'
    
    if enhancement_data:
        inmate_dict['total_records'] = enhancement_data.total_records
        inmate_dict['first_booking_date'] = format_date_only(enhancement_data.first_booking)
        
        # Parse custody dates
        if enhancement_data.all_custody_dates:
            custody_dates = enhancement_data.all_custody_dates.split(',')
            inmate_dict['all_custody_dates'] = custody_dates
        else:
            inmate_dict['all_custody_dates'] = []
    else:
        inmate_dict['total_records'] = 1
        inmate_dict['first_booking_date'] = format_date_only(row.in_custody_date)
        inmate_dict['all_custody_dates'] = [format_date_only(row.in_custody_date)] if row.in_custody_date else []
    
    return inmate_dict

# Monitors endpoints
@app.get("/monitors")
async def get_monitors(
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Admin sees all monitors, users see only their own
    if current_user.role == "admin":
        query = db.query(Monitor)
    else:
        query = db.query(Monitor).filter(Monitor.user_id == current_user.id)
    
    total = query.count()
    monitors = query.offset((page - 1) * limit).limit(limit).all()
    
    return PaginatedResponse(
        items=[monitor.to_dict() for monitor in monitors],
        total=total,
        page=page,
        limit=limit,
        pages=(total + limit - 1) // limit
    )

@app.post("/monitors")
async def create_monitor(
    monitor_data: MonitorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    monitor = Monitor(
        name=monitor_data.name,
        notify_address=monitor_data.notify_address,
        notify_method=monitor_data.notify_method,
        enable_notifications=monitor_data.enable_notifications,
        user_id=current_user.id
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return monitor.to_dict()

@app.get("/monitors/{monitor_id}")
async def get_monitor(
    monitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    # Users can only view their own monitors, admins can view any
    if current_user.role != "admin" and monitor.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this monitor")
    
    return monitor.to_dict()

@app.put("/monitors/{monitor_id}")
async def update_monitor(
    monitor_id: int,
    monitor_data: MonitorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    # Users can only edit their own monitors, admins can edit any
    if current_user.role != "admin" and monitor.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this monitor")
    
    # Update monitor fields
    monitor.name = monitor_data.name
    monitor.notify_address = monitor_data.notify_address
    monitor.notify_method = monitor_data.notify_method
    monitor.enable_notifications = monitor_data.enable_notifications
    
    db.commit()
    db.refresh(monitor)
    return monitor.to_dict()

@app.delete("/monitors/{monitor_id}")
async def delete_monitor(
    monitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    # Users can only delete their own monitors, admins can delete any
    if current_user.role != "admin" and monitor.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this monitor")
    
    db.delete(monitor)
    db.commit()
    return {"message": "Monitor deleted successfully"}

# Jails endpoints
@app.get("/jails")
async def get_jails(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    jails = db.query(Jail).all()
    return [{"id": jail.id, "jail_name": jail.jail_name, "state": jail.state, 
             "jail_id": jail.jail_id, "active": jail.active} for jail in jails]

# Users endpoints (admin only)
@app.get("/users")
async def get_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = db.query(User).all()
    return [user.to_dict() for user in users]

@app.post("/users")
async def create_user(user_data: UserCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=User.hash_password(user_data.password),
        role=user_data.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user.to_dict()

@app.put("/users/{user_id}")
async def update_user(user_id: int, user_data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user fields
    if "username" in user_data:
        # Check if username already exists for other users
        existing_user = db.query(User).filter(User.username == user_data["username"], User.id != user_id).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        user.username = user_data["username"]
    
    if "email" in user_data:
        # Check if email already exists for other users
        existing_email = db.query(User).filter(User.email == user_data["email"], User.id != user_id).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")
        user.email = user_data["email"]
    
    if "role" in user_data:
        user.role = user_data["role"]
    
    if "password" in user_data and user_data["password"]:
        user.hashed_password = User.hash_password(user_data["password"])
    
    db.commit()
    db.refresh(user)
    
    return user.to_dict()

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

@app.get("/users/{user_id}/monitors")
async def get_user_monitors(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    monitors = db.query(Monitor).filter(Monitor.user_id == user_id).all()
    return [monitor.to_dict() for monitor in monitors]

@app.put("/monitors/{monitor_id}/assign/{user_id}")
async def assign_monitor_to_user(
    monitor_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    monitor.user_id = user_id
    db.commit()
    return {"message": f"Monitor assigned to user {user.username}"}

# Monitor linking endpoints
@app.post("/monitors/{monitor_id}/link")
async def link_monitor(
    monitor_id: int,
    link_data: MonitorLinkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if primary monitor exists and user has access
    primary_monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not primary_monitor:
        raise HTTPException(status_code=404, detail="Primary monitor not found")
    
    if current_user.role != "admin" and primary_monitor.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to link this monitor")
    
    # Check if linked monitor exists
    linked_monitor = db.query(Monitor).filter(Monitor.id == link_data.linked_monitor_id).first()
    if not linked_monitor:
        raise HTTPException(status_code=404, detail="Linked monitor not found")
    
    # Create the link
    link = MonitorLink(
        primary_monitor_id=monitor_id,
        linked_monitor_id=link_data.linked_monitor_id,
        linked_by_user_id=current_user.id,
        link_reason=link_data.link_reason
    )
    db.add(link)
    db.commit()
    return {"message": "Monitors linked successfully"}

@app.get("/monitors/{monitor_id}/inmate-record")
async def get_monitor_as_inmate_record(
    monitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from sqlalchemy import text, or_
    
    # Get the primary monitor
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    if current_user.role != "admin" and monitor.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this monitor")
    
    # Get all linked monitors (both directions)
    linked_monitor_ids = []
    
    # Get monitors linked TO this one
    primary_links = db.query(MonitorLink).filter(MonitorLink.primary_monitor_id == monitor_id).all()
    linked_monitor_ids.extend([link.linked_monitor_id for link in primary_links])
    
    # Get monitors where this one is linked FROM
    secondary_links = db.query(MonitorLink).filter(MonitorLink.linked_monitor_id == monitor_id).all()
    linked_monitor_ids.extend([link.primary_monitor_id for link in secondary_links])
    
    # Include the original monitor
    all_monitor_ids = [monitor_id] + linked_monitor_ids
    
    # Get all monitors
    all_monitors = db.query(Monitor).filter(Monitor.id.in_(all_monitor_ids)).all()
    
    # Get all names to search for
    all_names = [m.name for m in all_monitors]
    
    # Search for incarceration records for all these names
    inmate_query = """
        SELECT i1.* FROM inmates i1
        INNER JOIN (
            SELECT name, dob, jail_id, MAX(in_custody_date) as latest_date
            FROM inmates
            WHERE name IN :names
            GROUP BY name, dob, jail_id
        ) i2 ON i1.name = i2.name 
               AND i1.dob = i2.dob 
               AND i1.jail_id = i2.jail_id 
               AND i1.in_custody_date = i2.latest_date
        ORDER BY i1.in_custody_date DESC
    """
    
    result = db.execute(text(inmate_query), {"names": tuple(all_names) if all_names else ("",)})
    
    incarceration_records = []
    for row in result:
        # Convert row to dict
        record = {
            'id': row.idinmates,
            'name': row.name,
            'race': row.race,
            'sex': row.sex,
            'cell_block': row.cell_block,
            'arrest_date': format_date_only(row.arrest_date),
            'held_for_agency': row.held_for_agency,
            'mugshot': row.mugshot,
            'dob': row.dob,
            'hold_reasons': row.hold_reasons,
            'is_juvenile': row.is_juvenile,
            'release_date': row.release_date,
            'in_custody_date': format_date_only(row.in_custody_date),
            'jail_id': row.jail_id,
            'hide_record': row.hide_record
        }
        
        # Determine status
        record['actual_status'] = 'released' if (row.release_date and row.release_date.strip()) else 'in_custody'
        incarceration_records.append(record)
    
    return {
        "primary_monitor": monitor.to_dict(),
        "linked_monitors": [m.to_dict() for m in all_monitors if m.id != monitor_id],
        "all_names": all_names,
        "incarceration_records": incarceration_records,
        "total_records": len(incarceration_records)
    }

# Monitor-Inmate Link Management Endpoints
@app.get("/monitors/{monitor_id}/inmate-links")
async def get_monitor_inmate_links(
    monitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all manual inmate links for a monitor"""
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    if current_user.role != "admin" and monitor.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this monitor")
    
    links = db.query(MonitorInmateLink).filter(MonitorInmateLink.monitor_id == monitor_id).all()
    return [link.to_dict() for link in links]

@app.get("/monitors/{monitor_id}/inmate-links-detailed")
async def get_monitor_inmate_links_detailed(
    monitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all manual inmate links for a monitor with detailed inmate information"""
    from sqlalchemy import text
    
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    if current_user.role != "admin" and monitor.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this monitor")
    
    # Get links with detailed inmate information
    query = text("""
        SELECT 
            ml.*,
            i.name as inmate_name,
            i.race as inmate_race,
            i.sex as inmate_sex,
            i.dob as inmate_dob,
            i.mugshot as inmate_mugshot,
            i.jail_id as inmate_jail_id,
            i.arrest_date as latest_arrest_date,
            i.release_date as latest_release_date,
            i.in_custody_date as latest_custody_date,
            i.hold_reasons as latest_charges,
            CASE WHEN i.release_date IS NULL OR i.release_date = '' THEN 'in_custody' ELSE 'released' END as actual_status
        FROM monitor_inmate_links ml
        LEFT JOIN inmates i ON ml.inmate_id = i.idinmates
        WHERE ml.monitor_id = :monitor_id
        ORDER BY ml.created_at DESC
    """)
    
    result = db.execute(query, {"monitor_id": monitor_id})
    
    enriched_links = []
    for row in result:
        link_data = {
            'id': row.id,
            'monitor_id': row.monitor_id,
            'inmate_id': row.inmate_id,
            'linked_by_user_id': row.linked_by_user_id,
            'is_excluded': row.is_excluded,
            'link_reason': row.link_reason,
            'created_at': row.created_at.isoformat() if row.created_at else None,
            'updated_at': row.updated_at.isoformat() if row.updated_at else None,
            'inmate_details': {
                'name': row.inmate_name,
                'race': row.inmate_race,
                'sex': row.inmate_sex,
                'dob': row.inmate_dob,
                'mugshot': row.inmate_mugshot,
                'jail_id': row.inmate_jail_id,
                'latest_arrest_date': format_date_only(row.latest_arrest_date),
                'latest_release_date': row.latest_release_date,
                'latest_custody_date': format_date_only(row.latest_custody_date),
                'latest_charges': row.latest_charges,
                'current_status': row.actual_status
            } if row.inmate_name else None
        }
        enriched_links.append(link_data)
    
    return enriched_links

@app.get("/monitors/{monitor_id}/inmate-history")
async def get_monitor_inmate_history(
    monitor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all historical incarceration records for linked inmates"""
    from sqlalchemy import text
    
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    if current_user.role != "admin" and monitor.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this monitor")
    
    # Get all incarceration records for linked inmates
    query = text("""
        SELECT 
            i.*,
            CASE WHEN i.release_date IS NULL OR i.release_date = '' THEN 'in_custody' ELSE 'released' END as actual_status,
            ml.is_excluded,
            ml.link_reason
        FROM inmates i
        INNER JOIN monitor_inmate_links ml ON i.idinmates = ml.inmate_id
        WHERE ml.monitor_id = :monitor_id
        ORDER BY i.name, i.in_custody_date DESC
    """)
    
    result = db.execute(query, {"monitor_id": monitor_id})
    
    history_records = []
    for row in result:
        record = {
            'id': row.idinmates,
            'name': row.name,
            'race': row.race,
            'sex': row.sex,
            'cell_block': row.cell_block,
            'arrest_date': format_date_only(row.arrest_date),
            'held_for_agency': row.held_for_agency,
            'mugshot': row.mugshot,
            'dob': row.dob,
            'hold_reasons': row.hold_reasons,
            'is_juvenile': row.is_juvenile,
            'release_date': row.release_date,
            'in_custody_date': format_date_only(row.in_custody_date),
            'jail_id': row.jail_id,
            'hide_record': row.hide_record,
            'actual_status': row.actual_status,
            'is_excluded_link': row.is_excluded,
            'link_reason': row.link_reason
        }
        history_records.append(record)
    
    return history_records

@app.post("/monitors/{monitor_id}/inmate-links")
async def create_monitor_inmate_link(
    monitor_id: int,
    link_data: MonitorInmateLinkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a manual link between monitor and inmate record"""
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    if current_user.role != "admin" and monitor.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this monitor")
    
    # Check if inmate exists
    inmate = db.query(Inmate).filter(Inmate.id == link_data.inmate_id).first()
    if not inmate:
        raise HTTPException(status_code=404, detail="Inmate record not found")
    
    # Check if link already exists
    existing_link = db.query(MonitorInmateLink).filter(
        MonitorInmateLink.monitor_id == monitor_id,
        MonitorInmateLink.inmate_id == link_data.inmate_id
    ).first()
    
    if existing_link:
        raise HTTPException(status_code=400, detail="Link already exists")
    
    # Create new link
    new_link = MonitorInmateLink(
        monitor_id=monitor_id,
        inmate_id=link_data.inmate_id,
        linked_by_user_id=current_user.id,
        is_excluded=link_data.is_excluded,
        link_reason=link_data.link_reason
    )
    
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    
    return new_link.to_dict()

@app.put("/monitors/{monitor_id}/inmate-links/{link_id}")
async def update_monitor_inmate_link(
    monitor_id: int,
    link_id: int,
    link_data: MonitorInmateLinkUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a monitor-inmate link"""
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    if current_user.role != "admin" and monitor.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this monitor")
    
    link = db.query(MonitorInmateLink).filter(
        MonitorInmateLink.id == link_id,
        MonitorInmateLink.monitor_id == monitor_id
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    # Update link
    link.is_excluded = link_data.is_excluded
    link.link_reason = link_data.link_reason
    link.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(link)
    
    return link.to_dict()

@app.delete("/monitors/{monitor_id}/inmate-links/{link_id}")
async def delete_monitor_inmate_link(
    monitor_id: int,
    link_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a monitor-inmate link"""
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    if current_user.role != "admin" and monitor.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this monitor")
    
    link = db.query(MonitorInmateLink).filter(
        MonitorInmateLink.id == link_id,
        MonitorInmateLink.monitor_id == monitor_id
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    db.delete(link)
    db.commit()
    
    return {"message": "Link deleted successfully"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
