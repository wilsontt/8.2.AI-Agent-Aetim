"""
資料庫 Schema 整合測試

驗證所有資料表結構、索引、約束是否正確。
"""

import pytest
from sqlalchemy import text, inspect
from shared_kernel.infrastructure.database import engine, Base
from asset_management.infrastructure.persistence.models import Asset, AssetProduct
from threat_intelligence.infrastructure.persistence.models import ThreatFeed, Threat
from analysis_assessment.infrastructure.persistence.models import (
    PIR,
    ThreatAssetAssociation,
    RiskAssessment,
)
from reporting_notification.infrastructure.persistence.models import (
    Report,
    NotificationRule,
    Notification,
)
from system_management.infrastructure.persistence.models import (
    User,
    Role,
    Permission,
    UserRole,
    RolePermission,
    SystemConfiguration,
    Schedule,
    AuditLog,
)


@pytest.mark.integration
@pytest.mark.requires_db
async def test_create_all_tables():
    """測試建立所有資料表"""
    async with engine.begin() as conn:
        # 建立所有資料表
        await conn.run_sync(Base.metadata.create_all)

        # 驗證資料表已建立
        inspector = inspect(engine.sync_engine)
        tables = inspector.get_table_names()

        expected_tables = [
            "assets",
            "asset_products",
            "threat_feeds",
            "threats",
            "pirs",
            "threat_asset_associations",
            "risk_assessments",
            "reports",
            "notification_rules",
            "notifications",
            "users",
            "roles",
            "permissions",
            "user_roles",
            "role_permissions",
            "system_configurations",
            "schedules",
            "audit_logs",
        ]

        for table in expected_tables:
            assert table in tables, f"資料表 {table} 未建立"


@pytest.mark.integration
@pytest.mark.requires_db
async def test_asset_table_structure():
    """測試 Assets 表結構"""
    async with engine.begin() as conn:
        inspector = inspect(engine.sync_engine)
        columns = inspector.get_columns("assets")

        # 驗證必要欄位存在
        column_names = [col["name"] for col in columns]
        required_columns = [
            "id",
            "host_name",
            "operating_system",
            "running_applications",
            "owner",
            "data_sensitivity",
            "is_public_facing",
            "business_criticality",
            "created_at",
            "updated_at",
        ]

        for col in required_columns:
            assert col in column_names, f"欄位 {col} 不存在於 Assets 表"


@pytest.mark.integration
@pytest.mark.requires_db
async def test_foreign_key_constraints():
    """測試外鍵約束"""
    async with engine.begin() as conn:
        # 測試 AssetProducts 的外鍵約束
        inspector = inspect(engine.sync_engine)
        foreign_keys = inspector.get_foreign_keys("asset_products")

        # 驗證 asset_id 外鍵存在
        asset_id_fk = [fk for fk in foreign_keys if "asset_id" in fk["constrained_columns"]]
        assert len(asset_id_fk) > 0, "AssetProducts.asset_id 外鍵不存在"


@pytest.mark.integration
@pytest.mark.requires_db
async def test_indexes():
    """測試索引"""
    async with engine.begin() as conn:
        inspector = inspect(engine.sync_engine)

        # 測試 Assets 表的索引
        indexes = inspector.get_indexes("assets")
        index_names = [idx["name"] for idx in indexes]

        expected_indexes = [
            "IX_Assets_HostName",
            "IX_Assets_IsPublicFacing",
            "IX_Assets_DataSensitivity",
            "IX_Assets_BusinessCriticality",
        ]

        for idx_name in expected_indexes:
            assert any(
                idx_name in name for name in index_names
            ), f"索引 {idx_name} 不存在於 Assets 表"


@pytest.mark.integration
@pytest.mark.requires_db
async def test_unique_constraints():
    """測試唯一約束"""
    async with engine.begin() as conn:
        inspector = inspect(engine.sync_engine)

        # 測試 ThreatFeeds 表的唯一約束
        unique_constraints = inspector.get_unique_constraints("threat_feeds")
        constraint_names = [uc["name"] for uc in unique_constraints]

        # 驗證 name 欄位的唯一約束
        name_unique = [
            uc for uc in unique_constraints if "name" in uc["column_names"]
        ]
        assert len(name_unique) > 0, "ThreatFeeds.name 唯一約束不存在"

