"""
Utility functions for idempotent Alembic migrations
These functions help make migrations safe to run multiple times
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    try:
        connection = op.get_bind()
        inspector = inspect(connection)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception:
        return False


def table_exists(table_name):
    """Check if a table exists"""
    try:
        connection = op.get_bind()
        inspector = inspect(connection)
        return table_name in inspector.get_table_names()
    except Exception:
        return False


def index_exists(table_name, index_name):
    """Check if an index exists on a table"""
    try:
        connection = op.get_bind()
        inspector = inspect(connection)
        indexes = inspector.get_indexes(table_name)
        return any(idx['name'] == index_name for idx in indexes)
    except Exception:
        return False


def safe_add_column(table_name, column_name, column_type, **kwargs):
    """Safely add a column only if it doesn't exist"""
    if not column_exists(table_name, column_name):
        print(f"Adding column {column_name} to {table_name}")
        op.add_column(table_name, sa.Column(column_name, column_type, **kwargs))
        return True
    else:
        print(f"Column {column_name} already exists in {table_name}, skipping")
        return False


def safe_drop_column(table_name, column_name):
    """Safely drop a column only if it exists"""
    if column_exists(table_name, column_name):
        print(f"Dropping column {column_name} from {table_name}")
        op.drop_column(table_name, column_name)
        return True
    else:
        print(f"Column {column_name} doesn't exist in {table_name}, skipping")
        return False


def safe_rename_column(table_name, old_name, new_name, column_type=None):
    """Safely rename a column only if the old exists and new doesn't"""
    if column_exists(table_name, old_name) and not column_exists(table_name, new_name):
        print(f"Renaming column {old_name} to {new_name} in {table_name}")
        
        # For MySQL, we need to specify the existing type
        if column_type is None:
            # Try to detect the type
            connection = op.get_bind()
            inspector = inspect(connection)
            columns = inspector.get_columns(table_name)
            for col in columns:
                if col['name'] == old_name:
                    column_type = col['type']
                    break
        
        if column_type:
            op.alter_column(table_name, old_name, 
                           new_column_name=new_name,
                           existing_type=column_type)
            return True
        else:
            print(f"Warning: Could not determine type for column {old_name}")
            return False
    elif column_exists(table_name, new_name):
        print(f"Column {new_name} already exists in {table_name}, skipping rename")
        return False
    else:
        print(f"Column {old_name} doesn't exist in {table_name}, skipping rename")
        return False


def safe_create_index(table_name, columns, index_name=None, unique=False):
    """Safely create an index only if it doesn't exist"""
    if index_name is None:
        # Generate a default index name
        index_name = f"ix_{table_name}_{'_'.join(columns)}"
    
    if not index_exists(table_name, index_name):
        print(f"Creating index {index_name} on {table_name}({', '.join(columns)})")
        op.create_index(index_name, table_name, columns, unique=unique)
        return True
    else:
        print(f"Index {index_name} already exists, skipping")
        return False


def safe_drop_index(table_name, index_name):
    """Safely drop an index only if it exists"""
    if index_exists(table_name, index_name):
        print(f"Dropping index {index_name} from {table_name}")
        op.drop_index(index_name, table_name)
        return True
    else:
        print(f"Index {index_name} doesn't exist, skipping")
        return False


def safe_create_table(table_name, *columns, **kwargs):
    """Safely create a table only if it doesn't exist"""
    if not table_exists(table_name):
        print(f"Creating table {table_name}")
        op.create_table(table_name, *columns, **kwargs)
        return True
    else:
        print(f"Table {table_name} already exists, skipping creation")
        return False


def safe_drop_table(table_name):
    """Safely drop a table only if it exists"""
    if table_exists(table_name):
        print(f"Dropping table {table_name}")
        op.drop_table(table_name)
        return True
    else:
        print(f"Table {table_name} doesn't exist, skipping")
        return False


def get_table_columns(table_name):
    """Get all columns for a table"""
    try:
        connection = op.get_bind()
        inspector = inspect(connection)
        return inspector.get_columns(table_name)
    except Exception:
        return []


def execute_sql_if_condition(sql, condition_sql, description="SQL operation"):
    """Execute SQL only if a condition is met"""
    try:
        connection = op.get_bind()
        
        # Check the condition
        result = connection.execute(text(condition_sql))
        should_execute = bool(result.fetchone()[0])
        
        if should_execute:
            print(f"Executing {description}")
            connection.execute(text(sql))
            return True
        else:
            print(f"Condition not met for {description}, skipping")
            return False
    except Exception as e:
        print(f"Warning: Failed to execute {description}: {e}")
        return False


def migration_summary(table_name):
    """Print a summary of the table structure after migration"""
    try:
        columns = get_table_columns(table_name)
        print(f"\n{table_name} table structure after migration:")
        for col in columns:
            nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
            default = f" DEFAULT {col.get('default', '')}" if col.get('default') else ""
            print(f"  {col['name']} - {col['type']} {nullable}{default}")
        print()
    except Exception as e:
        print(f"Could not display table summary: {e}")


# Backward compatibility functions for new alembic helpers
def check_multiple_heads():
    """
    Backward compatibility wrapper for checking multiple heads
    Returns: (has_multiple_heads, list_of_heads)
    """
    import subprocess
    import os
    
    try:
        result = subprocess.run(['alembic', 'heads'], 
                              capture_output=True, text=True, 
                              cwd=os.getcwd(), check=False)
        
        if result.returncode == 0:
            heads = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            return len(heads) > 1, heads
        else:
            print(f"Failed to check heads: {result.stderr}")
            return False, []
    except Exception as e:
        print(f"Error checking heads: {e}")
        return False, []


def merge_heads_safely(allow_auto_merge=False):
    """
    Backward compatibility wrapper for merging heads safely
    """
    import subprocess
    import os
    
    if not allow_auto_merge:
        print("Auto-merge is disabled. Please resolve manually.")
        return False
    
    try:
        # Check if we have multiple heads
        has_multiple, heads = check_multiple_heads()
        
        if not has_multiple:
            print("Only one head found - no merge needed")
            return True
            
        print(f"Found {len(heads)} heads - merging...")
        
        # Create merge migration
        merge_result = subprocess.run([
            'alembic', 'merge', '-m', 'auto merge conflicting heads during startup', 'heads'
        ], capture_output=True, text=True, cwd=os.getcwd(), check=False)
        
        if merge_result.returncode == 0:
            print("✅ Heads merged successfully")
            print(f"Merge output: {merge_result.stdout}")
            
            # Upgrade to merged head
            upgrade_result = subprocess.run(['alembic', 'upgrade', 'head'],
                                          capture_output=True, text=True, 
                                          cwd=os.getcwd(), check=False)
            
            if upgrade_result.returncode == 0:
                print("✅ Database upgraded to merged head")
                return True
            else:
                print(f"Failed to upgrade after merge: {upgrade_result.stderr}")
                return False
        else:
            print(f"Failed to merge heads: {merge_result.stderr}")
            return False
            
    except Exception as e:
        print(f"Failed to merge heads: {e}")
        return False
