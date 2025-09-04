"""merge_heads_before_partitioning

Revision ID: ae704cc1468a
Revises: 36814ca63b22, 79ddd61092cc
Create Date: 2025-09-02 18:54:06.343386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ae704cc1468a'
down_revision: Union[str, Sequence[str], None] = ('36814ca63b22', '79ddd61092cc')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
