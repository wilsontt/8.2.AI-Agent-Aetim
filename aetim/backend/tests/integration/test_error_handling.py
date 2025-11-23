"""
錯誤處理整合測試

測試錯誤處理機制在實際場景中的運作。
"""

import pytest
import sys
import os
import httpx
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from threat_intelligence.domain.aggregates.threat_feed import ThreatFeed
from threat_intelligence.infrastructure.persistence.threat_feed_repository import ThreatFeedRepository
from threat_intelligence.infrastructure.persistence.threat_repository import ThreatRepository
from threat_intelligence.infrastructure.external_services.collector_factory import CollectorFactory
from threat_intelligence.infrastructure.external_services.ai_service_client import AIServiceClient
from threat_intelligence.application.services.threat_collection_service import ThreatCollectionService
from threat_intelligence.infrastructure.external_services.error_handler import ErrorType
from shared_kernel.infrastructure.database import Base


@pytest.fixture
async def db_session():
    """建立測試用的資料庫會話"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
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
            "products": [{"product_name": "Test Product"}],
            "ttps": ["T1566.001"],
            "iocs": {"ips": [], "domains": [], "hashes": []},
            "confidence": 0.95,
        }
    )
    return client


@pytest.mark.asyncio
class TestErrorHandling:
    """錯誤處理整合測試"""
    
    async def test_rate_limit_error_handling(
        self,
        db_session,
        mock_ai_service_client,
    ):
        """測試速率限制錯誤處理（AC-008-3）"""
        # 建立模擬收集器，模擬 HTTP 429 錯誤
        collector = MagicMock()
        collector.get_collector_type.return_value = "TEST"
        
        # 第一次呼叫返回 429，第二次成功
        response_429 = httpx.Response(429, headers={"Retry-After": "1"})
        error_429 = httpx.HTTPStatusError("Rate limit exceeded", request=None, response=response_429)
        
        collector.collect = AsyncMock(side_effect=[error_429, []])
        
        # 建立收集器工廠
        factory = CollectorFactory()
        factory.register_collector("TEST", collector)
        
        # 建立威脅收集服務
        feed_repository = ThreatFeedRepository(db_session)
        threat_repository = ThreatRepository(db_session)
        service = ThreatCollectionService(
            feed_repository=feed_repository,
            threat_repository=threat_repository,
            collector_factory=factory,
            ai_service_client=mock_ai_service_client,
        )
        
        # 建立威脅來源
        feed = ThreatFeed.create(
            name="TEST",
            priority="P0",
            collection_frequency="每日",
        )
        await feed_repository.save(feed)
        await db_session.commit()
        
        # 執行收集（應該重試並成功）
        result = await service.collect_from_feed(feed.id, use_ai=False)
        
        # 驗證重試機制運作
        assert collector.collect.call_count == 2  # 第一次失敗，第二次成功
    
    async def test_network_error_retry(
        self,
        db_session,
        mock_ai_service_client,
    ):
        """測試網路錯誤重試（AC-008-3）"""
        # 建立模擬收集器，模擬網路錯誤
        collector = MagicMock()
        collector.get_collector_type.return_value = "TEST"
        
        # 第一次呼叫返回網路錯誤，第二次成功
        error_network = httpx.NetworkError("Connection failed")
        collector.collect = AsyncMock(side_effect=[error_network, []])
        
        # 建立收集器工廠
        factory = CollectorFactory()
        factory.register_collector("TEST", collector)
        
        # 建立威脅收集服務
        feed_repository = ThreatFeedRepository(db_session)
        threat_repository = ThreatRepository(db_session)
        service = ThreatCollectionService(
            feed_repository=feed_repository,
            threat_repository=threat_repository,
            collector_factory=factory,
            ai_service_client=mock_ai_service_client,
        )
        
        # 建立威脅來源
        feed = ThreatFeed.create(
            name="TEST",
            priority="P0",
            collection_frequency="每日",
        )
        await feed_repository.save(feed)
        await db_session.commit()
        
        # 執行收集（應該重試並成功）
        result = await service.collect_from_feed(feed.id, use_ai=False)
        
        # 驗證重試機制運作
        assert collector.collect.call_count == 2  # 第一次失敗，第二次成功
    
    async def test_consecutive_failure_alert(
        self,
        db_session,
        mock_ai_service_client,
    ):
        """測試連續失敗告警（AC-008-4）"""
        # 建立模擬收集器，總是失敗
        collector = MagicMock()
        collector.get_collector_type.return_value = "TEST"
        collector.collect = AsyncMock(side_effect=httpx.NetworkError("Connection failed"))
        
        # 建立收集器工廠
        factory = CollectorFactory()
        factory.register_collector("TEST", collector)
        
        # 建立威脅收集服務
        feed_repository = ThreatFeedRepository(db_session)
        threat_repository = ThreatRepository(db_session)
        service = ThreatCollectionService(
            feed_repository=feed_repository,
            threat_repository=threat_repository,
            collector_factory=factory,
            ai_service_client=mock_ai_service_client,
        )
        
        # 建立威脅來源
        feed = ThreatFeed.create(
            name="TEST",
            priority="P0",
            collection_frequency="每日",
        )
        await feed_repository.save(feed)
        await db_session.commit()
        
        # 執行 3 次收集（應該觸發告警）
        for i in range(3):
            await service.collect_from_feed(feed.id, use_ai=False)
        
        # 驗證失敗記錄
        failure_record = service.failure_tracker.get_failure_record(feed.id)
        assert failure_record is not None
        assert failure_record.failure_count >= 3
        assert failure_record.alert_sent is True
    
    async def test_error_logging(
        self,
        db_session,
        mock_ai_service_client,
    ):
        """測試錯誤日誌記錄（AC-008-4）"""
        # 建立模擬收集器，總是失敗
        collector = MagicMock()
        collector.get_collector_type.return_value = "TEST"
        collector.collect = AsyncMock(side_effect=httpx.NetworkError("Connection failed"))
        
        # 建立收集器工廠
        factory = CollectorFactory()
        factory.register_collector("TEST", collector)
        
        # 建立威脅收集服務
        feed_repository = ThreatFeedRepository(db_session)
        threat_repository = ThreatRepository(db_session)
        service = ThreatCollectionService(
            feed_repository=feed_repository,
            threat_repository=threat_repository,
            collector_factory=factory,
            ai_service_client=mock_ai_service_client,
        )
        
        # 建立威脅來源
        feed = ThreatFeed.create(
            name="TEST",
            priority="P0",
            collection_frequency="每日",
        )
        await feed_repository.save(feed)
        await db_session.commit()
        
        # 執行收集（應該記錄錯誤）
        result = await service.collect_from_feed(feed.id, use_ai=False)
        
        # 驗證錯誤被記錄
        assert result["success"] is False
        assert len(result["errors"]) > 0
        
        # 驗證失敗記錄
        failure_record = service.failure_tracker.get_failure_record(feed.id)
        assert failure_record is not None
        assert failure_record.failure_count == 1
        assert failure_record.last_error_type == ErrorType.NETWORK_ERROR.value

