"""add_failed_step_to_enum

Revision ID: 4180c3fd9ee3
Revises: a4f82f8a87af
Create Date: 2026-05-15 07:09:33.184159

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4180c3fd9ee3'
down_revision: Union[str, Sequence[str], None] = 'a4f82f8a87af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Thêm giá trị FAILED vào enum buocgiaotac
    # Lưu ý: Postgres yêu cầu chạy ngoài transaction block cho ALTER TYPE ADD VALUE
    op.execute("COMMIT")
    op.execute("ALTER TYPE buocgiaotac ADD VALUE IF NOT EXISTS 'FAILED'")
    op.execute("ALTER TYPE trangthaigiaotac ADD VALUE IF NOT EXISTS 'THAT_BAI'")


def downgrade() -> None:
    """Downgrade schema."""
    # Downgrade cho Enum trong Postgres rất phức tạp (không thể dễ dàng xóa value)
    # Nên thường để pass hoặc thông báo không hỗ trợ
    pass
