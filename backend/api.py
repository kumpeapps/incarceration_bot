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
from models.Jail import Jail
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
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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

# Mock user store (in production, use a proper database)
fake_users_db = {
    "admin": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": pwd_context.hash("admin123"),
        "role": "admin"
    },
    "user": {
        "id": 2,
        "username": "user",
        "email": "user@example.com", 
        "hashed_password": pwd_context.hash("user123"),
        "role": "user"
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user = fake_users_db.get(username)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

# Database dependency
def get_db():
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()

# Authentication endpoints
@app.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    user = fake_users_db.get(login_data.username)
    if not user or not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }

@app.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Successfully logged out"}

@app.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "role": current_user["role"]
    }

# Dashboard endpoints
@app.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user),
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Inmate)
    
    if name:
        query = query.filter(Inmate.name.ilike(f"%{name}%"))
    if jail_id:
        query = query.filter(Inmate.jail_id == jail_id)
    
    total = query.count()
    inmates = query.offset((page - 1) * limit).limit(limit).all()
    
    return PaginatedResponse(
        items=[inmate.to_dict() for inmate in inmates],
        total=total,
        page=page,
        limit=limit,
        pages=(total + limit - 1) // limit
    )

@app.get("/inmates/{inmate_id}")
async def get_inmate(
    inmate_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    inmate = db.query(Inmate).filter(Inmate.id == inmate_id).first()
    if not inmate:
        raise HTTPException(status_code=404, detail="Inmate not found")
    return inmate.to_dict()

# Monitors endpoints
@app.get("/monitors")
async def get_monitors(
    page: int = 1,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Monitor)
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    monitor = Monitor(
        name=monitor_data.name,
        notify_address=monitor_data.notify_address,
        notify_method=monitor_data.notify_method,
        enable_notifications=monitor_data.enable_notifications
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return monitor.to_dict()

@app.put("/monitors/{monitor_id}")
async def update_monitor(
    monitor_id: int,
    monitor_data: MonitorCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
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
async def get_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return [
        {
            "id": user["id"],
            "username": user["username"], 
            "email": user["email"],
            "role": user["role"]
        }
        for user in fake_users_db.values()
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
