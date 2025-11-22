#!/usr/bin/env python3
"""
資料種子腳本

用於開發環境初始化，建立測試資料。
"""

import asyncio
import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from shared_kernel.infrastructure.database import AsyncSessionLocal, init_db
from tests.factories import (
    AssetFactory,
    AssetProductFactory,
    ThreatFeedFactory,
    ThreatFactory,
    PIRFactory,
    UserFactory,
    RoleFactory,
    PermissionFactory,
)
from system_management.infrastructure.persistence.models import UserRole, RolePermission


async def seed_assets(session):
    """建立測試用資產資料（至少 100 筆）"""
    print("📦 建立測試用資產資料...")
    
    assets = AssetFactory.create_batch(100)
    
    # 建立不同類型的資產
    # 高優先級資產（20 筆）
    for i in range(20):
        asset = AssetFactory.create_high_priority(item=i + 1)
        assets.append(asset)
    
    # 低優先級資產（20 筆）
    for i in range(20):
        asset = AssetFactory.create_low_priority(item=i + 21)
        assets.append(asset)
    
    # 對外暴露資產（20 筆）
    for i in range(20):
        asset = AssetFactory.create_public_facing(item=i + 41)
        assets.append(asset)
    
    # 邊界情況測試
    # 極長主機名稱
    assets.append(AssetFactory.create(
        host_name="a" * 200,
        item=141
    ))
    
    # 特殊字元 IP
    assets.append(AssetFactory.create(
        ip="10.0.0.0/24",
        item=142
    ))
    
    session.add_all(assets)
    await session.commit()
    
    # 為每個資產建立產品資訊
    print("📦 建立資產產品資訊...")
    products = []
    for asset in assets:
        # 作業系統產品
        products.append(AssetProductFactory.create_os_product(
            asset_id=asset.id,
            product_name="Linux",
            product_version="5.4"
        ))
        # 應用程式產品
        products.append(AssetProductFactory.create_application_product(
            asset_id=asset.id,
            product_name="nginx",
            product_version="1.18.0"
        ))
    
    session.add_all(products)
    await session.commit()
    
    print(f"✅ 已建立 {len(assets)} 筆資產資料和 {len(products)} 筆產品資料")
    return assets


async def seed_pirs(session):
    """建立測試用 PIR 資料（5 個 PIR 項目）"""
    print("📋 建立測試用 PIR 資料...")
    
    pirs = [
        PIRFactory.create_product_name_pir(item=1),
        PIRFactory.create_cve_pir(item=2),
        PIRFactory.create_threat_type_pir(item=3),
        PIRFactory.create_cisa_kev_pir(item=4),
        PIRFactory.create_taiwan_cert_pir(item=5),
    ]
    
    session.add_all(pirs)
    await session.commit()
    
    print(f"✅ 已建立 {len(pirs)} 筆 PIR 資料")
    return pirs


async def seed_threat_feeds(session):
    """建立測試用威脅來源資料（5 個來源）"""
    print("🔗 建立測試用威脅來源資料...")
    
    feeds = [
        ThreatFeedFactory.create_cisa_kev(),
        ThreatFeedFactory.create_nvd(),
        ThreatFeedFactory.create_vmware_vmsa(),
        ThreatFeedFactory.create_msrc(),
        ThreatFeedFactory.create_twcert(),
    ]
    
    session.add_all(feeds)
    await session.commit()
    
    print(f"✅ 已建立 {len(feeds)} 筆威脅來源資料")
    return feeds


async def seed_users_and_roles(session):
    """建立測試用使用者與角色資料"""
    print("👥 建立測試用使用者與角色資料...")
    
    # 建立角色
    roles = [
        RoleFactory.create_ciso(),
        RoleFactory.create_it_admin(),
        RoleFactory.create_analyst(),
        RoleFactory.create_viewer(),
    ]
    
    session.add_all(roles)
    await session.commit()
    
    # 建立權限
    permissions = []
    resources = ["asset", "threat", "report", "pir", "threat_feed"]
    actions = ["read", "write", "delete"]
    
    for resource in resources:
        for action in actions:
            permissions.append(PermissionFactory.create(
                resource=resource,
                action=action
            ))
    
    session.add_all(permissions)
    await session.commit()
    
    # 建立角色權限關聯
    role_permissions = []
    for role in roles:
        if role.name == "CISO":
            # CISO 擁有所有權限
            for perm in permissions:
                role_permissions.append(RolePermission(
                    role_id=role.id,
                    permission_id=perm.id
                ))
        elif role.name == "IT_Admin":
            # IT 管理員擁有資產和報告的讀寫權限
            for perm in permissions:
                if perm.resource in ["asset", "report"] and perm.action in ["read", "write"]:
                    role_permissions.append(RolePermission(
                        role_id=role.id,
                        permission_id=perm.id
                    ))
        elif role.name == "Analyst":
            # 分析師擁有讀取和寫入權限（無刪除權限）
            for perm in permissions:
                if perm.action in ["read", "write"]:
                    role_permissions.append(RolePermission(
                        role_id=role.id,
                        permission_id=perm.id
                    ))
        elif role.name == "Viewer":
            # 檢視者只有讀取權限
            for perm in permissions:
                if perm.action == "read":
                    role_permissions.append(RolePermission(
                        role_id=role.id,
                        permission_id=perm.id
                    ))
    
    session.add_all(role_permissions)
    await session.commit()
    
    # 建立使用者
    users = [
        UserFactory.create_ciso(),
        UserFactory.create_it_admin(),
        UserFactory.create_analyst(),
    ]
    
    session.add_all(users)
    await session.commit()
    
    # 建立使用者角色關聯
    user_roles = []
    for user in users:
        if "ciso" in user.email:
            # CISO 使用者擁有 CISO 角色
            ciso_role = next(r for r in roles if r.name == "CISO")
            user_roles.append(UserRole(
                user_id=user.id,
                role_id=ciso_role.id
            ))
        elif "itadmin" in user.email:
            # IT 管理員擁有 IT_Admin 角色
            it_admin_role = next(r for r in roles if r.name == "IT_Admin")
            user_roles.append(UserRole(
                user_id=user.id,
                role_id=it_admin_role.id
            ))
        elif "analyst" in user.email:
            # 分析師擁有 Analyst 角色
            analyst_role = next(r for r in roles if r.name == "Analyst")
            user_roles.append(UserRole(
                user_id=user.id,
                role_id=analyst_role.id
            ))
    
    session.add_all(user_roles)
    await session.commit()
    
    print(f"✅ 已建立 {len(roles)} 個角色、{len(permissions)} 個權限、{len(users)} 個使用者")
    return users, roles


async def main():
    """主函數"""
    print("🌱 開始執行資料種子腳本...")
    
    # 初始化資料庫
    await init_db()
    
    async with AsyncSessionLocal() as session:
        # 建立資產資料
        assets = await seed_assets(session)
        
        # 建立 PIR 資料
        pirs = await seed_pirs(session)
        
        # 建立威脅來源資料
        feeds = await seed_threat_feeds(session)
        
        # 建立使用者與角色資料
        users, roles = await seed_users_and_roles(session)
        
        print("\n✅ 資料種子腳本執行完成！")
        print(f"📊 統計：")
        print(f"  - 資產：{len(assets)} 筆")
        print(f"  - PIR：{len(pirs)} 筆")
        print(f"  - 威脅來源：{len(feeds)} 筆")
        print(f"  - 使用者：{len(users)} 筆")
        print(f"  - 角色：{len(roles)} 筆")


if __name__ == "__main__":
    asyncio.run(main())

