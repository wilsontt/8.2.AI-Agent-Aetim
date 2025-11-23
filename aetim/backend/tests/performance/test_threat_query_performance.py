"""
威脅查詢效能測試

測試威脅查詢的效能，包含：
- 威脅查詢效能（10,000 筆資料下回應時間 ≤ 2 秒，NFR-001）
"""

import pytest
import sys
import os
import time
from datetime import datetime

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from threat_intelligence.domain.aggregates.threat import Threat
from threat_intelligence.domain.value_objects.threat_severity import ThreatSeverity
from threat_intelligence.domain.value_objects.threat_status import ThreatStatus
from threat_intelligence.infrastructure.persistence.threat_repository import ThreatRepository
from threat_intelligence.application.services.threat_service import ThreatService
from threat_intelligence.infrastructure.persistence.threat_asset_association_repository import (
    ThreatAssetAssociationRepository,
)
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
async def threat_repository(db_session):
    """建立 ThreatRepository 實例"""
    return ThreatRepository(db_session)


@pytest.fixture
async def threat_service(db_session):
    """建立 ThreatService 實例"""
    threat_repository = ThreatRepository(db_session)
    association_repository = ThreatAssetAssociationRepository(db_session)
    return ThreatService(threat_repository, association_repository)


@pytest.fixture
async def sample_threats(db_session, threat_repository):
    """建立 10,000 筆測試用威脅資料"""
    threats = []
    
    for i in range(10000):
        threat = Threat.create(
            threat_feed_id="feed-123",
            title=f"Test Threat {i}",
            description=f"Test threat description {i}",
            cve_id=f"CVE-2024-{i:05d}",
            cvss_base_score=float(1.0 + (i % 10)),
            severity=ThreatSeverity(["Critical", "High", "Medium", "Low"][i % 4]),
            source_url=f"https://example.com/threat/{i}",
            published_date=datetime(2024, 1, 1),
        )
        threats.append(threat)
        await threat_repository.save(threat)
    
    await db_session.commit()
    return threats


@pytest.mark.asyncio
class TestThreatQueryPerformance:
    """威脅查詢效能測試"""
    
    async def test_query_performance_with_large_dataset(
        self,
        threat_service,
        sample_threats,
    ):
        """
        測試大量資料下的查詢效能（NFR-001）
        
        要求：10,000 筆資料下回應時間 ≤ 2 秒
        """
        # 測量查詢時間
        start_time = time.time()
        
        result = await threat_service.get_threats(
            page=1,
            page_size=100,
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 驗證查詢成功
        assert result["total"] == 10000
        assert len(result["items"]) == 100
        
        # 驗證效能要求（≤ 2 秒）
        assert elapsed_time <= 2.0, f"查詢時間 {elapsed_time:.2f} 秒超過 2 秒限制"
        
        print(f"查詢 10,000 筆資料時間：{elapsed_time:.2f} 秒")
    
    async def test_query_with_filter_performance(
        self,
        threat_service,
        sample_threats,
    ):
        """
        測試帶篩選條件的查詢效能
        """
        # 測量帶篩選條件的查詢時間
        start_time = time.time()
        
        result = await threat_service.get_threats(
            page=1,
            page_size=100,
            min_cvss_score=7.0,
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 驗證查詢成功
        assert result["total"] > 0
        
        # 驗證效能要求（≤ 2 秒）
        assert elapsed_time <= 2.0, f"帶篩選條件的查詢時間 {elapsed_time:.2f} 秒超過 2 秒限制"
        
        print(f"帶篩選條件的查詢時間：{elapsed_time:.2f} 秒")
    
    async def test_query_with_sort_performance(
        self,
        threat_service,
        sample_threats,
    ):
        """
        測試帶排序的查詢效能
        """
        # 測量帶排序的查詢時間
        start_time = time.time()
        
        result = await threat_service.get_threats(
            page=1,
            page_size=100,
            sort_by="cvss_base_score",
            sort_order="desc",
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 驗證查詢成功
        assert result["total"] == 10000
        assert len(result["items"]) == 100
        
        # 驗證排序正確
        scores = [
            threat.cvss_base_score
            for threat in result["items"]
            if threat.cvss_base_score is not None
        ]
        assert scores == sorted(scores, reverse=True)
        
        # 驗證效能要求（≤ 2 秒）
        assert elapsed_time <= 2.0, f"帶排序的查詢時間 {elapsed_time:.2f} 秒超過 2 秒限制"
        
        print(f"帶排序的查詢時間：{elapsed_time:.2f} 秒")
    
    async def test_search_performance(
        self,
        threat_service,
        sample_threats,
    ):
        """
        測試搜尋效能
        """
        # 測量搜尋時間
        start_time = time.time()
        
        result = await threat_service.search_threats(
            query="Test",
            page=1,
            page_size=100,
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 驗證搜尋成功
        assert result["total"] > 0
        
        # 驗證效能要求（≤ 2 秒）
        assert elapsed_time <= 2.0, f"搜尋時間 {elapsed_time:.2f} 秒超過 2 秒限制"
        
        print(f"搜尋時間：{elapsed_time:.2f} 秒")
    
    async def test_pagination_performance(
        self,
        threat_service,
        sample_threats,
    ):
        """
        測試分頁查詢效能
        """
        # 測量分頁查詢時間（最後一頁）
        start_time = time.time()
        
        result = await threat_service.get_threats(
            page=100,  # 最後一頁
            page_size=100,
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 驗證查詢成功
        assert result["total"] == 10000
        assert len(result["items"]) == 100
        
        # 驗證效能要求（≤ 2 秒）
        assert elapsed_time <= 2.0, f"分頁查詢時間 {elapsed_time:.2f} 秒超過 2 秒限制"
        
        print(f"分頁查詢（最後一頁）時間：{elapsed_time:.2f} 秒")

