"""merge_heads_before_constraint_optimization

Revision ID: 9112011517ea
Revises: a9f5f7465f50, 007_add_password_format
Create Date: 2025-09-02 18:36:46.849974

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9112011517ea'
down_revision: Union[str, Sequence[str], None] = ('a9f5f7465f50', '007_add_password_format')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
