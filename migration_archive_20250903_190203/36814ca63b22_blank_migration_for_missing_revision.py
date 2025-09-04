"""blank_migration_for_missing_revision

Revision ID: 36814ca63b22
Revises: 
Create Date: 2025-09-02 18:00:00.000000

This is a blank migration created to handle missing revision references.
Some environments may have references to this revision ID that don't exist
in the current codebase. This blank migration prevents Alembic from failing
when it encounters those references.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '36814ca63b22'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Blank upgrade - no changes needed."""
    print("ℹ️  Blank migration 36814ca63b22 - no schema changes")
    print("   This migration exists only to satisfy dependency references")
    pass


def downgrade() -> None:
    """Blank downgrade - no changes needed."""
    print("ℹ️  Blank migration 36814ca63b22 downgrade - no schema changes")
    pass
