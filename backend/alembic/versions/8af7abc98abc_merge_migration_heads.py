"""merge migration heads

Revision ID: 8af7abc98abc
Revises: 009_remove_role_column, fbbe54e05259
Create Date: 2025-08-11 20:57:26.997937

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8af7abc98abc'
down_revision: Union[str, Sequence[str], None] = ('009_remove_role_column', 'fbbe54e05259')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
