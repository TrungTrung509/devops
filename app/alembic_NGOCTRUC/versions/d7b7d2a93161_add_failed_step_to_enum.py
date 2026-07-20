"""add_failed_step_to_enum

Revision ID: d7b7d2a93161
Revises: 514abb209b2e
Create Date: 2026-05-15 07:10:31.041992

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7b7d2a93161'
down_revision: Union[str, Sequence[str], None] = '514abb209b2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Thêm giá trị FAILED vào enum buocgiaotac
    op.execute("COMMIT")
    op.execute("ALTER TYPE buocgiaotac ADD VALUE IF NOT EXISTS 'FAILED'")
    op.execute("ALTER TYPE trangthaigiaotac ADD VALUE IF NOT EXISTS 'THAT_BAI'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
