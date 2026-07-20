"""add_userId_MaHP_MaHocKy_to_DangKy

Revision ID: b8468531a136
Revises: c6083e14140f
Create Date: 2026-05-22 01:04:05.460405

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8468531a136'
down_revision: Union[str, Sequence[str], None] = 'c6083e14140f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Thêm các cột userId, MaHP, MaHocKy vào bảng DangKy để đồng bộ với Python model."""
    # Thêm cột userId (FK tới users)
    op.add_column('DangKy', sa.Column('userId', sa.String(length=50), nullable=True))
    op.create_foreign_key(
        'fk_dk_userid', 'DangKy', 'users', ['userId'], ['userId']
    )

    # Thêm cột MaHP (FK tới HocPhan)
    op.add_column('DangKy', sa.Column('MaHP', sa.String(length=20), nullable=True))
    op.create_foreign_key(
        'fk_dk_mahp', 'DangKy', 'HocPhan', ['MaHP'], ['MaHP']
    )

    # Thêm cột MaHocKy (FK tới HocKy)
    op.add_column('DangKy', sa.Column('MaHocKy', sa.String(length=20), nullable=True))
    op.create_foreign_key(
        'fk_dk_mahocky', 'DangKy', 'HocKy', ['MaHocKy'], ['MaHocKy']
    )

    # Thêm unique constraint để tránh đăng ký trùng (userId, MaHP, MaHocKy)
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
