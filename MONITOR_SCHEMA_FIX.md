# Monitor Table Schema Fix

## Issue Resolved
**Error**: `pymysql.err.OperationalError: (1054, "Unknown column 'monitors.arrest_date' in 'SELECT'")`

**Root Cause**: The `monitors` table schema in `create_clean_schema.py` was missing several critical fields that exist in the SQLAlchemy `Monitor` model, causing SQL queries to fail when trying to access these fields.

## Schema Mismatch Analysis

### Fields Missing from Database Schema
- ❌ `arrest_date` (DATE) - **Critical field causing the error**
- ❌ `arrest_reason` (VARCHAR(255))
- ❌ `arresting_agency` (VARCHAR(255)) 
- ❌ `mugshot` (TEXT)
- ❌ `enable_notifications` (INTEGER)
- ❌ `notify_method` (VARCHAR(255))
- ❌ `notify_address` (VARCHAR(255))

### Obsolete Fields in Schema (Not in Model)
- ⚠️ `race` (VARCHAR(255)) - Removed
- ⚠️ `sex` (VARCHAR(255)) - Removed  
- ⚠️ `dob` (VARCHAR(255)) - Removed
- ⚠️ `last_check` (DATETIME) - Removed

## Fix Applied

### Updated Monitor Table Schema
```sql
CREATE TABLE IF NOT EXISTS monitors (
    idmonitors INTEGER PRIMARY KEY AUTO_INCREMENT NOT NULL,
    name VARCHAR(255) NOT NULL,
    user_id INTEGER NULL,
    arrest_date DATE NULL,                    -- ✅ ADDED
    release_date VARCHAR(255) NULL,
    arrest_reason VARCHAR(255) NULL,          -- ✅ ADDED
    arresting_agency VARCHAR(255) NULL,       -- ✅ ADDED
    jail VARCHAR(255) NULL,
    mugshot TEXT NULL,                        -- ✅ ADDED
    enable_notifications INTEGER NOT NULL DEFAULT 1,  -- ✅ ADDED
    notify_method VARCHAR(255) NULL DEFAULT 'pushover',  -- ✅ ADDED
    notify_address VARCHAR(255) NOT NULL DEFAULT '',     -- ✅ ADDED
    last_seen_incarcerated DATETIME NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE KEY unique_monitor (name, notify_address)
)
```

### Key Changes
1. **Added missing fields**: All fields from SQLAlchemy model now present
2. **Removed obsolete fields**: Cleaned up unused columns
3. **Proper constraints**: Added unique constraint matching the model
4. **Default values**: Set appropriate defaults for notification fields

## Impact Areas

### Code That Was Failing
- **Monitor processing scripts**: `scrapes/process_optimized.py`, `scrapes/process.py`
- **Helper functions**: `helpers/process_optimized.py`
- **Frontend display**: `frontend/src/pages/MonitorsPage.tsx`

### Queries Now Working
```python
# These queries will now work correctly:
monitor.arrest_date = inmate.arrest_date
monitor.arrest_reason = "Felony warrant"
monitor.enable_notifications = 1
monitor.notify_method = "pushover"
monitor.notify_address = "user_token"
```

## Database Migration

### Automatic Updates
- ✅ **New installations**: Use complete schema automatically
- ✅ **Existing databases**: Missing columns added via `init_db.py`
- ✅ **Data preservation**: Existing monitor data retained
- ✅ **Obsolete columns**: Will be ignored (can be manually dropped later)

### Verification After Restart
```sql
-- Check monitor table structure
DESCRIBE monitors;

-- Verify arrest_date column exists
SHOW COLUMNS FROM monitors LIKE 'arrest_date';

-- Check all monitor fields
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT 
FROM information_schema.COLUMNS 
WHERE TABLE_NAME = 'monitors' 
ORDER BY ORDINAL_POSITION;
```

## Expected Results After Container Restart
- ✅ No more "Unknown column 'monitors.arrest_date'" errors
- ✅ Monitor processing scripts work correctly
- ✅ Frontend monitor display shows arrest dates
- ✅ Notification system functions properly
- ✅ All monitor CRUD operations successful

This fix ensures the database schema matches the application code expectations, resolving the SQL column reference errors.
