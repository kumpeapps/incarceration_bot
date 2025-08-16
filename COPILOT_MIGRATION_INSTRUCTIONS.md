# Copilot Instructions: Idempotent Migration System

## Overview
This project now uses an idempotent migration system that makes database migrations safe to run multiple times without causing errors. This provides a much better user experience for developers and deployments.

## Key Principles

### 1. Always Use Safe Functions
- Use `safe_create_table()` instead of `op.create_table()`
- Use `safe_add_column()` instead of `op.add_column()`
- Use `safe_drop_table()` and `safe_drop_column()` for removals
- Use `execute_sql_if_condition()` for data migrations

### 2. Include Fallback Functions
Every migration must include comprehensive fallback functions in case `migration_utils.py` can't be imported:

```python
try:
    from migration_utils import safe_create_table, safe_add_column, execute_sql_if_condition
except ImportError as e:
    print(f"Warning: Could not import migration utilities: {e}")
    
    def safe_create_table(table_name, *columns, **kwargs):
        from sqlalchemy import inspect
        try:
            connection = op.get_bind()
            inspector = inspect(connection)
            if table_name not in inspector.get_table_names():
                op.create_table(table_name, *columns, **kwargs)
            else:
                print(f"Table {table_name} already exists, skipping")
        except Exception as ex:
            # Handle "already exists" errors gracefully
    
    # ... other fallback functions
```

### 3. Check Before Acting
- Always check if tables/columns exist before creating them
- Always check conditions before migrating data
- Use NOT EXISTS clauses in data migration queries to prevent duplicates

### 4. Provide Informative Logging
- Print what operations are being performed
- Print when operations are skipped due to existing structures
- Use descriptive messages in `execute_sql_if_condition()`

## Migration Template

Here's the standard template for new migrations:

```python
"""Migration description

Revision ID: xxx
Revises: xxx
Create Date: xxx
"""
from typing import Sequence, Union
import os
import sys
from alembic import op
import sqlalchemy as sa

# Import path setup
alembic_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(alembic_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

try:
    from migration_utils import (
        safe_create_table, safe_add_column, safe_drop_table, safe_drop_column,
        execute_sql_if_condition, column_exists, table_exists, migration_summary
    )
except ImportError as e:
    print(f"Warning: Could not import migration utilities: {e}")
    
    # Include comprehensive fallback functions here
    def safe_create_table(table_name, *columns, **kwargs):
        # Implementation with existence checking
    
    def safe_add_column(table_name, column_name, column_type, **kwargs):
        # Implementation with existence checking
    
    # ... other fallbacks

def upgrade() -> None:
    """Upgrade operations"""
    print("Starting migration: [description]")
    
    # Use safe functions
    safe_create_table('my_table', ...)
    safe_add_column('existing_table', 'new_column', sa.String(50))
    
    # Conditional data migration
    execute_sql_if_condition(
        sql="INSERT INTO ...",
        condition_sql="SELECT COUNT(*) > 0 FROM ... WHERE ...",
        description="migrating existing data"
    )
    
    migration_summary('my_table')

def downgrade() -> None:
    """Downgrade operations"""
    safe_drop_column('existing_table', 'new_column')
    safe_drop_table('my_table')
```

## Testing Migrations

When creating or modifying migrations, always test idempotency:

1. `docker-compose exec backend_api alembic upgrade head`
2. `docker-compose exec backend_api alembic upgrade head` (should succeed again)
3. `docker-compose restart backend_api`
4. `docker-compose exec backend_api alembic upgrade head` (should still work)

## Common Patterns

### Safe Table Creation
```python
safe_create_table('groups',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(50), nullable=False),
    sa.PrimaryKeyConstraint('id')
)
```

### Safe Column Addition
```python
safe_add_column('users', 'api_key', sa.String(255), nullable=True, unique=True)
```

### Conditional Data Migration
```python
execute_sql_if_condition(
    sql="""
        INSERT INTO user_groups (user_id, group_id)
        SELECT u.id, g.id FROM users u CROSS JOIN groups g 
        WHERE u.role = 'admin' AND g.name = 'admin'
        AND NOT EXISTS (SELECT 1 FROM user_groups ug WHERE ug.user_id = u.id AND ug.group_id = g.id)
    """,
    condition_sql="""
        SELECT COUNT(*) > 0 FROM users u CROSS JOIN groups g 
        WHERE u.role = 'admin' AND g.name = 'admin'
        AND NOT EXISTS (SELECT 1 FROM user_groups ug WHERE ug.user_id = u.id AND ug.group_id = g.id)
    """,
    description="migrating admin users to admin group"
)
```

## Container Considerations

Since this project uses Docker containers, remember:

1. **CRITICAL**: When making code changes that affect the API, always rebuild with no cache: `docker-compose build --no-cache backend_api`
2. Regular builds (`docker-compose build backend_api`) may use cached layers and not include your latest code changes
3. After making ANY code changes to backend files, always use `--no-cache` to ensure changes are applied
4. Migration file changes require rebuilding the container: `docker-compose build --no-cache backend_api`
5. Always test migrations after rebuilding containers
6. The `init_db.py` script may create tables before migrations run - this is expected and handled by the idempotent system

## Troubleshooting Login Issues

If users report "username password incorrect" errors:

1. **First check for syntax errors** in the API code that could cause 500 errors
2. **Rebuild with no cache**: `docker-compose build --no-cache backend_api && docker-compose up -d backend_api`
3. Test login directly: `docker exec -it incarceration_bot-backend_api-1 python -c "import requests; response = requests.post('http://localhost:8000/auth/login', json={'username': 'admin', 'password': 'admin123'}); print(f'Status: {response.status_code}, Response: {response.text}')"`
4. Check container logs: `docker logs incarceration_bot-backend_api-1 --tail=50`
5. Verify user exists in database: `docker exec -it incarceration_bot-backend_api-1 python -c "from models.User import User; import database_connect as db; session = db.new_session(); admin = session.query(User).filter(User.username == 'admin').first(); print(f'Admin exists: {admin is not None}'); session.close()"`

## Error Recovery

If migrations fail:

1. Fix the underlying issue (database connectivity, permissions, etc.)
2. Simply re-run `docker-compose exec backend_api alembic upgrade head`
3. The idempotent design ensures no duplicate structures or data

## Best Practices Summary

1. **Always use safe_* functions** - never use direct Alembic operations
2. **Include comprehensive fallbacks** - migrations must work even if utilities fail to import
3. **Test idempotency** - run migrations multiple times to ensure they work
4. **Check existence before operations** - use table_exists(), column_exists(), etc.
5. **Use conditional data migration** - prevent duplicate data with NOT EXISTS clauses
6. **Provide clear logging** - help users understand what's happening
7. **Test in containers** - rebuild and test after changes
8. **Document complex migrations** - explain the purpose and approach

This idempotent migration system makes database management much more reliable and provides a significantly better user experience for both development and deployment scenarios.
