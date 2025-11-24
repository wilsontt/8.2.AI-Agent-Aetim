"""add risk_assessment_history

Revision ID: 20250127000001
Revises: 20241121000001
Create Date: 2025-01-27 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '20250127000001'
down_revision = '20241121000001'
branch_labels = None
depends_on = None


def upgrade():
    """建立 risk_assessment_histories 表"""
    op.create_table(
        'risk_assessment_histories',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('risk_assessment_id', sa.CHAR(36), nullable=False),
        sa.Column('base_cvss_score', sa.Numeric(precision=3, scale=1), nullable=False),
        sa.Column('asset_importance_weight', sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column('asset_count_weight', sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column('pir_match_weight', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('cisa_kev_weight', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('final_risk_score', sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('calculation_details', sa.Text(), nullable=True),
        sa.Column('calculated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ['risk_assessment_id'],
            ['risk_assessments.id'],
            ondelete='CASCADE',
            onupdate='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'IX_RiskAssessmentHistories_RiskAssessmentId',
        'risk_assessment_histories',
        ['risk_assessment_id'],
        unique=False
    )
    op.create_index(
        'IX_RiskAssessmentHistories_CalculatedAt',
        'risk_assessment_histories',
        ['calculated_at'],
        unique=False
    )


def downgrade():
    """刪除 risk_assessment_histories 表"""
    op.drop_index('IX_RiskAssessmentHistories_CalculatedAt', table_name='risk_assessment_histories')
    op.drop_index('IX_RiskAssessmentHistories_RiskAssessmentId', table_name='risk_assessment_histories')
    op.drop_table('risk_assessment_histories')

