"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
import sys
import os
${imports if imports else ""}

# Add the alembic directory to the path to import migration_utils
sys.path.append(os.path.dirname(__file__))
try:
    from migration_utils import (
        column_exists, table_exists, index_exists,
        safe_add_column, safe_drop_column, safe_rename_column,
        safe_create_index, safe_drop_index,
        execute_sql_if_condition, migration_summary
    )
except ImportError:
    # Fallback minimal functions if utils aren't available
    def column_exists(table_name, column_name):
        try:
            connection = op.get_bind()
            inspector = sa.inspect(connection)
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            return column_name in columns
        except Exception:
            return False
    
    def table_exists(table_name):
        try:
            connection = op.get_bind()
            inspector = sa.inspect(connection)
            return table_name in inspector.get_table_names()
        except Exception:
            return False
    
    def safe_add_column(table_name, column_name, column_type, **kwargs):
        if not column_exists(table_name, column_name):
            print(f"Adding column {column_name} to {table_name}")
            op.add_column(table_name, sa.Column(column_name, column_type, **kwargs))
            return True
        else:
            print(f"Column {column_name} already exists in {table_name}, skipping")
            return False
    
    def migration_summary(table_name):
        try:
            connection = op.get_bind()
            inspector = sa.inspect(connection)
            columns = inspector.get_columns(table_name)
            print(f"\n{table_name} table structure after migration:")
            for col in columns:
                nullable = "NULL" if col.get('nullable', True) else "NOT NULL"
                print(f"  {col['name']} - {col['type']} {nullable}")
            print()
        except Exception as e:
            print(f"Could not display table summary: {e}")

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    """Apply the migration changes"""
    print("Starting migration: ${message}")
    
    # Example idempotent operations:
    
    # Add columns only if they don't exist
    # safe_add_column('table_name', 'column_name', sa.String(length=255), nullable=False)
    
    # Rename columns only if source exists and target doesn't
    # safe_rename_column('table_name', 'old_name', 'new_name', sa.String(length=255))
    
    # Execute SQL only when conditions are met
    # execute_sql_if_condition(
    #     sql="UPDATE table_name SET column = 'value' WHERE condition",
    #     condition_sql="SELECT COUNT(*) FROM table_name WHERE condition_that_needs_update",
    #     description="updating specific records"
    # )
    
    # Create indexes only if they don't exist
    # safe_create_index('table_name', ['column1', 'column2'], 'index_name')
    
    print("Migration completed successfully")
    # migration_summary('table_name')  # Show table structure after changes


def downgrade():
    """Reverse the migration changes"""
    print("Reversing migration: ${message}")
    
    # Reverse operations in opposite order
    # safe_drop_index('table_name', 'index_name')
    # safe_drop_column('table_name', 'column_name')
    # safe_rename_column('table_name', 'new_name', 'old_name', sa.String(length=255))
    
    print("Migration reversal completed successfully")
    # migration_summary('table_name')
