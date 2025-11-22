#!/usr/bin/env python3
"""
資料庫遷移測試腳本

驗證 Alembic 遷移工具的功能。
"""

import asyncio
import os
import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect, text
from shared_kernel.infrastructure.database import engine, Base


async def test_migration():
    """測試資料庫遷移"""
    print("🔍 開始測試資料庫遷移...")

    # 檢查資料表
    print("\n📊 檢查資料表...")
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

    print(f"\n預期資料表數量: {len(expected_tables)}")
    print(f"實際資料表數量: {len(tables)}")

    missing_tables = []
    for table in expected_tables:
        if table in tables:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} (缺失)")
            missing_tables.append(table)

    if missing_tables:
        print(f"\n❌ 缺失 {len(missing_tables)} 個資料表")
        return False

    print(f"\n✅ 所有 {len(expected_tables)} 個資料表都已建立")

    # 檢查 alembic_version 表（遷移歷史追蹤）
    print("\n📜 檢查遷移歷史追蹤...")
    if "alembic_version" in tables:
        print("  ✅ alembic_version 表存在")
        
        # 查詢當前版本
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            version = result.scalar()
            if version:
                print(f"  ✅ 當前遷移版本: {version}")
            else:
                print("  ⚠️  未找到遷移版本記錄")
    else:
        print("  ⚠️  alembic_version 表不存在（可能尚未執行遷移）")

    print("\n✅ 資料庫遷移測試完成")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_migration())
    exit(0 if success else 1)

