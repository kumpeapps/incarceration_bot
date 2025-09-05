# Clean Schema Deployment

This directory contains the clean schema deployment system that replaces the problematic Alembic migration chain with a comprehensive, single-file schema deployment.

## Overview

Due to irreconcilable migration conflicts and auto-merge issues in the Alembic migration chain, we've implemented a clean schema approach that:

1. **Archives all existing migrations** to prevent conflicts
2. **Creates the complete database schema** from scratch with all optimizations
3. **Implements table partitioning** for performance (MySQL)
4. **Sets up default user groups** and configurations
5. **Ensures idempotent deployment** that can be safely re-run

## Files

- `create_clean_schema.py` - Main schema creation script with all table definitions
- `deploy_clean_schema.sh` - Safe deployment script with testing and verification
- `test_clean_schema.py` - Test script to verify schema deployment
- `migration_archive_20250903_190203/` - Archived migration files for reference

## Key Features

### Performance Optimizations
- **Partitioned inmates table**: 16 hash partitions based on `jail_id` for large dataset performance
- **Optimized unique constraint**: Reordered to `(jail_id, arrest_date, name, dob, sex, race)` for better performance
- **Strategic indexes**: Added performance indexes for common query patterns
- **Pre-filtering optimization**: Separate INSERT/UPDATE operations for databases >100K records

### Database Compatibility
- **MySQL/MariaDB**: Full partitioning and optimization support
- **PostgreSQL**: Database-agnostic SQL with appropriate adaptations
- **SQLite**: Development environment support

### Migration Resolution
- **Complete migration archive**: All 24 problematic migration files safely preserved
- **Clean slate approach**: No migration conflicts or auto-merge issues
- **Idempotent deployment**: Safe to re-run without data loss

## Deployment

### Production Deployment
```bash
cd /path/to/incarceration_bot/backend
./deploy_clean_schema.sh
```

### Testing Only
```bash
cd /path/to/incarceration_bot/backend
python test_clean_schema.py
```

### Manual Deployment
```python
from create_clean_schema import create_complete_schema, setup_default_groups
from database_connect import get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create session
engine = create_engine(get_database_url())
Session = sessionmaker(bind=engine)
session = Session()

# Deploy schema
create_complete_schema(session)
setup_default_groups(session)
session.commit()
```

## Verification

The deployment script automatically verifies:

1. **Table creation**: All expected tables are created
2. **Partitioning**: Inmates table has correct partitions (MySQL)
3. **Default groups**: User management groups are configured
4. **Foreign keys**: All relationships are properly established

### Manual Verification (MySQL)
```sql
-- Check partitioning
SELECT 
    table_name,
    partition_name,
    partition_ordinal_position,
    table_rows
FROM information_schema.partitions 
WHERE table_schema = DATABASE() 
AND table_name = 'inmates' 
AND partition_name IS NOT NULL;

-- Verify unique constraint
SHOW CREATE TABLE inmates;

-- Check default groups
SELECT * FROM groups;
```

## Performance Impact

### Before (Migration Issues)
- ❌ Auto-merge conflicts preventing startup
- ❌ Hanging on bulk upsert operations (1288 inmates)
- ❌ Inefficient unique constraint order
- ❌ No table partitioning for large datasets

### After (Clean Schema)
- ✅ Zero migration conflicts
- ✅ Pre-filtered bulk operations (13 batches instead of 1288)
- ✅ Optimized constraint order for performance
- ✅ Hash partitioning for horizontal scaling

## Rollback Plan

If rollback is needed:

1. **Restore migration files**: Copy from `migration_archive_20250903_190203/` back to `alembic/versions/`
2. **Reset alembic state**: `alembic stamp head`
3. **Rebuild containers**: `docker-compose down && docker-compose up --build`

## Maintenance

### Adding New Tables
Add table definitions to `get_schema_sql()` in `create_clean_schema.py`:

```python
'new_table': f'''
    CREATE TABLE IF NOT EXISTS new_table (
        id INTEGER PRIMARY KEY {auto_increment} NOT NULL,
        name VARCHAR(255) NOT NULL,
        created_at {datetime_type} NOT NULL DEFAULT {timestamp_default}
    )
''',
```

### Schema Updates
For schema changes, update the table definition and re-run deployment. The system handles:
- Missing columns (added automatically)
- New indexes (created if not exists)
- Updated constraints (modified as needed)

## Troubleshooting

### Common Issues

**"Table already exists"**: This is normal and expected. The script handles existing tables gracefully.

**"Partitioning failed"**: Check MySQL version and partition syntax. Partitioning requires MySQL 5.1+.

**"Foreign key constraint fails"**: Ensure all referenced tables exist before creating dependent tables.

### Debug Mode
Set `LOG_LEVEL=DEBUG` environment variable for detailed logging:

```bash
export LOG_LEVEL=DEBUG
./deploy_clean_schema.sh
```

## Summary

This clean schema approach completely resolves the migration conflicts while implementing all performance optimizations. The system is now ready for production deployment with:

- ✅ Partitioned tables for performance
- ✅ Optimized constraints and indexes  
- ✅ Zero migration conflicts
- ✅ Safe, idempotent deployment
- ✅ Full database compatibility
