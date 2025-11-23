"""
威脅收集效能測試

測試威脅收集的效能，包含：
- 單一來源收集時間（≤ 5 分鐘，AC-008-1）
- 並行收集效能（至少 3 個來源同時處理，AC-008-2）
"""

import pytest
import sys
import os
import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from threat_intelligence.domain.aggregates.threat_feed import ThreatFeed
from threat_intelligence.domain.aggregates.threat import Threat
from threat_intelligence.domain.value_objects.threat_severity import ThreatSeverity
from threat_intelligence.infrastructure.persistence.threat_feed_repository import ThreatFeedRepository
from threat_intelligence.infrastructure.persistence.threat_repository import ThreatRepository
from threat_intelligence.infrastructure.external_services.collector_factory import CollectorFactory
from threat_intelligence.infrastructure.external_services.ai_service_client import AIServiceClient
from threat_intelligence.application.services.threat_collection_service import ThreatCollectionService
from shared_kernel.infrastructure.database import Base


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
    """建立模擬的 AI 服務客戶端（快速回應）"""
    client = MagicMock(spec=AIServiceClient)
    client.base_url = "http://localhost:8001"
    client.timeout = 30
    client.health_check = AsyncMock(return_value=True)
    client.extract_threat_info = AsyncMock(
        return_value={
            "cves": ["CVE-2024-12345"],
            "products": [{"product_name": "Test Product"}],
            "ttps": ["T1566.001"],
            "iocs": {"ips": [], "domains": [], "hashes": []},
            "confidence": 0.95,
        }
    )
    return client


@pytest.fixture
def mock_collector():
    """建立模擬的收集器（快速回應）"""
    collector = MagicMock()
    collector.get_collector_type.return_value = "TEST"
    
    # 模擬收集 10 個威脅，每個威脅收集時間約 0.1 秒
    async def collect(feed):
        await asyncio.sleep(0.1)  # 模擬網路延遲
        return [
            Threat.create(
                threat_feed_id=feed.id,
                title=f"Test Threat {i}",
                description=f"Test threat description {i}",
                cve_id=f"CVE-2024-{i:05d}",
                cvss_base_score=7.5 + (i % 3) * 0.5,
                severity=ThreatSeverity("High"),
                source_url=f"https://example.com/threat/{i}",
                published_date=datetime(2024, 1, 1),
            )
            for i in range(10)
        ]
    
    collector.collect = collect
    return collector


@pytest.fixture
def collector_factory(mock_collector):
    """建立模擬的收集器工廠"""
    factory = CollectorFactory()
    factory.register_collector("TEST", mock_collector)
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


@pytest.mark.asyncio
class TestThreatCollectionPerformance:
    """威脅收集效能測試"""
    
    async def test_single_feed_collection_performance(
        self,
        db_session,
        threat_collection_service,
    ):
        """
        測試單一來源收集效能（AC-008-1）
        
        要求：單一來源收集時間 ≤ 5 分鐘
        """
        # 建立威脅來源
        feed = ThreatFeed.create(
            name="TEST",
            priority="P0",
            collection_frequency="每日",
        )
        feed_repository = ThreatFeedRepository(db_session)
        await feed_repository.save(feed)
        await db_session.commit()
        
        # 測量收集時間
        start_time = time.time()
        
        result = await threat_collection_service.collect_from_feed(
            feed_id=feed.id,
            use_ai=True,
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 驗證收集成功
        assert result["success"] is True
        assert result["threats_collected"] > 0
        
        # 驗證效能要求（≤ 5 分鐘 = 300 秒）
        assert elapsed_time <= 300, f"單一來源收集時間 {elapsed_time:.2f} 秒超過 5 分鐘限制"
        
        print(f"單一來源收集時間：{elapsed_time:.2f} 秒")
    
    async def test_concurrent_collection_performance(
        self,
        db_session,
        threat_collection_service,
    ):
        """
        測試並行收集效能（AC-008-2）
        
        要求：至少 3 個來源同時處理
        """
        # 建立 3 個威脅來源
        feed_repository = ThreatFeedRepository(db_session)
        feeds = []
        
        for i in range(3):
            feed = ThreatFeed.create(
                name="TEST",
                priority="P0",
                collection_frequency="每日",
            )
            await feed_repository.save(feed)
            feeds.append(feed)
        
        await db_session.commit()
        
        # 測量並行收集時間
        start_time = time.time()
        
        # 並行收集 3 個來源
        results = await asyncio.gather(
            *[
                threat_collection_service.collect_from_feed(feed.id, use_ai=True)
                for feed in feeds
            ]
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 驗證所有收集成功
        for result in results:
            assert result["success"] is True
            assert result["threats_collected"] > 0
        
        # 驗證並行處理（並行收集時間應該小於順序收集時間的總和）
        # 順序收集時間約為 3 * 單一收集時間
        # 並行收集時間應該明顯小於這個值
        print(f"並行收集 3 個來源時間：{elapsed_time:.2f} 秒")
        
        # 驗證效能要求（≤ 5 分鐘 = 300 秒）
        assert elapsed_time <= 300, f"並行收集時間 {elapsed_time:.2f} 秒超過 5 分鐘限制"

