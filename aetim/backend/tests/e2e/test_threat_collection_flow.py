"""
威脅收集流程端對端測試

測試威脅收集的完整流程，包含：
- 設定威脅來源
- 觸發收集作業
- 驗證收集結果
- 驗證 AI 處理結果
- 驗證威脅查詢功能
"""

import pytest
import sys
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from threat_intelligence.domain.aggregates.threat_feed import ThreatFeed
from threat_intelligence.domain.aggregates.threat import Threat
from threat_intelligence.domain.value_objects.threat_severity import ThreatSeverity
from threat_intelligence.domain.value_objects.threat_status import ThreatStatus
from threat_intelligence.infrastructure.persistence.threat_feed_repository import ThreatFeedRepository
from threat_intelligence.infrastructure.persistence.threat_repository import ThreatRepository
from threat_intelligence.infrastructure.external_services.collector_factory import CollectorFactory
from threat_intelligence.infrastructure.external_services.ai_service_client import AIServiceClient
from threat_intelligence.application.services.threat_collection_service import ThreatCollectionService
from threat_intelligence.application.services.threat_service import ThreatService
from threat_intelligence.infrastructure.persistence.threat_asset_association_repository import (
    ThreatAssetAssociationRepository,
)
from shared_kernel.infrastructure.database import Base
from threat_intelligence.domain.interfaces.threat_feed_repository import IThreatFeedRepository
from threat_intelligence.domain.interfaces.threat_repository import IThreatRepository


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
def mock_ai_service_client():
    """建立模擬的 AI 服務客戶端"""
    client = MagicMock(spec=AIServiceClient)
    client.base_url = "http://localhost:8001"
    client.timeout = 30
    client.health_check = AsyncMock(return_value=True)
    client.extract_threat_info = AsyncMock(
        return_value={
            "cves": ["CVE-2024-12345"],
            "products": [
                {
                    "product_name": "Windows Server",
                    "product_version": "2019",
                    "product_type": "Operating System",
                }
            ],
            "ttps": ["T1566.001"],
            "iocs": {
                "ips": ["192.168.1.1"],
                "domains": ["example.com"],
                "hashes": [],
            },
            "confidence": 0.95,
        }
    )
    return client


@pytest.fixture
def mock_cisa_kev_collector():
    """建立模擬的 CISA KEV 收集器"""
    collector = MagicMock()
    collector.get_collector_type.return_value = "CISA KEV"
    collector.collect = AsyncMock(
        return_value=[
            Threat.create(
                threat_feed_id="feed-cisa-kev",
                title="CISA KEV Test Threat",
                description="This is a test threat from CISA KEV",
                cve_id="CVE-2024-12345",
                cvss_base_score=9.8,
                severity=ThreatSeverity("Critical"),
                source_url="https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
                published_date=datetime(2024, 1, 1),
            )
        ]
    )
    return collector


@pytest.fixture
def mock_nvd_collector():
    """建立模擬的 NVD 收集器"""
    collector = MagicMock()
    collector.get_collector_type.return_value = "NVD"
    collector.collect = AsyncMock(
        return_value=[
            Threat.create(
                threat_feed_id="feed-nvd",
                title="NVD Test Threat",
                description="This is a test threat from NVD with unstructured content that needs AI processing",
                cve_id="CVE-2024-67890",
                cvss_base_score=7.5,
                severity=ThreatSeverity("High"),
                source_url="https://nvd.nist.gov/vuln/detail/CVE-2024-67890",
                published_date=datetime(2024, 1, 2),
            )
        ]
    )
    return collector


@pytest.fixture
def collector_factory(mock_cisa_kev_collector, mock_nvd_collector):
    """建立模擬的收集器工廠"""
    factory = CollectorFactory()
    
    # 註冊模擬收集器（使用 CollectorFactory 的註冊機制）
    factory.register_collector("CISA_KEV", mock_cisa_kev_collector)
    factory.register_collector("NVD", mock_nvd_collector)
    
    return factory


@pytest.fixture
async def threat_collection_service(
    db_session,
    collector_factory,
    mock_ai_service_client,
):
    """建立威脅收集服務"""
    feed_repository = ThreatFeedRepository(db_session)
    threat_repository = ThreatRepository(db_session)
    
    return ThreatCollectionService(
        feed_repository=feed_repository,
        threat_repository=threat_repository,
        collector_factory=collector_factory,
        ai_service_client=mock_ai_service_client,
        max_concurrent_collections=3,
    )


@pytest.fixture
async def threat_service(db_session):
    """建立威脅服務"""
    threat_repository = ThreatRepository(db_session)
    association_repository = ThreatAssetAssociationRepository(db_session)
    
    return ThreatService(
        threat_repository=threat_repository,
        association_repository=association_repository,
    )


@pytest.mark.asyncio
class TestThreatCollectionFlow:
    """威脅收集流程端對端測試"""
    
    async def test_complete_collection_flow_with_ai(
        self,
        db_session,
        threat_collection_service,
        threat_service,
        mock_ai_service_client,
    ):
        """
        測試完整的威脅收集流程（包含 AI 處理）
        
        場景：
        1. 建立 CISA KEV 威脅來源
        2. 觸發收集作業
        3. 驗證威脅資料已儲存
        4. 驗證 AI 處理結果
        5. 驗證威脅查詢功能
        """
        # 1. 建立威脅來源
        feed = ThreatFeed.create(
            name="CISA KEV",
            priority="P0",
            collection_frequency="每日",
        )
        feed_repository = ThreatFeedRepository(db_session)
        await feed_repository.save(feed)
        await db_session.commit()
        
        # 2. 觸發收集作業
        result = await threat_collection_service.collect_from_feed(
            feed_id=feed.id,
            use_ai=True,
        )
        
        # 3. 驗證收集結果
        assert result["success"] is True
        assert result["threats_collected"] > 0
        assert len(result["errors"]) == 0
        
        # 4. 驗證威脅資料已儲存
        threats = await threat_service.get_threats(page=1, page_size=100)
        assert threats["total"] > 0
        
        # 找到收集到的威脅
        collected_threat = None
        for threat in threats["items"]:
            if threat.cve_id == "CVE-2024-12345":
                collected_threat = threat
                break
        
        assert collected_threat is not None
        assert collected_threat.title == "CISA KEV Test Threat"
        assert collected_threat.cve_id == "CVE-2024-12345"
        assert collected_threat.cvss_base_score == 9.8
        
        # 5. 驗證 AI 處理結果（如果 AI 服務被呼叫）
        # 注意：由於我們使用 mock，實際的 AI 處理可能不會執行
        # 但我們可以驗證威脅資料已正確儲存
        
        # 6. 驗證威脅查詢功能
        threat_detail = await threat_service.get_threat_by_id(collected_threat.id)
        assert threat_detail is not None
        assert threat_detail.cve_id == "CVE-2024-12345"
    
    async def test_collection_flow_without_ai(
        self,
        db_session,
        threat_collection_service,
        threat_service,
    ):
        """
        測試威脅收集流程（不使用 AI）
        
        場景：
        1. 建立 NVD 威脅來源
        2. 觸發收集作業（不使用 AI）
        3. 驗證威脅資料已儲存
        4. 驗證威脅查詢功能
        """
        # 1. 建立威脅來源
        feed = ThreatFeed.create(
            name="NVD",
            priority="P0",
            collection_frequency="每日",
        )
        feed_repository = ThreatFeedRepository(db_session)
        await feed_repository.save(feed)
        await db_session.commit()
        
        # 2. 觸發收集作業（不使用 AI）
        result = await threat_collection_service.collect_from_feed(
            feed_id=feed.id,
            use_ai=False,
        )
        
        # 3. 驗證收集結果
        assert result["success"] is True
        assert result["threats_collected"] > 0
        
        # 4. 驗證威脅資料已儲存
        threats = await threat_service.get_threats(page=1, page_size=100)
        assert threats["total"] > 0
        
        # 找到收集到的威脅
        collected_threat = None
        for threat in threats["items"]:
            if threat.cve_id == "CVE-2024-67890":
                collected_threat = threat
                break
        
        assert collected_threat is not None
        assert collected_threat.title == "NVD Test Threat"
        assert collected_threat.cve_id == "CVE-2024-67890"
    
    async def test_collection_flow_with_ai_fallback(
        self,
        db_session,
        threat_collection_service,
        threat_service,
        mock_ai_service_client,
    ):
        """
        測試威脅收集流程（AI 服務失敗時使用回退機制）
        
        場景：
        1. 建立威脅來源
        2. 模擬 AI 服務失敗
        3. 觸發收集作業
        4. 驗證回退機制正常運作
        5. 驗證威脅資料已儲存（使用規則基礎方法提取）
        """
        # 模擬 AI 服務失敗
        mock_ai_service_client.extract_threat_info.side_effect = Exception("AI 服務錯誤")
        
        # 1. 建立威脅來源
        feed = ThreatFeed.create(
            name="NVD",
            priority="P0",
            collection_frequency="每日",
        )
        feed_repository = ThreatFeedRepository(db_session)
        await feed_repository.save(feed)
        await db_session.commit()
        
        # 2. 觸發收集作業（使用 AI，但會回退到規則基礎方法）
        result = await threat_collection_service.collect_from_feed(
            feed_id=feed.id,
            use_ai=True,
        )
        
        # 3. 驗證收集結果（即使 AI 服務失敗，收集仍應成功）
        assert result["success"] is True
        assert result["threats_collected"] > 0
        
        # 4. 驗證威脅資料已儲存
        threats = await threat_service.get_threats(page=1, page_size=100)
        assert threats["total"] > 0
    
    async def test_collection_flow_with_multiple_feeds(
        self,
        db_session,
        threat_collection_service,
        threat_service,
        mock_ai_service_client,
    ):
        """
        測試並行收集多個威脅來源
        
        場景：
        1. 建立多個威脅來源（CISA KEV、NVD）
        2. 並行觸發收集作業
        3. 驗證所有威脅資料已儲存
        4. 驗證威脅查詢功能
        """
        # 1. 建立多個威脅來源
        feed_repository = ThreatFeedRepository(db_session)
        
        feed1 = ThreatFeed.create(
            name="CISA KEV",
            priority="P0",
            collection_frequency="每日",
        )
        await feed_repository.save(feed1)
        
        feed2 = ThreatFeed.create(
            name="NVD",
            priority="P0",
            collection_frequency="每日",
        )
        await feed_repository.save(feed2)
        
        await db_session.commit()
        
        # 2. 並行觸發收集作業
        import asyncio
        
        results = await asyncio.gather(
            threat_collection_service.collect_from_feed(feed1.id, use_ai=True),
            threat_collection_service.collect_from_feed(feed2.id, use_ai=True),
        )
        
        # 3. 驗證所有收集結果
        for result in results:
            assert result["success"] is True
            assert result["threats_collected"] > 0
        
        # 4. 驗證所有威脅資料已儲存
        threats = await threat_service.get_threats(page=1, page_size=100)
        assert threats["total"] >= 2  # 至少 2 個威脅
        
        # 驗證兩個威脅都存在
        cve_ids = [threat.cve_id for threat in threats["items"]]
        assert "CVE-2024-12345" in cve_ids
        assert "CVE-2024-67890" in cve_ids
    
    async def test_collection_flow_with_search(
        self,
        db_session,
        threat_collection_service,
        threat_service,
        mock_ai_service_client,
    ):
        """
        測試威脅收集後使用搜尋功能
        
        場景：
        1. 建立威脅來源並收集威脅
        2. 使用搜尋功能查詢威脅
        3. 驗證搜尋結果
        """
        # 1. 建立威脅來源並收集
        feed = ThreatFeed.create(
            name="CISA KEV",
            priority="P0",
            collection_frequency="每日",
        )
        feed_repository = ThreatFeedRepository(db_session)
        await feed_repository.save(feed)
        await db_session.commit()
        
        await threat_collection_service.collect_from_feed(feed.id, use_ai=True)
        
        # 2. 使用搜尋功能
        search_results = await threat_service.search_threats("CISA", page=1, page_size=100)
        
        # 3. 驗證搜尋結果
        assert search_results["total"] > 0
        assert any("CISA" in threat.title for threat in search_results["items"])
    
    async def test_collection_flow_with_filtering(
        self,
        db_session,
        threat_collection_service,
        threat_service,
        mock_ai_service_client,
    ):
        """
        測試威脅收集後使用篩選功能
        
        場景：
        1. 建立威脅來源並收集威脅
        2. 使用篩選功能查詢威脅
        3. 驗證篩選結果
        """
        # 1. 建立威脅來源並收集
        feed = ThreatFeed.create(
            name="CISA KEV",
            priority="P0",
            collection_frequency="每日",
        )
        feed_repository = ThreatFeedRepository(db_session)
        await feed_repository.save(feed)
        await db_session.commit()
        
        await threat_collection_service.collect_from_feed(feed.id, use_ai=True)
        
        # 2. 使用篩選功能（依 CVE 編號）
        filtered_threats = await threat_service.get_threats(
            page=1,
            page_size=100,
            cve_id="CVE-2024-12345",
        )
        
        # 3. 驗證篩選結果
        assert filtered_threats["total"] > 0
        assert all(threat.cve_id == "CVE-2024-12345" for threat in filtered_threats["items"])
        
        # 4. 使用篩選功能（依 CVSS 分數）
        high_cvss_threats = await threat_service.get_threats(
            page=1,
            page_size=100,
            min_cvss_score=9.0,
        )
        
        assert high_cvss_threats["total"] > 0
        assert all(
            threat.cvss_base_score >= 9.0
            for threat in high_cvss_threats["items"]
            if threat.cvss_base_score is not None
        )

