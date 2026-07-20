"""merge ngoctruc heads

Revision ID: ffa28a06fdb3
Revises: d7b7d2a93161, dee220bf1fbe
Create Date: 2026-05-22 17:32:05.942135

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ffa28a06fdb3'
down_revision: Union[str, Sequence[str], None] = ('d7b7d2a93161', 'dee220bf1fbe')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
