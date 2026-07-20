"""add_failed_step_to_enum

Revision ID: f138f6828af9
Revises: ddf0d2a4fb49
Create Date: 2026-05-15 07:10:30.351721

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f138f6828af9'
down_revision: Union[str, Sequence[str], None] = 'ddf0d2a4fb49'
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
