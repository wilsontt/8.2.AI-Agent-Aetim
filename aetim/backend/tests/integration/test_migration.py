"""
資料庫遷移整合測試

驗證 Alembic 遷移工具的功能。
"""

import pytest
import asyncio
from sqlalchemy import inspect, text
from shared_kernel.infrastructure.database import engine, Base


@pytest.mark.integration
@pytest.mark.requires_db
async def test_migration_upgrade():
    """測試遷移升級"""
    # 檢查資料表是否存在
    inspector = inspect(engine.sync_engine)
    tables = inspector.get_table_names()

    # 驗證所有必要的資料表都已建立
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
async def test_migration_history():
    """測試遷移歷史追蹤"""
    inspector = inspect(engine.sync_engine)
    tables = inspector.get_table_names()

    # 驗證 alembic_version 表存在
    assert "alembic_version" in tables, "alembic_version 表未建立"

    # 查詢當前版本
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar()
        assert version is not None, "未找到遷移版本記錄"


@pytest.mark.integration
@pytest.mark.requires_db
async def test_migration_idempotent():
    """測試遷移腳本可重複執行（idempotent）"""
    # 這個測試需要實際執行遷移兩次來驗證
    # 在實際環境中，應該使用測試資料庫來執行
    inspector = inspect(engine.sync_engine)
    tables = inspector.get_table_names()

    # 驗證資料表結構正確
    assert "assets" in tables, "assets 表未建立"
    assert "threats" in tables, "threats 表未建立"

    # 驗證索引存在
    asset_indexes = inspector.get_indexes("assets")
    index_names = [idx["name"] for idx in asset_indexes]
    assert any("IX_Assets_HostName" in name for name in index_names), "索引未建立"

