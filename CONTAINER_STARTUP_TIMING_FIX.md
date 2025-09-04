# Complete Container Startup Timing Fix

## Issue Summary
The `incarceration_bot-1` container was starting before the `backend_api-1` container finished initializing the database, causing:
- ❌ `Table 'Bot_incarceration.jails' doesn't exist` errors
- ❌ `update_jails_db()` failing immediately on startup
- ❌ Container startup race condition

## Root Cause
1. **No startup dependency**: `incarceration_bot` started in parallel with `backend_api`
2. **No database readiness check**: `main.py` immediately tried to access database tables
3. **Timing conflict**: Database initialization takes time, but bot expected immediate access

## Complete Solution Applied

### 1. Docker Compose Dependency Fix
**File**: `docker-compose.yml`
```yaml
services:
  incarceration_bot:
    # ... existing config ...
    depends_on:
      - backend_api  # ✅ ADDED: Wait for backend_api to start
    networks:
      - incarceration_network
```

### 2. Database Readiness Check Function
**File**: `main.py`
```python
def wait_for_database_ready(max_retries: int = 30, retry_delay: int = 5) -> bool:
    """Wait for database to be ready with all required tables."""
    required_tables = ['jails', 'inmates', 'users', 'groups', 'monitors']
    
    for attempt in range(max_retries):
        try:
            session = db.new_session()
            missing_tables = []
            
            # Check each required table
            for table in required_tables:
                try:
                    session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                except (OperationalError, ProgrammingError) as e:
                    if 'doesn\'t exist' in str(e):
                        missing_tables.append(table)
                        
            if not missing_tables:
                return True  # ✅ All tables ready
                
            time.sleep(retry_delay)  # ⏳ Wait and retry
            
        except Exception as e:
            logger.warning(f"Database attempt {attempt + 1} failed: {e}")
            
    return False  # ❌ Timeout
```

### 3. Main Execution Flow Updated
**File**: `main.py`
```python
if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stdout, level=LOG_LEVEL)
    
    # ✅ ADDED: Wait for database readiness
    logger.info("🚀 Starting Incarceration Bot - waiting for database...")
    if not wait_for_database_ready():
        logger.error("❌ Failed to connect to database - exiting")
        sys.exit(1)
    
    # ✅ NOW SAFE: Database is guaranteed to be ready
    session = db.new_session()
    update_jails_db(session)
    session.close()
```

### 4. Required Imports Added
**File**: `main.py`
```python
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError
```

## Fixed Container Startup Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Container Startup Flow                   │
├─────────────────────────────────────────────────────────────┤
│ 1️⃣  backend_api starts                                      │
│    ├── Database connection                                  │
│    ├── Schema creation (Phase 1: Independent tables)       │
│    ├── Partitioned inmates table (Phase 2)                 │
│    └── Dependent tables (Phase 3)                          │
│                                                             │
│ 2️⃣  incarceration_bot waits (depends_on: backend_api)       │
│                                                             │
│ 3️⃣  incarceration_bot starts                               │
│    ├── wait_for_database_ready() checks tables             │
│    ├── Retries every 5 seconds for up to 150 seconds       │
│    └── Proceeds only when all tables exist                 │
│                                                             │
│ 4️⃣  update_jails_db() runs safely                          │
│    └── No more "Table doesn't exist" errors! ✅            │
└─────────────────────────────────────────────────────────────┘
```

## Expected Results After Container Restart

### backend_api-1 Logs:
```
✅ Database connection successful
✅ All tables created successfully  
✅ Partitioned inmates table with 16 partitions
✅ Complete schema creation finished!
```

### incarceration_bot-1 Logs:
```
🚀 Starting Incarceration Bot - waiting for database...
⏳ Database not ready yet - missing tables: [jails, inmates]
🔄 Waiting 5 seconds before retry 1/30...
⏳ Database not ready yet - missing tables: [jails]  
🔄 Waiting 5 seconds before retry 2/30...
✅ Database is ready - all required tables exist!
✅ Updating Jail Database
✅ Adding Benton County AR Jail
✅ Adding Pulaski County AR Jail
...
```

## Verification Commands

```bash
# Restart containers and monitor logs
docker-compose down && docker-compose up

# Check container startup order
docker-compose logs --timestamps

# Verify no table existence errors
docker-compose logs incarceration_bot | grep -E "(doesn't exist|ProgrammingError)"
```

This solution eliminates the race condition and ensures the incarceration bot waits for complete database initialization before attempting any database operations.
