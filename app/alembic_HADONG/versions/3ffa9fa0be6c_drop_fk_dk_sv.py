"""drop_fk_dk_sv

Revision ID: 3ffa9fa0be6c
Revises: b8468531a136
Create Date: 2026-05-22 01:45:46.158863

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ffa9fa0be6c'
down_revision: Union[str, Sequence[str], None] = 'b8468531a136'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('fk_dk_sv', 'DangKy', type_='foreignkey')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_foreign_key('fk_dk_sv', 'DangKy', 'SinhVien', ['MaSV'], ['MaSV'])
