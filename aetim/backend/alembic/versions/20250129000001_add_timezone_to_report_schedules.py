"""add timezone to report_schedules

Revision ID: 20250129000001
Revises: 20250127000002
Create Date: 2025-01-29 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250129000001'
down_revision = '20250127000003'
branch_labels = None
depends_on = None


def upgrade():
    """新增 timezone 欄位到 report_schedules 表"""
    op.add_column(
        'report_schedules',
        sa.Column(
            'timezone',
            sa.String(length=50),
            nullable=False,
            server_default='Asia/Taipei',
            comment='時區設定（例如：Asia/Taipei、UTC）'
        )
    )


def downgrade():
    """移除 timezone 欄位"""
    op.drop_column('report_schedules', 'timezone')
