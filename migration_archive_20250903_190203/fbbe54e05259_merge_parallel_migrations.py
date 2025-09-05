"""merge parallel migrations

Revision ID: fbbe54e05259
Revises: 47952153bdcf, 5db04f5e1c8f
Create Date: 2025-08-11 17:05:04.311064

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fbbe54e05259'
down_revision: Union[str, Sequence[str], None] = ('47952153bdcf', '5db04f5e1c8f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
