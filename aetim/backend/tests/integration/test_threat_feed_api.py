"""
威脅情資來源 API 整合測試

測試威脅情資來源 API 端點的功能。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from shared_kernel.infrastructure.database import get_db
from threat_intelligence.infrastructure.persistence.threat_feed_repository import ThreatFeedRepository
from threat_intelligence.domain.aggregates.threat_feed import ThreatFeed


@pytest.fixture
def client(db_session):
    """建立測試客戶端"""
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_threat_feed(client, db_session):
    """測試建立威脅情資來源"""
    response = client.post(
        "/api/v1/threat-feeds",
        json={
            "name": "CISA KEV",
            "description": "CISA Known Exploited Vulnerabilities",
            "priority": "P0",
            "collection_frequency": "每小時",
            "collection_strategy": "API / JSON Feed",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "威脅情資來源建立成功"


@pytest.mark.asyncio
async def test_get_threat_feeds(client, db_session):
    """測試查詢威脅情資來源清單"""
    # 先建立一個威脅情資來源
    repository = ThreatFeedRepository(db_session)
    threat_feed = ThreatFeed.create(
        name="CISA KEV",
        priority="P0",
        collection_frequency="每小時",
    )
    await repository.save(threat_feed)
    
    # 查詢清單
    response = client.get("/api/v1/threat-feeds?page=1&page_size=20")
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total_count" in data
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_get_threat_feed_by_id(client, db_session):
    """測試查詢威脅情資來源詳情"""
    # 先建立一個威脅情資來源
    repository = ThreatFeedRepository(db_session)
    threat_feed = ThreatFeed.create(
        name="CISA KEV",
        priority="P0",
        collection_frequency="每小時",
    )
    await repository.save(threat_feed)
    
    # 查詢詳情
    response = client.get(f"/api/v1/threat-feeds/{threat_feed.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == threat_feed.id
    assert data["name"] == "CISA KEV"


@pytest.mark.asyncio
async def test_update_threat_feed(client, db_session):
    """測試更新威脅情資來源"""
    # 先建立一個威脅情資來源
    repository = ThreatFeedRepository(db_session)
    threat_feed = ThreatFeed.create(
        name="CISA KEV",
        priority="P0",
        collection_frequency="每小時",
    )
    await repository.save(threat_feed)
    
    # 更新威脅情資來源
    response = client.put(
        f"/api/v1/threat-feeds/{threat_feed.id}",
        json={
            "name": "NVD",
            "priority": "P1",
            "collection_frequency": "每日",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "威脅情資來源更新成功"
    
    # 驗證已更新
    response = client.get(f"/api/v1/threat-feeds/{threat_feed.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "NVD"
    assert data["priority"] == "P1"


@pytest.mark.asyncio
async def test_delete_threat_feed(client, db_session):
    """測試刪除威脅情資來源"""
    # 先建立一個威脅情資來源
    repository = ThreatFeedRepository(db_session)
    threat_feed = ThreatFeed.create(
        name="CISA KEV",
        priority="P0",
        collection_frequency="每小時",
    )
    await repository.save(threat_feed)
    
    # 刪除威脅情資來源
    response = client.delete(f"/api/v1/threat-feeds/{threat_feed.id}")
    
    assert response.status_code == 204
    
    # 驗證已刪除
    response = client.get(f"/api/v1/threat-feeds/{threat_feed.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_toggle_threat_feed(client, db_session):
    """測試切換威脅情資來源啟用狀態"""
    # 先建立一個威脅情資來源
    repository = ThreatFeedRepository(db_session)
    threat_feed = ThreatFeed.create(
        name="CISA KEV",
        priority="P0",
        collection_frequency="每小時",
        is_enabled=True,
    )
    await repository.save(threat_feed)
    
    # 切換狀態
    response = client.patch(f"/api/v1/threat-feeds/{threat_feed.id}/toggle")
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_enabled"] is False
    assert "已停用" in data["message"]


@pytest.mark.asyncio
async def test_get_collection_status(client, db_session):
    """測試查詢收集狀態"""
    # 先建立一個威脅情資來源
    repository = ThreatFeedRepository(db_session)
    threat_feed = ThreatFeed.create(
        name="CISA KEV",
        priority="P0",
        collection_frequency="每小時",
    )
    threat_feed.update_collection_status("success", record_count=10)
    await repository.save(threat_feed)
    
    # 查詢收集狀態
    response = client.get(f"/api/v1/threat-feeds/{threat_feed.id}/status")
    
    assert response.status_code == 200
    data = response.json()
    assert data["threat_feed_id"] == threat_feed.id
    assert data["last_collection_status"] == "success"


@pytest.mark.asyncio
async def test_get_all_collection_status(client, db_session):
    """測試查詢所有收集狀態"""
    # 先建立多個威脅情資來源
    repository = ThreatFeedRepository(db_session)
    
    feed1 = ThreatFeed.create(
        name="CISA KEV",
        priority="P0",
        collection_frequency="每小時",
        is_enabled=True,
    )
    feed1.update_collection_status("success", record_count=10)
    await repository.save(feed1)
    
    feed2 = ThreatFeed.create(
        name="NVD",
        priority="P1",
        collection_frequency="每日",
        is_enabled=True,
    )
    feed2.update_collection_status("failed", error_message="連線失敗")
    await repository.save(feed2)
    
    # 查詢所有收集狀態
    response = client.get("/api/v1/threat-feeds/status/list")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

