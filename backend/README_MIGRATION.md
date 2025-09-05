# Database Migration System

## Overview

The Incarceration Bot now includes a comprehensive database migration system that automatically ensures all SQLAlchemy models match the database schema. This system runs automatically on container startup and can also be executed manually.

## Architecture

### Core Components

1. **`schema_migrator.py`** - Modern comprehensive schema validator and migrator
2. **`database_migration_complete.py`** - Complete migration system with legacy support
3. **`legacy_monitor_migration.py`** - Legacy monitor table migration (deprecated)
4. **`test_migration_system.py`** - Test suite for migration system
5. **`init_db.py`** - Integration with container startup

### Integration Points

- **Container Startup**: Automatic migration via `init_db.py`
- **Manual Execution**: Direct script execution for maintenance
- **Legacy Support**: Backwards compatibility with old migration scripts

## Usage

### Automatic (Recommended)

The migration system runs automatically when containers start:

```bash
# Migrations run automatically during container startup
docker-compose up
```

### Manual Execution

#### Complete Migration
```bash
# Run comprehensive migration (recommended)
python backend/database_migration_complete.py

# With verbose logging
python backend/database_migration_complete.py --verbose

# Force legacy sync + comprehensive migration
python backend/database_migration_complete.py --force-sync
```

#### Verification Only
```bash
# Only run verification queries (no changes)
python backend/database_migration_complete.py --verify-only
```

#### Individual Components
```bash
# Modern schema migrator only
python backend/schema_migrator.py

# Legacy monitor migration only (deprecated)
python backend/legacy_monitor_migration.py
```

#### Testing
```bash
# Test migration system without making changes
python backend/test_migration_system.py
```

## Features

### Comprehensive Model Support

The system automatically validates and migrates all SQLAlchemy models:

- ✅ **User** - User accounts with authentication
- ✅ **Group** - User groups and permissions  
- ✅ **UserGroup** - User-group relationships
- ✅ **Jail** - Jail/facility information
- ✅ **Inmate** - Inmate records with partitioning support
- ✅ **Monitor** - Monitoring configurations
- ✅ **MonitorLink** - Monitor relationships
- ✅ **MonitorInmateLink** - Monitor-inmate relationships
- ✅ **Session** - User sessions

### Database Compatibility

- ✅ **MySQL/MariaDB** - Primary production database
- ✅ **PostgreSQL** - Alternative production database
- ✅ **SQLite** - Development and testing database

### Migration Features

- **Automatic Column Addition** - Adds missing columns from models
- **Type Compatibility** - Handles database-specific type mappings
- **Default Value Support** - Applies appropriate defaults for new columns
- **Primary Key Handling** - Respects existing primary key structures
- **Foreign Key Awareness** - Handles foreign key constraints appropriately
- **Idempotent Operations** - Safe to run multiple times

### Verification System

- **Critical Query Testing** - Tests common queries that fail due to schema mismatches
- **Comprehensive Coverage** - Tests all major tables and relationships
- **Detailed Reporting** - Clear success/failure reporting with error details
- **Non-Blocking Verification** - Migration continues even if some verifications fail

## Error Handling

### Common Issues

1. **"Unknown column 'monitors.arrest_date'"**
   - **Cause**: Monitor table missing columns from model
   - **Solution**: Automatic migration adds missing columns
   - **Prevention**: Migration system prevents this in future

2. **"Table 'inmates' doesn't exist"**
   - **Cause**: Missing table creation
   - **Solution**: Clean schema initialization creates tables
   - **Prevention**: Schema validation before operations

3. **"Duplicate column name"**
   - **Cause**: Column already exists
   - **Solution**: Migration system detects and skips existing columns
   - **Prevention**: Column existence checks before addition

### Migration Failures

If migration fails:

1. **Check Logs**: Review detailed error messages
2. **Database Permissions**: Ensure ALTER TABLE permissions
3. **Connectivity**: Verify database connection
4. **Manual Recovery**: Use verification mode to assess damage

```bash
# Check current state without making changes
python backend/database_migration_complete.py --verify-only

# Try force sync if needed
python backend/database_migration_complete.py --force-sync
```

## Technical Details

### Schema Detection

The system uses SQLAlchemy reflection to:
- Detect existing database schema
- Compare with model definitions
- Identify missing columns and constraints
- Generate appropriate DDL for additions

### Type Mapping

Automatic type conversion between SQLAlchemy and database types:

| SQLAlchemy Type | MySQL | PostgreSQL | SQLite |
|----------------|-------|------------|--------|
| String(255) | VARCHAR(255) | VARCHAR(255) | VARCHAR(255) |
| Text | TEXT | TEXT | TEXT |
| Integer | INTEGER | INTEGER | INTEGER |
| Boolean | BOOLEAN | BOOLEAN | INTEGER |
| Date | DATE | DATE | DATE |
| DateTime | DATETIME | TIMESTAMP | DATETIME |

### Legacy Support

The system maintains compatibility with:
- Old monitor table migration scripts
- Force schema sync operations
- Manual column addition procedures

## Development

### Adding New Models

1. Create SQLAlchemy model in `models/`
2. Import model in migration system
3. Test with verification system
4. Migration runs automatically

### Testing Changes

```bash
# Test import and basic functionality
python backend/test_migration_system.py

# Test migration without changes
python backend/database_migration_complete.py --verify-only

# Run full migration in development
python backend/database_migration_complete.py --verbose
```

### Debugging

Enable verbose logging:
```bash
export LOG_LEVEL=DEBUG
python backend/database_migration_complete.py --verbose
```

## Files Moved to Backend

The following migration files have been moved from project root to `backend/`:

- `migrate_monitors_table.py` → `backend/legacy_monitor_migration.py`
- New comprehensive system in `backend/database_migration_complete.py`
- Modern validator in `backend/schema_migrator.py`

## Container Integration

The migration system is fully integrated with container startup:

1. **Database Wait**: Waits for database availability
2. **Schema Creation**: Creates missing tables via clean schema
3. **Migration**: Runs comprehensive migration for all models
4. **Verification**: Tests critical queries
5. **Application Start**: Proceeds with application startup

## Monitoring

Migration results are logged with structured information:

```
🚀 Starting comprehensive database migration system...
🔍 Checking table: monitors
  ❌ Missing column: arrest_date
  📝 Adding missing column: arrest_date
  ✅ Added arrest_date successfully
📊 Total changes applied: 7
🎉 Complete migration SUCCEEDED!
```

## Future Enhancements

- **Schema Versioning**: Track schema versions for rollback support
- **Performance Optimization**: Batch operations for large migrations
- **Backup Integration**: Automatic backups before major migrations
- **Monitoring Dashboard**: Web interface for migration status

## Support

For migration issues:

1. Check container logs for detailed error messages
2. Run verification to assess current state
3. Use force-sync for legacy compatibility
4. Review model definitions for accuracy

The migration system is designed to be robust and self-healing, automatically resolving most common schema mismatches without manual intervention.
