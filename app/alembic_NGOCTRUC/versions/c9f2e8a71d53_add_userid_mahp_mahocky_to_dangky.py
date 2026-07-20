"""add_userId_MaHP_MaHocKy_to_DangKy

Revision ID: c9f2e8a71d53
Revises: d68ad340346a
Create Date: 2026-05-22 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9f2e8a71d53'
down_revision: Union[str, Sequence[str], None] = 'd68ad340346a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Thêm các cột userId, MaHP, MaHocKy vào bảng DangKy để đồng bộ với Python model."""
    op.add_column('DangKy', sa.Column('userId', sa.String(length=50), nullable=True))
    op.create_foreign_key(
        'fk_dk_userid', 'DangKy', 'users', ['userId'], ['userId']
    )

    op.add_column('DangKy', sa.Column('MaHP', sa.String(length=20), nullable=True))
    op.create_foreign_key(
        'fk_dk_mahp', 'DangKy', 'HocPhan', ['MaHP'], ['MaHP']
    )

    op.add_column('DangKy', sa.Column('MaHocKy', sa.String(length=20), nullable=True))
    op.create_foreign_key(
        'fk_dk_mahocky', 'DangKy', 'HocKy', ['MaHocKy'], ['MaHocKy']
    )

    op.create_unique_constraint('uq_dk_user_hp_hk', 'DangKy', ['userId', 'MaHP', 'MaHocKy'])


def downgrade() -> None:
    """Xóa các cột đã thêm."""
    op.drop_constraint('uq_dk_user_hp_hk', 'DangKy', type_='unique')
    op.drop_constraint('fk_dk_mahocky', 'DangKy', type_='foreignkey')
    op.drop_column('DangKy', 'MaHocKy')
    op.drop_constraint('fk_dk_mahp', 'DangKy', type_='foreignkey')
    op.drop_column('DangKy', 'MaHP')
    op.drop_constraint('fk_dk_userid', 'DangKy', type_='foreignkey')
    op.drop_column('DangKy', 'userId')
