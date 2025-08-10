"""fix unique constraint and deduplicate

Revision ID: b47722ea223c
Revises: 003
Create Date: 2025-08-09 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'b47722ea223c'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """
    1. Deduplicate existing records based on new unique constraint
    2. Drop old unique constraint
    3. Add new unique constraint: name, race, dob, sex, arrest_date, jail_id
    """
    # Get database connection
    connection = op.get_bind()
    
    print("Starting deduplication process...")
    
    # Step 1: Find and deduplicate records
    # Keep the record with the most recent last_seen (or earliest idinmates if last_seen is null)
    dedup_query = text("""
        DELETE i1 FROM inmates i1
        INNER JOIN inmates i2 
        WHERE i1.name = i2.name 
        AND i1.race = i2.race 
        AND i1.dob = i2.dob 
        AND i1.sex = i2.sex 
        AND i1.arrest_date = i2.arrest_date 
        AND i1.jail_id = i2.jail_id
        AND (
            (i1.last_seen IS NULL AND i2.last_seen IS NOT NULL)
            OR (i1.last_seen < i2.last_seen)
            OR (i1.last_seen = i2.last_seen AND i1.idinmates > i2.idinmates)
            OR (i1.last_seen IS NULL AND i2.last_seen IS NULL AND i1.idinmates > i2.idinmates)
        )
    """)
    
    # Execute deduplication
    result = connection.execute(dedup_query)
    print(f"Deleted {result.rowcount} duplicate records")
    
    # Step 2: Drop the old unique constraint
    print("Dropping old unique constraint...")
    try:
        op.drop_constraint('unique_inmate', 'inmates', type_='unique')
        print("Successfully dropped old unique constraint")
    except Exception as e:
        print(f"Could not drop old constraint (might not exist): {e}")
    
    # Step 3: Add new unique constraint
    print("Adding new unique constraint...")
    op.create_unique_constraint(
        'unique_inmate_new',
        'inmates',
        ['name', 'race', 'dob', 'sex', 'arrest_date', 'jail_id']
    )
    print("Successfully added new unique constraint")


def downgrade():
    """
    Reverse the migration by restoring the old unique constraint
    """
    # Drop the new constraint
    op.drop_constraint('unique_inmate_new', 'inmates', type_='unique')
    
    # Restore the old constraint (though this might fail due to duplicates)
    op.create_unique_constraint(
        'unique_inmate',
        'inmates',
        ['name', 'race', 'dob', 'sex', 'hold_reasons', 'in_custody_date', 'release_date', 'jail_id']
    )
