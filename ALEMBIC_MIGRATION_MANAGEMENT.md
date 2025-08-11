# Alembic Migration Management

This document describes the improved Alembic migration management system implemented to address code review feedback.

## Overview

The migration system has been refactored to:
- Use a proper package structure for utilities
- Implement shared helpers to reduce code duplication  
- Add configurable auto-merge behavior for safety
- Use Alembic's Python API instead of subprocess calls where possible
- Ensure data consistency across different database types

## Package Structure

```
backend/alembic/utils/
├── __init__.py                 # Package exports
├── migration_helpers.py        # Database schema utilities
└── alembic_helpers.py         # Alembic command utilities
```

### Migration Helpers (`migration_helpers.py`)
Contains idempotent database operations:
- `column_exists()`, `table_exists()`, `index_exists()`
- `safe_add_column()`, `safe_drop_column()`, `safe_rename_column()`
- `safe_create_index()`, `safe_drop_index()`
- `execute_sql_if_condition()`

### Alembic Helpers (`alembic_helpers.py`)
Contains shared Alembic operations:
- `check_multiple_heads()` - Check for conflicting migration heads
- `merge_heads_safely()` - Safely merge multiple heads with configuration
- `get_current_revision()` - Get current database revision
- `show_migration_history()` - Display migration history

## Auto-Merge Configuration

The system now includes configurable auto-merge behavior to address safety concerns:

### Environment Variable
```bash
ALEMBIC_ALLOW_AUTO_MERGE=true   # Enable automatic head merging
ALEMBIC_ALLOW_AUTO_MERGE=false  # Require manual resolution (default)
```

### Behavior

**When `ALEMBIC_ALLOW_AUTO_MERGE=false` (default):**
- Multiple heads cause startup to halt
- Clear error messages with resolution instructions
- Prevents database inconsistencies from unresolved conflicts

**When `ALEMBIC_ALLOW_AUTO_MERGE=true`:**
- Automatically merges multiple heads during startup
- Creates merge migration with descriptive commit message
- Upgrades to merged head automatically

### Safety Features
1. **Default to Safe**: Auto-merge is disabled by default
2. **Explicit Configuration**: Must be explicitly enabled via environment variable
3. **Graceful Degradation**: Falls back to subprocess calls if Python API unavailable
4. **Clear Logging**: Detailed logs for all operations and failures

## Usage Examples

### Manual Migration Operations
```bash
# Check for multiple heads
docker-compose exec backend_api python maintenance.py check-heads

# Merge heads manually
docker-compose exec backend_api python maintenance.py merge-heads

# View migration history
docker-compose exec backend_api python maintenance.py migration-history
```

### Production Deployment with Auto-Merge
```bash
# Enable auto-merge for automated deployments
export ALEMBIC_ALLOW_AUTO_MERGE=true
docker-compose up -d backend_api
```

### Development with Manual Control
```bash
# Default behavior - require manual resolution
docker-compose up -d backend_api
# If multiple heads detected, container startup will halt with instructions
```

## Data Consistency Improvements

### Users Table Migration Fix
The `006_fix_users_table_columns.py` migration now includes explicit steps to ensure data consistency across database types:

1. **Column Addition**: Add role column with server default
2. **Explicit Backfill**: Update existing rows to ensure consistent values
3. **Conditional Updates**: Only update rows that need changes

```python
# Step 2.1: Explicitly update existing rows to ensure consistency across databases
execute_sql_if_condition(
    sql="UPDATE users SET role = 'user' WHERE role IS NULL",
    condition_sql="SELECT COUNT(*) FROM users WHERE role IS NULL",
    description="ensuring all existing rows have the default role value"
)
```

This addresses MySQL's behavior where server defaults may not backfill existing rows.

## Error Handling

### Multiple Heads Detection
1. **Early Detection**: Check for multiple heads before attempting migrations
2. **Clear Messages**: Provide specific instructions for resolution
3. **Safe Defaults**: Halt startup rather than risk inconsistency

### Graceful Fallbacks
1. **Utils Unavailable**: Fall back to subprocess calls with proper error handling
2. **Python API Failure**: Attempt alternative approaches
3. **Complete Failure**: Clear error messages with manual resolution steps

## Maintenance Commands

The maintenance system has been updated to use the shared utilities:

```bash
# Check migration status
python maintenance.py check-heads

# Merge conflicting heads  
python maintenance.py merge-heads

# Show migration history
python maintenance.py migration-history
```

## Migration Best Practices

1. **Test Migrations**: Always test migrations in development first
2. **Backup Data**: Backup production database before running migrations
3. **Monitor Logs**: Check container logs for migration status
4. **Manual Review**: Review auto-generated merge migrations before deployment
5. **Rollback Plan**: Have a rollback strategy for failed migrations

## Troubleshooting

### Multiple Heads Error
```bash
# Check current heads
docker-compose exec backend_api alembic heads

# Manual merge
docker-compose exec backend_api alembic merge -m 'merge heads' heads
docker-compose exec backend_api alembic upgrade head
```

### Container Startup Failure
1. Check logs: `docker-compose logs backend_api`
2. Look for migration errors
3. Resolve multiple heads if present
4. Restart container

### Data Inconsistency
1. Check migration history: `python maintenance.py migration-history`
2. Verify current revision: `alembic current`
3. Run maintenance commands to check database state
4. Contact administrator if issues persist
