#!/usr/bin/env python3
"""
資料庫 Schema 測試腳本

驗證所有資料表是否正確建立。
"""

import asyncio
from sqlalchemy import inspect, text
from shared_kernel.infrastructure.database import engine, init_db


async def test_schema():
    """測試資料庫 Schema"""
    print("🔍 開始測試資料庫 Schema...")

    # 初始化資料庫
    print("\n📦 初始化資料庫...")
    await init_db()
    print("✅ 資料庫初始化完成")

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

    # 檢查索引
    print("\n🔍 檢查索引...")
    asset_indexes = inspector.get_indexes("assets")
    print(f"Assets 表索引數量: {len(asset_indexes)}")
    for idx in asset_indexes:
        print(f"  - {idx['name']}: {idx['column_names']}")

    # 檢查外鍵
    print("\n🔗 檢查外鍵...")
    asset_products_fks = inspector.get_foreign_keys("asset_products")
    print(f"AssetProducts 表外鍵數量: {len(asset_products_fks)}")
    for fk in asset_products_fks:
        print(f"  - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

    print("\n✅ 資料庫 Schema 測試完成")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_schema())
    exit(0 if success else 1)

