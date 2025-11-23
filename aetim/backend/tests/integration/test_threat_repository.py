"""
威脅 Repository 整合測試

測試威脅 Repository 的功能。
"""

import pytest
import sys
import os
from datetime import datetime

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from threat_intelligence.infrastructure.persistence.threat_repository import ThreatRepository
from threat_intelligence.infrastructure.persistence.threat_asset_association_repository import (
    ThreatAssetAssociationRepository,
)
from threat_intelligence.domain.aggregates.threat import Threat
from threat_intelligence.domain.value_objects.threat_severity import ThreatSeverity
from threat_intelligence.domain.value_objects.threat_status import ThreatStatus
from threat_intelligence.domain.entities.threat_product import ThreatProduct
from shared_kernel.infrastructure.database import Base, get_db
from threat_intelligence.infrastructure.persistence.models import Threat as ThreatModel
from analysis_assessment.infrastructure.persistence.models import ThreatAssetAssociation as ThreatAssetAssociationModel


@pytest.fixture
async def db_session():
    """建立測試用的資料庫會話"""
    # 使用記憶體 SQLite 資料庫
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # 建立所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 建立會話
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def threat_repository(db_session):
    """建立 ThreatRepository 實例"""
    return ThreatRepository(db_session)


@pytest.fixture
def association_repository(db_session):
    """建立 ThreatAssetAssociationRepository 實例"""
    return ThreatAssetAssociationRepository(db_session)


@pytest.fixture
def sample_threat():
    """建立測試用的威脅"""
    return Threat.create(
        threat_feed_id="feed-123",
        title="Test Threat",
        description="This is a test threat",
        cve_id="CVE-2024-12345",
        cvss_base_score=9.8,
        cvss_vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
        severity=ThreatSeverity("Critical"),
        source_url="https://example.com/threat",
        published_date=datetime(2024, 1, 1),
    )


@pytest.mark.asyncio
class TestThreatRepository:
    """威脅 Repository 測試"""
    
    async def test_save_new_threat(self, threat_repository, sample_threat):
        """測試儲存新威脅"""
        await threat_repository.save(sample_threat)
        
        # 驗證已儲存
        retrieved = await threat_repository.get_by_id(sample_threat.id)
        assert retrieved is not None
        assert retrieved.id == sample_threat.id
        assert retrieved.title == sample_threat.title
        assert retrieved.cve_id == sample_threat.cve_id
    
    async def test_save_update_threat(self, threat_repository, sample_threat):
        """測試更新威脅"""
        # 先儲存
        await threat_repository.save(sample_threat)
        
        # 更新
        sample_threat.title = "Updated Threat Title"
        sample_threat.update_status("Analyzing")
        await threat_repository.save(sample_threat)
        
        # 驗證已更新
        retrieved = await threat_repository.get_by_id(sample_threat.id)
        assert retrieved.title == "Updated Threat Title"
        assert retrieved.status.value == "Analyzing"
    
    async def test_get_by_id(self, threat_repository, sample_threat):
        """測試根據 ID 取得威脅"""
        await threat_repository.save(sample_threat)
        
        retrieved = await threat_repository.get_by_id(sample_threat.id)
        assert retrieved is not None
        assert retrieved.id == sample_threat.id
    
    async def test_get_by_id_not_found(self, threat_repository):
        """測試取得不存在的威脅"""
        retrieved = await threat_repository.get_by_id("non-existent-id")
        assert retrieved is None
    
    async def test_get_by_cve(self, threat_repository, sample_threat):
        """測試根據 CVE 取得威脅"""
        await threat_repository.save(sample_threat)
        
        retrieved = await threat_repository.get_by_cve("CVE-2024-12345")
        assert retrieved is not None
        assert retrieved.cve_id == "CVE-2024-12345"
    
    async def test_get_by_cve_not_found(self, threat_repository):
        """測試取得不存在的 CVE"""
        retrieved = await threat_repository.get_by_cve("CVE-9999-99999")
        assert retrieved is None
    
    async def test_exists_by_cve(self, threat_repository, sample_threat):
        """測試檢查 CVE 是否存在"""
        await threat_repository.save(sample_threat)
        
        assert await threat_repository.exists_by_cve("CVE-2024-12345") is True
        assert await threat_repository.exists_by_cve("CVE-9999-99999") is False
    
    async def test_delete(self, threat_repository, sample_threat):
        """測試刪除威脅"""
        await threat_repository.save(sample_threat)
        
        await threat_repository.delete(sample_threat.id)
        
        retrieved = await threat_repository.get_by_id(sample_threat.id)
        assert retrieved is None
    
    async def test_get_all_with_pagination(self, threat_repository):
        """測試分頁查詢"""
        # 建立多個威脅
        for i in range(10):
            threat = Threat.create(
                threat_feed_id="feed-123",
                title=f"Threat {i}",
                cve_id=f"CVE-2024-{i:05d}",
            )
            await threat_repository.save(threat)
        
        # 測試分頁
        threats = await threat_repository.get_all(skip=0, limit=5)
        assert len(threats) == 5
        
        threats = await threat_repository.get_all(skip=5, limit=5)
        assert len(threats) == 5
    
    async def test_get_all_with_status_filter(self, threat_repository):
        """測試狀態篩選"""
        # 建立不同狀態的威脅
        threat1 = Threat.create(
            threat_feed_id="feed-123",
            title="New Threat",
            cve_id="CVE-2024-00001",
        )
        threat1.status = ThreatStatus("New")
        await threat_repository.save(threat1)
        
        threat2 = Threat.create(
            threat_feed_id="feed-123",
            title="Processed Threat",
            cve_id="CVE-2024-00002",
        )
        threat2.update_status("Processed")
        await threat_repository.save(threat2)
        
        # 測試篩選
        new_threats = await threat_repository.get_all(status="New")
        assert len(new_threats) >= 1
        assert all(t.status.value == "New" for t in new_threats)
    
    async def test_get_all_with_cvss_filter(self, threat_repository):
        """測試 CVSS 分數篩選"""
        # 建立不同 CVSS 分數的威脅
        threat1 = Threat.create(
            threat_feed_id="feed-123",
            title="High CVSS Threat",
            cve_id="CVE-2024-00001",
            cvss_base_score=9.8,
        )
        await threat_repository.save(threat1)
        
        threat2 = Threat.create(
            threat_feed_id="feed-123",
            title="Low CVSS Threat",
            cve_id="CVE-2024-00002",
            cvss_base_score=3.5,
        )
        await threat_repository.save(threat2)
        
        # 測試篩選
        high_threats = await threat_repository.get_all(min_cvss_score=7.0)
        assert len(high_threats) >= 1
        assert all(t.cvss_base_score >= 7.0 for t in high_threats if t.cvss_base_score)
    
    async def test_get_all_with_sorting(self, threat_repository):
        """測試排序"""
        # 建立多個威脅
        for i in range(5):
            threat = Threat.create(
                threat_feed_id="feed-123",
                title=f"Threat {i}",
                cve_id=f"CVE-2024-{i:05d}",
                cvss_base_score=float(10 - i),
            )
            await threat_repository.save(threat)
        
        # 測試按 CVSS 分數降序排序
        threats = await threat_repository.get_all(
            sort_by="cvss_base_score",
            sort_order="desc",
        )
        assert len(threats) >= 5
        scores = [t.cvss_base_score for t in threats if t.cvss_base_score]
        assert scores == sorted(scores, reverse=True)
    
    async def test_search(self, threat_repository):
        """測試搜尋"""
        # 建立威脅
        threat1 = Threat.create(
            threat_feed_id="feed-123",
            title="Windows Server Vulnerability",
            description="A critical vulnerability in Windows Server",
            cve_id="CVE-2024-00001",
        )
        await threat_repository.save(threat1)
        
        threat2 = Threat.create(
            threat_feed_id="feed-123",
            title="Linux Kernel Issue",
            description="A security issue in Linux kernel",
            cve_id="CVE-2024-00002",
        )
        await threat_repository.save(threat2)
        
        # 測試搜尋
        results = await threat_repository.search("Windows")
        assert len(results) >= 1
        assert any("Windows" in t.title for t in results)


@pytest.mark.asyncio
class TestThreatAssetAssociationRepository:
    """威脅資產關聯 Repository 測試"""
    
    async def test_save_association(self, association_repository):
        """測試儲存關聯"""
        await association_repository.save_association(
            threat_id="threat-123",
            asset_id="asset-456",
            match_confidence=0.95,
            match_type="Exact",
            match_details='{"reason": "Exact product match"}',
        )
        
        # 驗證已儲存
        associations = await association_repository.get_by_threat_id("threat-123")
        assert len(associations) == 1
        assert associations[0].asset_id == "asset-456"
        assert associations[0].match_confidence == 0.95
    
    async def test_get_by_threat_id(self, association_repository):
        """測試根據威脅 ID 查詢關聯"""
        # 建立多個關聯
        await association_repository.save_association(
            threat_id="threat-123",
            asset_id="asset-1",
            match_confidence=0.9,
            match_type="Exact",
        )
        await association_repository.save_association(
            threat_id="threat-123",
            asset_id="asset-2",
            match_confidence=0.8,
            match_type="Fuzzy",
        )
        
        associations = await association_repository.get_by_threat_id("threat-123")
        assert len(associations) == 2
    
    async def test_get_by_asset_id(self, association_repository):
        """測試根據資產 ID 查詢關聯"""
        # 建立多個關聯
        await association_repository.save_association(
            threat_id="threat-1",
            asset_id="asset-123",
            match_confidence=0.9,
            match_type="Exact",
        )
        await association_repository.save_association(
            threat_id="threat-2",
            asset_id="asset-123",
            match_confidence=0.8,
            match_type="Fuzzy",
        )
        
        associations = await association_repository.get_by_asset_id("asset-123")
        assert len(associations) == 2
    
    async def test_delete_association(self, association_repository):
        """測試刪除關聯"""
        # 建立關聯
        await association_repository.save_association(
            threat_id="threat-123",
            asset_id="asset-456",
            match_confidence=0.9,
            match_type="Exact",
        )
        
        # 刪除關聯
        await association_repository.delete_association("threat-123", "asset-456")
        
        # 驗證已刪除
        associations = await association_repository.get_by_threat_id("threat-123")
        assert len(associations) == 0

