"""Fix FK constraints and add unique constraint

Revision ID: 5db04f5e1c8f
Revises: 005_monitor_inmate_links
Create Date: 2025-08-10 20:58:30.765307

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '5db04f5e1c8f'
down_revision = '005_monitor_inmate_links'
branch_labels = None
depends_on = None


def upgrade():
    # First, temporarily disable foreign key checks to modify constraints
    op.execute("SET FOREIGN_KEY_CHECKS = 0")
    
    try:
        # Step 1: Drop existing foreign key constraint first
        print("Updating foreign key constraint to CASCADE...")
        op.drop_constraint('monitor_inmate_links_ibfk_1', 'monitor_inmate_links', type_='foreignkey')
        
        # Step 2: Create new foreign key constraint with CASCADE
        op.create_foreign_key(
            'monitor_inmate_links_ibfk_1',
            'monitor_inmate_links', 'inmates',
            ['inmate_id'], ['idinmates'],
            ondelete='CASCADE'
        )
        
        # Re-enable foreign key checks before cleanup
        op.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # Step 3: Now run cleanup with CASCADE FK in place
        print("Running database cleanup to remove duplicates...")
        
        # Import and run existing maintenance functions
        import sys
        import os
        sys.path.append('/app')
        
        from maintenance import cleanup_duplicates, populate_last_seen
        
        # Run cleanup and populate last_seen
        cleanup_success = cleanup_duplicates()
        if cleanup_success:
            print("Database cleanup completed successfully")
        else:
            print("Database cleanup had issues, but continuing with migration")
            
        populate_success = populate_last_seen()
        if populate_success:
            print("Last seen population completed successfully")
        else:
            print("Last seen population had issues, but continuing with migration")
        
        # Disable FK checks again for final constraint addition
        op.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # Step 4: Add unique constraint to prevent future duplicates
        print("Adding unique constraint to prevent future duplicates...")
        op.create_unique_constraint(
            'unique_inmate_record',
            'inmates',
            ['name', 'race', 'dob', 'sex', 'arrest_date', 'jail_id']
        )
        
        print("Migration completed successfully!")
        
    finally:
        # Re-enable foreign key checks
        op.execute("SET FOREIGN_KEY_CHECKS = 1")


def downgrade():
    # Remove unique constraint
    op.drop_constraint('unique_inmate_record', 'inmates', type_='unique')
    
    # Drop CASCADE foreign key
    op.drop_constraint('monitor_inmate_links_ibfk_1', 'monitor_inmate_links', type_='foreignkey')
    
    # Recreate original foreign key without CASCADE
    op.create_foreign_key(
        'monitor_inmate_links_ibfk_1',
        'monitor_inmate_links', 'inmates',
        ['inmate_id'], ['idinmates']
    )