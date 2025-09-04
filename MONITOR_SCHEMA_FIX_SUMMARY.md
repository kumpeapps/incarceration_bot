# Monitor Table Schema Fix - Implementation Options

## The Issue
Your existing `monitors` table is missing several columns that the SQLAlchemy model expects:
- `arrest_date` (causing the "Unknown column" error)
- `arrest_reason`, `arresting_agency`, `mugshot`
- `enable_notifications`, `notify_method`, `notify_address`

## Solution 1: Automatic Fix (Recommended)
✅ **Container restart will handle this automatically**

I've updated `backend/init_db.py` to automatically add missing columns to the `monitors` table during container startup. This means:

- **No manual script needed**
- **Automatic on next restart**
- **Safe and idempotent** (won't break if columns already exist)

### What happens on container restart:
1. Container starts up
2. `init_db.py` runs automatically
3. `ensure_monitors_schema()` checks for missing columns
4. Missing columns are added automatically
5. Your application works without errors

## Solution 2: Manual Migration Script (Backup option)
If for some reason the automatic fix doesn't work, I've created `migrate_monitors_table.py`:

```bash
# Run inside your container or with database access
python migrate_monitors_table.py
```

## What Gets Added to Your Database

### New Columns in `monitors` table:
```sql
ALTER TABLE monitors ADD COLUMN arrest_date DATE NULL;
ALTER TABLE monitors ADD COLUMN arrest_reason VARCHAR(255) NULL;
ALTER TABLE monitors ADD COLUMN arresting_agency VARCHAR(255) NULL;
ALTER TABLE monitors ADD COLUMN mugshot TEXT NULL;
ALTER TABLE monitors ADD COLUMN enable_notifications INTEGER NOT NULL DEFAULT 1;
ALTER TABLE monitors ADD COLUMN notify_method VARCHAR(255) NULL DEFAULT 'pushover';
ALTER TABLE monitors ADD COLUMN notify_address VARCHAR(255) NOT NULL DEFAULT '';
```

### Unique Constraint:
```sql
ALTER TABLE monitors ADD CONSTRAINT unique_monitor UNIQUE (name, notify_address);
```

## Database Schema Before vs After

### Before (Missing columns):
```
monitors table:
- idmonitors (PRIMARY KEY)
- name
- race          ← Will be ignored (not in model)
- sex           ← Will be ignored (not in model)  
- dob           ← Will be ignored (not in model)
- last_seen_incarcerated
- last_check    ← Will be ignored (not in model)
- release_date
- jail
- user_id
```

### After (Complete schema):
```
monitors table:
- idmonitors (PRIMARY KEY)
- name
- user_id
- arrest_date         ← NEW
- release_date
- arrest_reason       ← NEW
- arresting_agency    ← NEW
- jail
- mugshot             ← NEW
- enable_notifications ← NEW
- notify_method       ← NEW
- notify_address      ← NEW
- last_seen_incarcerated
```

## Expected Results After Restart

### ✅ Fixed Errors:
- No more `"Unknown column 'monitors.arrest_date'"` errors
- Monitor processing scripts work correctly
- Frontend monitor pages display properly
- Notification system functions

### ✅ Preserved Data:
- All existing monitor records remain intact
- No data loss during schema update
- Old unused columns remain (but ignored by application)

## Verification Commands

After container restart, verify the fix worked:

```sql
-- Check if arrest_date column exists
SHOW COLUMNS FROM monitors LIKE 'arrest_date';

-- See all monitor table columns
DESCRIBE monitors;

-- Test a query that was failing before
SELECT name, arrest_date, notify_address FROM monitors LIMIT 5;
```

## Recommendation

**Simply restart your containers** - the automatic fix in `init_db.py` will handle everything:

```bash
docker-compose down
docker-compose up
```

The logs will show:
```
✅ Ensuring monitors table schema is up to date...
✅ Adding 7 missing columns to monitors table...
✅ Monitors table schema update completed
```

This is the safest approach as it's been integrated into the existing database initialization system.
