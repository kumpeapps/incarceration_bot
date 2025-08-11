"""Fix users table column names

Revision ID: 006_fix_users_table_columns
Revises: 005_monitor_inmate_links
Create Date: 2025-08-10 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '006_fix_users_table_columns'
down_revision = '005_monitor_inmate_links'
branch_labels = None
depends_on = None


def upgrade():
    """Fix users table to match API expectations"""
    connection = op.get_bind()
    
    print("Fixing users table column names...")
    
    # Step 1: Rename password_hash to hashed_password
    print("Renaming password_hash to hashed_password...")
    op.alter_column('users', 'password_hash', new_column_name='hashed_password')
    
    # Step 2: Add role column and populate based on is_admin
    print("Adding role column...")
    op.add_column('users', sa.Column('role', sa.String(length=20), nullable=False, server_default='user'))
    
    # Step 3: Update role values based on is_admin
    print("Updating role values...")
    connection.execute(text("""
        UPDATE users 
        SET role = CASE 
            WHEN is_admin = 1 THEN 'admin' 
            ELSE 'user' 
        END
    """))
    
    # Step 4: Remove the is_admin column (optional - we can keep both for compatibility)
    # Commenting this out to maintain backward compatibility
    # print("Dropping is_admin column...")
    # op.drop_column('users', 'is_admin')
    
    print("Users table column fixes completed successfully")


def downgrade():
    """Reverse the column name changes"""
    
    # Restore is_admin column if it was dropped
    # op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    
    # Update is_admin based on role
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE users 
        SET is_admin = CASE 
            WHEN role = 'admin' THEN 1 
            ELSE 0 
        END
    """))
    
    # Remove role column
    op.drop_column('users', 'role')
    
    # Rename hashed_password back to password_hash
    op.alter_column('users', 'hashed_password', new_column_name='password_hash')
