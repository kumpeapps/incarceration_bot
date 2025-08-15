"""merge heads

Revision ID: a9f5f7465f50
Revises: 009_optimize_last_seen, 58546d11f1b5, add_sessions_table
Create Date: 2025-08-15 15:50:07.411218

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9f5f7465f50'
down_revision: Union[str, Sequence[str], None] = ('009_optimize_last_seen', '58546d11f1b5', 'add_sessions_table')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
