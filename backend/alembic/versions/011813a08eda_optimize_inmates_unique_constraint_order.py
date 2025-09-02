"""optimize_inmates_unique_constraint_order

Revision ID: 011813a08eda
Revises: 9112011517ea
Create Date: 2025-09-02 18:36:52.057214

Optimizes the unique constraint on the inmates table by reordering columns for better performance.
Changes from: (name, race, dob, sex, arrest_date, jail_id)
To: (jail_id, arrest_date, name, dob, sex, race)

This order improves performance because:
1. jail_id first - Most selective for queries (each jail processes separately)  
2. arrest_date second - Good selectivity, often used in date-range queries
3. name third - High selectivity for most common lookups
4. dob, sex, race - Handle edge cases with same names

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from migration_utils import safe_drop_constraint, safe_create_unique_constraint


# revision identifiers, used by Alembic.
revision: str = '011813a08eda'
down_revision: Union[str, Sequence[str], None] = '9112011517ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema by optimizing the inmates unique constraint order."""
    print("🔧 Optimizing inmates unique constraint for better performance...")
    
    # Drop the old constraint if it exists
    old_dropped = safe_drop_constraint('inmates', 'unique_inmate_new', 'unique')
    
    # Also try dropping any other variations that might exist
    safe_drop_constraint('inmates', 'unique_inmate', 'unique')
    safe_drop_constraint('inmates', 'uq_inmates_name_race_dob_sex_arrest_date_jail_id', 'unique')
    
    # Create the new optimized constraint with better column order
    new_created = safe_create_unique_constraint(
        'inmates', 
        'unique_inmate_optimized',
        ['jail_id', 'arrest_date', 'name', 'dob', 'sex', 'race']
    )
    
    if new_created:
        print("✅ Successfully created optimized unique constraint")
        print("   New order: (jail_id, arrest_date, name, dob, sex, race)")
        print("   This should significantly improve performance on large databases")
    elif old_dropped:
        print("⚠️  Dropped old constraint but couldn't create new one - check manually")
    else:
        print("ℹ️  No changes needed - constraint may already be optimized")


def downgrade() -> None:
    """Downgrade schema by reverting to the original constraint order."""
    print("🔄 Reverting to original inmates unique constraint order...")
    
    # Drop the optimized constraint
    optimized_dropped = safe_drop_constraint('inmates', 'unique_inmate_optimized', 'unique')
    
    # Restore the original constraint with original column order
    original_created = safe_create_unique_constraint(
        'inmates',
        'unique_inmate_new', 
        ['name', 'race', 'dob', 'sex', 'arrest_date', 'jail_id']
    )
    
    if original_created:
        print("✅ Successfully restored original unique constraint")
        print("   Original order: (name, race, dob, sex, arrest_date, jail_id)")
    elif optimized_dropped:
        print("⚠️  Dropped optimized constraint but couldn't create original - check manually")
    else:
        print("ℹ️  No changes needed - constraint may already be in original form")
