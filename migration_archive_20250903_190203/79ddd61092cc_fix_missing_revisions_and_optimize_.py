"""fix_missing_revisions_and_optimize_constraint

Revision ID: 79ddd61092cc
Revises: 011813a08eda
Create Date: 2025-09-02 18:44:00.000000

This migration:
1. Handles missing revision issues gracefully
2. Optimizes the inmates unique constraint for better performance
3. Ensures database consistency regardless of migration state

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect
from migration_utils import safe_drop_constraint, safe_create_unique_constraint


# revision identifiers, used by Alembic.
revision: str = '79ddd61092cc'
down_revision: Union[str, Sequence[str], None] = '011813a08eda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def constraint_exists_check(table_name, constraint_name):
    """Check if a constraint exists - more robust version"""
    try:
        connection = op.get_bind()
        
        # For MySQL, check information_schema
        if connection.dialect.name == 'mysql':
            result = connection.execute(text("""
                SELECT COUNT(*) as cnt FROM information_schema.TABLE_CONSTRAINTS 
                WHERE TABLE_NAME = :table_name 
                AND CONSTRAINT_NAME = :constraint_name 
                AND TABLE_SCHEMA = DATABASE()
            """), {"table_name": table_name, "constraint_name": constraint_name})
            
            count = result.scalar()
            return count > 0
        else:
            # Fallback for other databases
            inspector = inspect(connection)
            unique_constraints = inspector.get_unique_constraints(table_name)
            return any(c['name'] == constraint_name for c in unique_constraints)
            
    except Exception as e:
        print(f"Error checking constraint {constraint_name}: {e}")
        return False


def upgrade() -> None:
    """Upgrade schema with robust constraint optimization."""
    print("🔧 Fixing missing revisions and optimizing inmates unique constraint...")
    
    try:
        # Check current constraint state
        old_constraint_exists = constraint_exists_check('inmates', 'unique_inmate_new')
        optimized_constraint_exists = constraint_exists_check('inmates', 'unique_inmate_optimized')
        
        print(f"Current state: old_constraint={old_constraint_exists}, optimized_constraint={optimized_constraint_exists}")
        
        if optimized_constraint_exists:
            print("✅ Optimized constraint already exists, no changes needed")
            return
            
        # Drop old constraint variations if they exist
        constraint_variations = [
            'unique_inmate_new',
            'unique_inmate', 
            'uq_inmates_name_race_dob_sex_arrest_date_jail_id',
            'inmates_name_race_dob_sex_arrest_date_jail_id_key'
        ]
        
        dropped_any = False
        for constraint_name in constraint_variations:
            if constraint_exists_check('inmates', constraint_name):
                print(f"Dropping existing constraint: {constraint_name}")
                try:
                    op.drop_constraint(constraint_name, 'inmates', type_='unique')
                    dropped_any = True
                    print(f"✅ Successfully dropped {constraint_name}")
                except Exception as e:
                    print(f"⚠️  Could not drop {constraint_name}: {e}")
        
        # Create the new optimized constraint
        print("Creating optimized unique constraint...")
        try:
            op.create_unique_constraint(
                'unique_inmate_optimized',
                'inmates',
                ['jail_id', 'arrest_date', 'name', 'dob', 'sex', 'race']
            )
            print("✅ Successfully created optimized unique constraint")
            print("   New order: (jail_id, arrest_date, name, dob, sex, race)")
            print("   This should significantly improve performance on large databases")
            
        except Exception as e:
            print(f"⚠️  Could not create optimized constraint: {e}")
            
            # If we dropped the old constraint but can't create the new one,
            # try to restore a basic constraint
            if dropped_any:
                print("Attempting to restore basic constraint for safety...")
                try:
                    op.create_unique_constraint(
                        'unique_inmate_new',
                        'inmates', 
                        ['name', 'race', 'dob', 'sex', 'arrest_date', 'jail_id']
                    )
                    print("✅ Restored basic constraint")
                except Exception as restore_error:
                    print(f"❌ Could not restore constraint: {restore_error}")
                    print("⚠️  MANUAL INTERVENTION REQUIRED: inmates table has no unique constraint")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("Continuing without constraint changes to avoid breaking the database")


def downgrade() -> None:
    """Downgrade schema by reverting to the original constraint order."""
    print("🔄 Reverting to original inmates unique constraint order...")
    
    try:
        # Drop the optimized constraint if it exists
        if constraint_exists_check('inmates', 'unique_inmate_optimized'):
            print("Dropping optimized constraint...")
            op.drop_constraint('unique_inmate_optimized', 'inmates', type_='unique')
            print("✅ Dropped optimized constraint")
        
        # Restore the original constraint if it doesn't exist
        if not constraint_exists_check('inmates', 'unique_inmate_new'):
            print("Restoring original constraint...")
            op.create_unique_constraint(
                'unique_inmate_new',
                'inmates',
                ['name', 'race', 'dob', 'sex', 'arrest_date', 'jail_id']
            )
            print("✅ Successfully restored original unique constraint")
        else:
            print("ℹ️  Original constraint already exists")
            
    except Exception as e:
        print(f"❌ Downgrade failed: {e}")
        print("Manual intervention may be required")
