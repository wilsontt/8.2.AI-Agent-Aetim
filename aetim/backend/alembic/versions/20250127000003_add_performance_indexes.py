"""add_performance_indexes

Revision ID: 20250127000003
Revises: 20250127000002
Create Date: 2025-01-27 00:00:03.000000

效能優化索引
符合 T-5-4-2：效能優化
符合 AC-014-5：建立索引以支援高效能查詢
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250127000003'
down_revision = '20250127000002'
branch_labels = None
depends_on = None


def upgrade():
    """
    新增效能優化索引
    
    符合 AC-014-5：建立索引以支援高效能查詢（依 CVE、產品名稱、風險分數等）
    """
    # 威脅表索引
    op.create_index(
        'IX_Threats_CVE',
        'threats',
        ['cve'],
        unique=False
    )
    op.create_index(
        'IX_Threats_CreatedAt',
        'threats',
        ['created_at'],
        unique=False
    )
    op.create_index(
        'IX_Threats_CVSSBaseScore',
        'threats',
        ['cvss_base_score'],
        unique=False
    )
    op.create_index(
        'IX_Threats_ThreatFeedId',
        'threats',
        ['threat_feed_id'],
        unique=False
    )
    
    # 風險評估表索引
    op.create_index(
        'IX_RiskAssessments_RiskLevel',
        'risk_assessments',
        ['risk_level'],
        unique=False
    )
    op.create_index(
        'IX_RiskAssessments_FinalRiskScore',
        'risk_assessments',
        ['final_risk_score'],
        unique=False
    )
    op.create_index(
        'IX_RiskAssessments_CreatedAt',
        'risk_assessments',
        ['created_at'],
        unique=False
    )
    
    # 威脅資產關聯表索引
    op.create_index(
        'IX_ThreatAssetAssociations_ThreatId',
        'threat_asset_associations',
        ['threat_id'],
        unique=False
    )
    op.create_index(
        'IX_ThreatAssetAssociations_AssetId',
        'threat_asset_associations',
        ['asset_id'],
        unique=False
    )
    op.create_index(
        'IX_ThreatAssetAssociations_CreatedAt',
        'threat_asset_associations',
        ['created_at'],
        unique=False
    )
    
    # 資產產品表索引
    op.create_index(
        'IX_AssetProducts_ProductName',
        'asset_products',
        ['product_name'],
        unique=False
    )
    op.create_index(
        'IX_AssetProducts_ProductType',
        'asset_products',
        ['product_type'],
        unique=False
    )
    
    # 稽核日誌表索引
    op.create_index(
        'IX_AuditLogs_CreatedAt',
        'audit_logs',
        ['created_at'],
        unique=False
    )
    op.create_index(
        'IX_AuditLogs_Action',
        'audit_logs',
        ['action'],
        unique=False
    )
    op.create_index(
        'IX_AuditLogs_ResourceType',
        'audit_logs',
        ['resource_type'],
        unique=False
    )
    op.create_index(
        'IX_AuditLogs_UserId',
        'audit_logs',
        ['user_id'],
        unique=False
    )


def downgrade():
    """移除效能優化索引"""
    # 稽核日誌表索引
    op.drop_index('IX_AuditLogs_UserId', table_name='audit_logs')
    op.drop_index('IX_AuditLogs_ResourceType', table_name='audit_logs')
    op.drop_index('IX_AuditLogs_Action', table_name='audit_logs')
    op.drop_index('IX_AuditLogs_CreatedAt', table_name='audit_logs')
    
    # 資產產品表索引
    op.drop_index('IX_AssetProducts_ProductType', table_name='asset_products')
    op.drop_index('IX_AssetProducts_ProductName', table_name='asset_products')
    
    # 威脅資產關聯表索引
    op.drop_index('IX_ThreatAssetAssociations_CreatedAt', table_name='threat_asset_associations')
    op.drop_index('IX_ThreatAssetAssociations_AssetId', table_name='threat_asset_associations')
    op.drop_index('IX_ThreatAssetAssociations_ThreatId', table_name='threat_asset_associations')
    
    # 風險評估表索引
    op.drop_index('IX_RiskAssessments_CreatedAt', table_name='risk_assessments')
    op.drop_index('IX_RiskAssessments_FinalRiskScore', table_name='risk_assessments')
    op.drop_index('IX_RiskAssessments_RiskLevel', table_name='risk_assessments')
    
    # 威脅表索引
    op.drop_index('IX_Threats_ThreatFeedId', table_name='threats')
    op.drop_index('IX_Threats_CVSSBaseScore', table_name='threats')
    op.drop_index('IX_Threats_CreatedAt', table_name='threats')
    op.drop_index('IX_Threats_CVE', table_name='threats')

