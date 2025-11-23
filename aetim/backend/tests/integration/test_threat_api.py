"""
威脅 API 整合測試

測試威脅 API 端點的功能。
"""

import pytest
import sys
import os
from datetime import datetime

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from shared_kernel.infrastructure.database import Base, get_db
from threat_intelligence.infrastructure.persistence.models import Threat as ThreatModel
from threat_intelligence.domain.aggregates.threat_feed import ThreatFeed
from threat_intelligence.domain.aggregates.threat import Threat
from threat_intelligence.domain.value_objects.threat_severity import ThreatSeverity
from threat_intelligence.domain.value_objects.threat_status import ThreatStatus


@pytest.fixture
def db_session():
    """建立測試用的資料庫會話"""
    # 使用記憶體 SQLite 資料庫
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # 建立所有表
    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    import asyncio
    asyncio.run(init_db())
    
    # 建立會話
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    # 覆寫 get_db 依賴
    async def override_get_db():
        async with async_session() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield async_session
    
    # 清理
    app.dependency_overrides.clear()
    async def cleanup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()
    
    asyncio.run(cleanup())


@pytest.fixture
def client(db_session):
    """建立測試客戶端"""
    return TestClient(app)


@pytest.fixture
def sample_threat_feed(db_session):
    """建立測試用的威脅情資來源"""
    feed = ThreatFeed.create(
        name="Test Feed",
        priority="P0",
        collection_frequency="每日",
    )
    return feed


@pytest.fixture
async def sample_threat(db_session, sample_threat_feed):
    """建立測試用的威脅"""
    from threat_intelligence.infrastructure.persistence.threat_repository import ThreatRepository
    
    threat = Threat.create(
        threat_feed_id=sample_threat_feed.id,
        title="Test Threat",
        description="This is a test threat",
        cve_id="CVE-2024-12345",
        cvss_base_score=9.8,
        severity=ThreatSeverity("Critical"),
    )
    
    # 儲存到資料庫
    async with db_session() as session:
        repository = ThreatRepository(session)
        await repository.save(threat)
        await session.commit()
    
    return threat


@pytest.mark.asyncio
class TestThreatAPI:
    """威脅 API 測試"""
    
    def test_get_threats_empty(self, client):
        """測試查詢空威脅清單"""
        response = client.get("/api/v1/threats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["items"]) == 0
    
    def test_get_threats_with_pagination(self, client, sample_threat):
        """測試分頁查詢"""
        response = client.get("/api/v1/threats?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
    
    def test_get_threats_with_status_filter(self, client, sample_threat):
        """測試狀態篩選"""
        response = client.get("/api/v1/threats?status=New")
        assert response.status_code == 200
        data = response.json()
        if data["total"] > 0:
            assert all(item["status"] == "New" for item in data["items"])
    
    def test_get_threats_with_cve_filter(self, client, sample_threat):
        """測試 CVE 篩選"""
        response = client.get("/api/v1/threats?cve_id=CVE-2024-12345")
        assert response.status_code == 200
        data = response.json()
        if data["total"] > 0:
            assert any(item["cve_id"] == "CVE-2024-12345" for item in data["items"])
    
    def test_get_threats_with_cvss_filter(self, client, sample_threat):
        """測試 CVSS 分數篩選"""
        response = client.get("/api/v1/threats?min_cvss_score=7.0")
        assert response.status_code == 200
        data = response.json()
        if data["total"] > 0:
            for item in data["items"]:
                if item["cvss_base_score"] is not None:
                    assert item["cvss_base_score"] >= 7.0
    
    def test_get_threats_with_sorting(self, client, sample_threat):
        """測試排序"""
        response = client.get("/api/v1/threats?sort_by=cvss_base_score&sort_order=desc")
        assert response.status_code == 200
        data = response.json()
        if len(data["items"]) > 1:
            scores = [
                item["cvss_base_score"]
                for item in data["items"]
                if item["cvss_base_score"] is not None
            ]
            assert scores == sorted(scores, reverse=True)
    
    def test_get_threat_by_id_success(self, client, sample_threat):
        """測試查詢威脅詳情（成功）"""
        response = client.get(f"/api/v1/threats/{sample_threat.id}")
        assert response.status_code == 200
        data = response.json()
        assert "threat" in data
        assert "associated_assets" in data
        assert data["threat"]["id"] == sample_threat.id
    
    def test_get_threat_by_id_not_found(self, client):
        """測試查詢威脅詳情（不存在）"""
        response = client.get("/api/v1/threats/non-existent-id")
        assert response.status_code == 404
    
    def test_search_threats(self, client, sample_threat):
        """測試搜尋威脅"""
        response = client.get("/api/v1/threats/search?query=Test")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
    
    def test_search_threats_empty_query(self, client):
        """測試搜尋威脅（空查詢）"""
        response = client.get("/api/v1/threats/search?query=")
        assert response.status_code == 422  # 驗證錯誤
    
    def test_update_threat_status_success(self, client, sample_threat):
        """測試更新威脅狀態（成功）"""
        response = client.put(
            f"/api/v1/threats/{sample_threat.id}/status",
            json={"status": "Analyzing"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "Analyzing"
    
    def test_update_threat_status_not_found(self, client):
        """測試更新威脅狀態（不存在）"""
        response = client.put(
            "/api/v1/threats/non-existent-id/status",
            json={"status": "Analyzing"},
        )
        assert response.status_code == 404
    
    def test_update_threat_status_invalid_transition(self, client, sample_threat):
        """測試更新威脅狀態（無效轉換）"""
        # 先將狀態設為 Closed
        response = client.put(
            f"/api/v1/threats/{sample_threat.id}/status",
            json={"status": "Closed"},
        )
        assert response.status_code == 200
        
        # 嘗試從 Closed 轉換到其他狀態（應該失敗）
        response = client.put(
            f"/api/v1/threats/{sample_threat.id}/status",
            json={"status": "New"},
        )
        assert response.status_code == 400
    
    def test_update_threat_status_invalid_status(self, client, sample_threat):
        """測試更新威脅狀態（無效狀態）"""
        response = client.put(
            f"/api/v1/threats/{sample_threat.id}/status",
            json={"status": "InvalidStatus"},
        )
        assert response.status_code == 400

