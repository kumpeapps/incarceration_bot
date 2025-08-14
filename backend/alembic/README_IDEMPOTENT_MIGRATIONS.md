# Idempotent Migrations Guide - Enhanced Version

This document describes how to create and maintain idempotent database migrations in this project.

## What are Idempotent Migrations?

Idempotent migrations can be run multiple times safely without causing errors or duplicating data. This provides several benefits:

1. **Better Developer Experience**: Migrations don't fail if tables/columns already exist
2. **Safer Deployments**: Migrations can be re-run if they fail partway through
3. **Docker Compatibility**: Containers can safely re-initialize the database
4. **Rollback Safety**: Downgrade operations won't fail if structures are already removed

## Migration Utilities

The `migration_utils.py` file provides helper functions for creating idempotent migrations:

### Table Operations
- `table_exists(table_name)` - Check if a table exists
- `safe_create_table(table_name, *columns, **kwargs)` - Create table only if it doesn't exist
- `safe_drop_table(table_name)` - Drop table only if it exists

### Column Operations
- `column_exists(table_name, column_name)` - Check if a column exists
- `safe_add_column(table_name, column_name, column_type, **kwargs)` - Add column only if it doesn't exist
- `safe_drop_column(table_name, column_name)` - Drop column only if it exists

### Data Operations
- `execute_sql_if_condition(sql, condition_sql, description)` - Execute SQL only if condition is met

### Other Utilities
- `migration_summary(table_name)` - Print table structure after migration
- `index_exists(table_name, index_name)` - Check if an index exists
- `safe_create_index()` / `safe_drop_index()` - Safe index operations

## Example Usage

```python
def upgrade():
    """Apply the migration changes"""
    print("Starting migration: Add user preferences")
    
    # Add columns only if they don't exist
    safe_add_column('users', 'preferences', sa.JSON(), nullable=True)
    safe_add_column('users', 'last_login', sa.DateTime(), nullable=True)
    
    # Rename columns only if source exists and target doesn't
    safe_rename_column('users', 'password_hash', 'hashed_password', sa.String(length=255))
    
    # Execute SQL only when conditions are met
    execute_sql_if_condition(
        sql="UPDATE users SET role = 'admin' WHERE is_admin = 1",
        condition_sql="SELECT COUNT(*) FROM users WHERE is_admin = 1 AND role != 'admin'",
        description="updating admin user roles"
    )
    
    # Create indexes only if they don't exist
    safe_create_index('users', ['email'], 'ix_users_email', unique=True)
    
    print("Migration completed successfully")
    migration_summary('users')
```

## Best Practices

1. **Always Check Before Changing**: Use the utility functions to check if changes are needed
2. **Handle Exceptions Gracefully**: Wrap operations in try-catch blocks with informative warnings
3. **Use Descriptive Messages**: Print what the migration is doing and why
4. **Test Both Directions**: Ensure both upgrade and downgrade are idempotent
5. **Document Complex Logic**: Add comments explaining the business logic behind changes

## Common Patterns

### Column Rename Pattern
```python
# Safe column rename that works even if already renamed
safe_rename_column('users', 'old_name', 'new_name', sa.String(length=255))
```

### Conditional Data Update Pattern
```python
# Only update data that actually needs updating
execute_sql_if_condition(
    sql="UPDATE table SET column = 'new_value' WHERE condition",
    condition_sql="SELECT COUNT(*) FROM table WHERE condition AND column != 'new_value'",
    description="updating records that need the new value"
)
```

### New Column with Data Population Pattern
```python
# Add column and populate it
if safe_add_column('users', 'full_name', sa.String(length=255), nullable=True):
    # Only populate if we just added the column
    execute_sql_if_condition(
        sql="UPDATE users SET full_name = CONCAT(first_name, ' ', last_name) WHERE full_name IS NULL",
        condition_sql="SELECT COUNT(*) FROM users WHERE full_name IS NULL",
        description="populating full_name from first_name and last_name"
    )
```

## Troubleshooting

### Migration Stuck on Failed State
If a migration is marked as failed but the database state is actually correct:

```bash
# Mark the migration as complete manually
docker-compose exec backend_api alembic stamp <revision_id>
```

### Check Current Database State
```bash
# Connect to database and inspect
docker-compose exec backend_api python -c "
from database_connect import new_session
from sqlalchemy import inspect
session = new_session()
inspector = inspect(session.bind)
print('Tables:', inspector.get_table_names())
for table in ['users', 'inmates', 'monitors']:
    if table in inspector.get_table_names():
        print(f'{table} columns:')
        for col in inspector.get_columns(table):
            print(f'  {col[\"name\"]} - {col[\"type\"]}')
session.close()
"
```

### Manual Migration Testing
```bash
# Test the migration without committing
docker-compose exec backend_api alembic upgrade <revision_id> --sql
```

This approach ensures your migrations are robust and can handle various deployment scenarios safely.
