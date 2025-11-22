"""InitialCreate

建立所有資料表（初始 Schema）

Revision ID: 20241121000001
Revises: 
Create Date: 2025-11-21 00:00:01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '20241121000001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    升級：建立所有資料表
    """
    # 資產管理模組
    op.create_table(
        'assets',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('item', sa.Integer(), nullable=True),
        sa.Column('ip', sa.String(length=500), nullable=True),
        sa.Column('host_name', sa.String(length=200), nullable=False),
        sa.Column('operating_system', sa.String(length=500), nullable=False),
        sa.Column('running_applications', sa.Text(), nullable=False),
        sa.Column('owner', sa.String(length=200), nullable=False),
        sa.Column('data_sensitivity', sa.String(length=10), nullable=False),
        sa.Column('is_public_facing', sa.Boolean(), nullable=False),
        sa.Column('business_criticality', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=False),
        sa.Column('updated_by', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('IX_Assets_HostName', 'assets', ['host_name'], unique=False)
    op.create_index('IX_Assets_IsPublicFacing', 'assets', ['is_public_facing'], unique=False)
    op.create_index('IX_Assets_DataSensitivity', 'assets', ['data_sensitivity'], unique=False)
    op.create_index('IX_Assets_BusinessCriticality', 'assets', ['business_criticality'], unique=False)

    op.create_table(
        'asset_products',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('asset_id', sa.CHAR(36), nullable=False),
        sa.Column('product_name', sa.String(length=200), nullable=False),
        sa.Column('product_version', sa.String(length=100), nullable=True),
        sa.Column('product_type', sa.String(length=50), nullable=True),
        sa.Column('original_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('IX_AssetProducts_AssetId', 'asset_products', ['asset_id'], unique=False)
    op.create_index('IX_AssetProducts_ProductName', 'asset_products', ['product_name'], unique=False)

    # 威脅情資模組
    op.create_table(
        'threat_feeds',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(length=10), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('collection_frequency', sa.String(length=50), nullable=False),
        sa.Column('collection_strategy', sa.Text(), nullable=True),
        sa.Column('api_key', sa.String(length=500), nullable=True),
        sa.Column('last_collection_time', sa.DateTime(), nullable=True),
        sa.Column('last_collection_status', sa.String(length=20), nullable=True),
        sa.Column('last_collection_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=False),
        sa.Column('updated_by', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('IX_ThreatFeeds_Name', 'threat_feeds', ['name'], unique=False)
    op.create_index('IX_ThreatFeeds_IsEnabled', 'threat_feeds', ['is_enabled'], unique=False)
    op.create_index('IX_ThreatFeeds_Priority', 'threat_feeds', ['priority'], unique=False)

    op.create_table(
        'threats',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('cve', sa.String(length=50), nullable=True),
        sa.Column('threat_feed_id', sa.CHAR(36), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cvss_base_score', sa.Numeric(precision=3, scale=1), nullable=True),
        sa.Column('cvss_vector', sa.String(length=200), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=True),
        sa.Column('published_date', sa.DateTime(), nullable=True),
        sa.Column('affected_products', sa.Text(), nullable=True),
        sa.Column('threat_type', sa.String(length=100), nullable=True),
        sa.Column('ttps', sa.Text(), nullable=True),
        sa.Column('iocs', sa.Text(), nullable=True),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('raw_data', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['threat_feed_id'], ['threat_feeds.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cve')
    )
    op.create_index('IX_Threats_CVE', 'threats', ['cve'], unique=False)
    op.create_index('IX_Threats_ThreatFeedId', 'threats', ['threat_feed_id'], unique=False)
    op.create_index('IX_Threats_Status', 'threats', ['status'], unique=False)
    op.create_index('IX_Threats_CVSS_BaseScore', 'threats', ['cvss_base_score'], unique=False)
    op.create_index('IX_Threats_PublishedDate', 'threats', ['published_date'], unique=False)

    # 分析與評估模組
    op.create_table(
        'pirs',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(length=10), nullable=False),
        sa.Column('condition_type', sa.String(length=50), nullable=False),
        sa.Column('condition_value', sa.Text(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=False),
        sa.Column('updated_by', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('IX_PIRs_IsEnabled', 'pirs', ['is_enabled'], unique=False)
    op.create_index('IX_PIRs_Priority', 'pirs', ['priority'], unique=False)

    op.create_table(
        'threat_asset_associations',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('threat_id', sa.CHAR(36), nullable=False),
        sa.Column('asset_id', sa.CHAR(36), nullable=False),
        sa.Column('match_confidence', sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column('match_type', sa.String(length=50), nullable=False),
        sa.Column('match_details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.ForeignKeyConstraint(['threat_id'], ['threats.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('threat_id', 'asset_id', name='UQ_ThreatAssetAssociations_ThreatId_AssetId')
    )
    op.create_index('IX_ThreatAssetAssociations_ThreatId', 'threat_asset_associations', ['threat_id'], unique=False)
    op.create_index('IX_ThreatAssetAssociations_AssetId', 'threat_asset_associations', ['asset_id'], unique=False)

    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('threat_id', sa.CHAR(36), nullable=False),
        sa.Column('threat_asset_association_id', sa.CHAR(36), nullable=False),
        sa.Column('base_cvss_score', sa.Numeric(precision=3, scale=1), nullable=False),
        sa.Column('asset_importance_weight', sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column('affected_asset_count', sa.Integer(), nullable=False),
        sa.Column('pir_match_weight', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('cisa_kev_weight', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('final_risk_score', sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column('risk_level', sa.String(length=20), nullable=False),
        sa.Column('calculation_details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['threat_asset_association_id'], ['threat_asset_associations.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.ForeignKeyConstraint(['threat_id'], ['threats.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('IX_RiskAssessments_ThreatId', 'risk_assessments', ['threat_id'], unique=False)
    op.create_index('IX_RiskAssessments_RiskLevel', 'risk_assessments', ['risk_level'], unique=False)
    op.create_index('IX_RiskAssessments_FinalRiskScore', 'risk_assessments', ['final_risk_score'], unique=False)

    # 報告與通知模組
    op.create_table(
        'reports',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('report_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('file_format', sa.String(length=20), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=True),
        sa.Column('period_end', sa.DateTime(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('IX_Reports_ReportType', 'reports', ['report_type'], unique=False)
    op.create_index('IX_Reports_GeneratedAt', 'reports', ['generated_at'], unique=False)

    op.create_table(
        'notification_rules',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('risk_score_threshold', sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('send_time', sa.Time(), nullable=True),
        sa.Column('recipients', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=False),
        sa.Column('updated_by', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('IX_NotificationRules_NotificationType', 'notification_rules', ['notification_type'], unique=False)
    op.create_index('IX_NotificationRules_IsEnabled', 'notification_rules', ['is_enabled'], unique=False)

    op.create_table(
        'notifications',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('notification_rule_id', sa.CHAR(36), nullable=True),
        sa.Column('related_threat_id', sa.CHAR(36), nullable=True),
        sa.Column('related_report_id', sa.CHAR(36), nullable=True),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('recipients', sa.Text(), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['notification_rule_id'], ['notification_rules.id'], ondelete='SET NULL', onupdate='CASCADE'),
        sa.ForeignKeyConstraint(['related_report_id'], ['reports.id'], ondelete='SET NULL', onupdate='CASCADE'),
        sa.ForeignKeyConstraint(['related_threat_id'], ['threats.id'], ondelete='SET NULL', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('IX_Notifications_SentAt', 'notifications', ['sent_at'], unique=False)
    op.create_index('IX_Notifications_Status', 'notifications', ['status'], unique=False)
    op.create_index('IX_Notifications_RelatedThreatId', 'notifications', ['related_threat_id'], unique=False)

    # 系統管理模組
    op.create_table(
        'users',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('subject_id', sa.String(length=200), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('subject_id')
    )
    op.create_index('IX_Users_SubjectId', 'users', ['subject_id'], unique=False)
    op.create_index('IX_Users_Email', 'users', ['email'], unique=False)

    op.create_table(
        'roles',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table(
        'permissions',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('resource', sa.String(length=200), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    op.create_table(
        'user_roles',
        sa.Column('user_id', sa.CHAR(36), nullable=False),
        sa.Column('role_id', sa.CHAR(36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.CHAR(36), nullable=False),
        sa.Column('permission_id', sa.CHAR(36), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    op.create_table(
        'system_configurations',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('key', sa.String(length=200), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('updated_by', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index('IX_SystemConfigurations_Key', 'system_configurations', ['key'], unique=False)
    op.create_index('IX_SystemConfigurations_Category', 'system_configurations', ['category'], unique=False)

    op.create_table(
        'schedules',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('schedule_type', sa.String(length=50), nullable=False),
        sa.Column('cron_expression', sa.String(length=100), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('last_run_time', sa.DateTime(), nullable=True),
        sa.Column('next_run_time', sa.DateTime(), nullable=True),
        sa.Column('last_run_status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=False),
        sa.Column('updated_by', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('IX_Schedules_ScheduleType', 'schedules', ['schedule_type'], unique=False)
    op.create_index('IX_Schedules_IsEnabled', 'schedules', ['is_enabled'], unique=False)
    op.create_index('IX_Schedules_NextRunTime', 'schedules', ['next_run_time'], unique=False)

    # 稽核日誌模組
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.CHAR(36), nullable=False),
        sa.Column('user_id', sa.CHAR(36), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.CHAR(36), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('IX_AuditLogs_UserId', 'audit_logs', ['user_id'], unique=False)
    op.create_index('IX_AuditLogs_ResourceType', 'audit_logs', ['resource_type'], unique=False)
    op.create_index('IX_AuditLogs_CreatedAt', 'audit_logs', ['created_at'], unique=False)
    op.create_index('IX_AuditLogs_UserId_CreatedAt', 'audit_logs', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    """
    降級：刪除所有資料表
    """
    # 刪除索引
    op.drop_index('IX_AuditLogs_UserId_CreatedAt', table_name='audit_logs')
    op.drop_index('IX_AuditLogs_CreatedAt', table_name='audit_logs')
    op.drop_index('IX_AuditLogs_ResourceType', table_name='audit_logs')
    op.drop_index('IX_AuditLogs_UserId', table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index('IX_Schedules_NextRunTime', table_name='schedules')
    op.drop_index('IX_Schedules_IsEnabled', table_name='schedules')
    op.drop_index('IX_Schedules_ScheduleType', table_name='schedules')
    op.drop_table('schedules')

    op.drop_index('IX_SystemConfigurations_Category', table_name='system_configurations')
    op.drop_index('IX_SystemConfigurations_Key', table_name='system_configurations')
    op.drop_table('system_configurations')

    op.drop_table('role_permissions')
    op.drop_table('user_roles')
    op.drop_table('permissions')
    op.drop_table('roles')

    op.drop_index('IX_Users_Email', table_name='users')
    op.drop_index('IX_Users_SubjectId', table_name='users')
    op.drop_table('users')

    op.drop_index('IX_Notifications_RelatedThreatId', table_name='notifications')
    op.drop_index('IX_Notifications_Status', table_name='notifications')
    op.drop_index('IX_Notifications_SentAt', table_name='notifications')
    op.drop_table('notifications')

    op.drop_index('IX_NotificationRules_IsEnabled', table_name='notification_rules')
    op.drop_index('IX_NotificationRules_NotificationType', table_name='notification_rules')
    op.drop_table('notification_rules')

    op.drop_index('IX_Reports_GeneratedAt', table_name='reports')
    op.drop_index('IX_Reports_ReportType', table_name='reports')
    op.drop_table('reports')

    op.drop_index('IX_RiskAssessments_FinalRiskScore', table_name='risk_assessments')
    op.drop_index('IX_RiskAssessments_RiskLevel', table_name='risk_assessments')
    op.drop_index('IX_RiskAssessments_ThreatId', table_name='risk_assessments')
    op.drop_table('risk_assessments')

    op.drop_index('IX_ThreatAssetAssociations_AssetId', table_name='threat_asset_associations')
    op.drop_index('IX_ThreatAssetAssociations_ThreatId', table_name='threat_asset_associations')
    op.drop_table('threat_asset_associations')

    op.drop_index('IX_PIRs_Priority', table_name='pirs')
    op.drop_index('IX_PIRs_IsEnabled', table_name='pirs')
    op.drop_table('pirs')

    op.drop_index('IX_Threats_PublishedDate', table_name='threats')
    op.drop_index('IX_Threats_CVSS_BaseScore', table_name='threats')
    op.drop_index('IX_Threats_Status', table_name='threats')
    op.drop_index('IX_Threats_ThreatFeedId', table_name='threats')
    op.drop_index('IX_Threats_CVE', table_name='threats')
    op.drop_table('threats')

    op.drop_index('IX_ThreatFeeds_Priority', table_name='threat_feeds')
    op.drop_index('IX_ThreatFeeds_IsEnabled', table_name='threat_feeds')
    op.drop_index('IX_ThreatFeeds_Name', table_name='threat_feeds')
    op.drop_table('threat_feeds')

    op.drop_index('IX_AssetProducts_ProductName', table_name='asset_products')
    op.drop_index('IX_AssetProducts_AssetId', table_name='asset_products')
    op.drop_table('asset_products')

    op.drop_index('IX_Assets_BusinessCriticality', table_name='assets')
    op.drop_index('IX_Assets_DataSensitivity', table_name='assets')
    op.drop_index('IX_Assets_IsPublicFacing', table_name='assets')
    op.drop_index('IX_Assets_HostName', table_name='assets')
    op.drop_table('assets')

