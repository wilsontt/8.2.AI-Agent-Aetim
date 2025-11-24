"""add report_schedules

Revision ID: 20250127000002
Revises: 20250127000001
Create Date: 2025-01-27 00:00:02.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '20250127000002'
down_revision = '20250127000001'
branch_labels = None
depends_on = None


def upgrade():
    """建立 report_schedules 表"""
    op.create_table(
        'report_schedules',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('report_type', sa.String(length=50), nullable=False, comment='報告類型（CISO_Weekly/IT_Ticket）'),
        sa.Column('cron_expression', sa.String(length=100), nullable=False, comment='Cron 表達式'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, default=True, comment='是否啟用'),
        sa.Column('recipients', sa.Text(), nullable=False, comment='收件人清單（JSON 格式）'),
        sa.Column('file_format', sa.String(length=20), nullable=False, default='HTML', comment='檔案格式（HTML/PDF）'),
        sa.Column('last_run_at', sa.DateTime(), nullable=True, comment='最後執行時間'),
        sa.Column('next_run_at', sa.DateTime(), nullable=True, comment='下次執行時間'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'IX_ReportSchedules_ReportType',
        'report_schedules',
        ['report_type'],
        unique=False
    )
    op.create_index(
        'IX_ReportSchedules_IsEnabled',
        'report_schedules',
        ['is_enabled'],
        unique=False
    )


def downgrade():
    """移除 report_schedules 表"""
    op.drop_index('IX_ReportSchedules_IsEnabled', table_name='report_schedules')
    op.drop_index('IX_ReportSchedules_ReportType', table_name='report_schedules')
    op.drop_table('report_schedules')

