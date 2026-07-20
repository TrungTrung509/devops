"""drop_fk_dk_sv

Revision ID: 293f86647660
Revises: d4a3b7c91e82
Create Date: 2026-05-22 01:45:54.624053

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '293f86647660'
down_revision: Union[str, Sequence[str], None] = 'd4a3b7c91e82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('fk_dk_sv', 'DangKy', type_='foreignkey')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_foreign_key('fk_dk_sv', 'DangKy', 'SinhVien', ['MaSV'], ['MaSV'])
