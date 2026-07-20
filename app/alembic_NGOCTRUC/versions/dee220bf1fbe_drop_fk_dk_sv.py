"""drop_fk_dk_sv

Revision ID: dee220bf1fbe
Revises: c9f2e8a71d53
Create Date: 2026-05-22 01:46:12.893670

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dee220bf1fbe'
down_revision: Union[str, Sequence[str], None] = 'c9f2e8a71d53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('fk_dk_sv', 'DangKy', type_='foreignkey')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_foreign_key('fk_dk_sv', 'DangKy', 'SinhVien', ['MaSV'], ['MaSV'])
