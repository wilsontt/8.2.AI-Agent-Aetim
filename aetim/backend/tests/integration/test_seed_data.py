"""
資料種子腳本整合測試

驗證資料種子腳本的功能。
"""

import pytest
import asyncio
from sqlalchemy import select, func
from shared_kernel.infrastructure.database import AsyncSessionLocal
from asset_management.infrastructure.persistence.models import Asset, AssetProduct
from threat_intelligence.infrastructure.persistence.models import ThreatFeed
from analysis_assessment.infrastructure.persistence.models import PIR
from system_management.infrastructure.persistence.models import User, Role, Permission


@pytest.mark.integration
@pytest.mark.requires_db
async def test_seed_data_completeness():
    """測試資料種子腳本的完整性"""
    async with AsyncSessionLocal() as session:
        # 檢查資產資料
        result = await session.execute(select(func.count(Asset.id)))
        asset_count = result.scalar()
        assert asset_count >= 100, f"資產數量不足：{asset_count} < 100"
        
        # 檢查資產產品資料
        result = await session.execute(select(func.count(AssetProduct.id)))
        product_count = result.scalar()
        assert product_count >= 200, f"資產產品數量不足：{product_count} < 200"
        
        # 檢查 PIR 資料
        result = await session.execute(select(func.count(PIR.id)))
        pir_count = result.scalar()
        assert pir_count >= 5, f"PIR 數量不足：{pir_count} < 5"
        
        # 檢查威脅來源資料
        result = await session.execute(select(func.count(ThreatFeed.id)))
        feed_count = result.scalar()
        assert feed_count >= 5, f"威脅來源數量不足：{feed_count} < 5"
        
        # 檢查使用者資料
        result = await session.execute(select(func.count(User.id)))
        user_count = result.scalar()
        assert user_count >= 3, f"使用者數量不足：{user_count} < 3"
        
        # 檢查角色資料
        result = await session.execute(select(func.count(Role.id)))
        role_count = result.scalar()
        assert role_count >= 4, f"角色數量不足：{role_count} < 4"


@pytest.mark.integration
@pytest.mark.requires_db
async def test_seed_data_boundary_cases():
    """測試資料種子腳本的邊界情況"""
    async with AsyncSessionLocal() as session:
        # 檢查是否有極長主機名稱的資產
        result = await session.execute(
            select(Asset).where(Asset.host_name.like("%" + "a" * 100 + "%"))
        )
        long_hostname_assets = result.scalars().all()
        assert len(long_hostname_assets) > 0, "未找到極長主機名稱的資產"
        
        # 檢查是否有特殊 IP 格式的資產
        result = await session.execute(
            select(Asset).where(Asset.ip.like("%/%"))
        )
        special_ip_assets = result.scalars().all()
        assert len(special_ip_assets) > 0, "未找到特殊 IP 格式的資產"


@pytest.mark.integration
@pytest.mark.requires_db
async def test_seed_data_pir_types():
    """測試 PIR 資料的類型多樣性"""
    async with AsyncSessionLocal() as session:
        # 檢查不同條件類型的 PIR
        result = await session.execute(
            select(PIR).where(PIR.condition_type == "產品名稱")
        )
        product_name_pirs = result.scalars().all()
        assert len(product_name_pirs) > 0, "未找到產品名稱條件的 PIR"
        
        result = await session.execute(
            select(PIR).where(PIR.condition_type == "CVE")
        )
        cve_pirs = result.scalars().all()
        assert len(cve_pirs) > 0, "未找到 CVE 條件的 PIR"
        
        result = await session.execute(
            select(PIR).where(PIR.condition_type == "威脅類型")
        )
        threat_type_pirs = result.scalars().all()
        assert len(threat_type_pirs) > 0, "未找到威脅類型條件的 PIR"


@pytest.mark.integration
@pytest.mark.requires_db
async def test_seed_data_threat_feed_priorities():
    """測試威脅來源資料的優先級多樣性"""
    async with AsyncSessionLocal() as session:
        # 檢查不同優先級的威脅來源
        result = await session.execute(
            select(ThreatFeed).where(ThreatFeed.priority == "P0")
        )
        p0_feeds = result.scalars().all()
        assert len(p0_feeds) > 0, "未找到 P0 優先級的威脅來源"
        
        result = await session.execute(
            select(ThreatFeed).where(ThreatFeed.priority == "P1")
        )
        p1_feeds = result.scalars().all()
        assert len(p1_feeds) > 0, "未找到 P1 優先級的威脅來源"
        
        result = await session.execute(
            select(ThreatFeed).where(ThreatFeed.priority == "P2")
        )
        p2_feeds = result.scalars().all()
        assert len(p2_feeds) > 0, "未找到 P2 優先級的威脅來源"


@pytest.mark.integration
@pytest.mark.requires_db
async def test_seed_data_user_roles():
    """測試使用者與角色的關聯"""
    async with AsyncSessionLocal() as session:
        from system_management.infrastructure.persistence.models import UserRole
        
        # 檢查使用者角色關聯
        result = await session.execute(select(func.count(UserRole.user_id)))
        user_role_count = result.scalar()
        assert user_role_count >= 3, f"使用者角色關聯數量不足：{user_role_count} < 3"
        
        # 檢查 CISO 使用者是否有 CISO 角色
        result = await session.execute(
            select(User).where(User.email == "ciso@example.com")
        )
        ciso_user = result.scalar_one_or_none()
        if ciso_user:
            result = await session.execute(
                select(UserRole).where(UserRole.user_id == ciso_user.id)
            )
            user_roles = result.scalars().all()
            assert len(user_roles) > 0, "CISO 使用者沒有角色關聯"

