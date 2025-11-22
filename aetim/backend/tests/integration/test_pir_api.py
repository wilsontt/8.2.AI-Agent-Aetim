"""
PIR API 整合測試

測試 PIR API 端點的功能。
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from main import app
from shared_kernel.infrastructure.database import get_db
from analysis_assessment.infrastructure.persistence.pir_repository import PIRRepository
from analysis_assessment.domain.aggregates.pir import PIR


@pytest.fixture
def client(db_session):
    """建立測試客戶端"""
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_pir(client, db_session):
    """測試建立 PIR"""
    response = client.post(
        "/api/v1/pirs",
        json={
            "name": "測試 PIR",
            "description": "測試描述",
            "priority": "高",
            "condition_type": "產品名稱",
            "condition_value": "VMware",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["message"] == "PIR 建立成功"


@pytest.mark.asyncio
async def test_get_pirs(client, db_session):
    """測試查詢 PIR 清單"""
    # 先建立一個 PIR
    repository = PIRRepository(db_session)
    pir = PIR.create(
        name="測試 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
    )
    await repository.save(pir)
    
    # 查詢清單
    response = client.get("/api/v1/pirs?page=1&page_size=20")
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total_count" in data
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_get_pir_by_id(client, db_session):
    """測試查詢 PIR 詳情"""
    # 先建立一個 PIR
    repository = PIRRepository(db_session)
    pir = PIR.create(
        name="測試 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
    )
    await repository.save(pir)
    
    # 查詢詳情
    response = client.get(f"/api/v1/pirs/{pir.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == pir.id
    assert data["name"] == "測試 PIR"


@pytest.mark.asyncio
async def test_update_pir(client, db_session):
    """測試更新 PIR"""
    # 先建立一個 PIR
    repository = PIRRepository(db_session)
    pir = PIR.create(
        name="測試 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
    )
    await repository.save(pir)
    
    # 更新 PIR
    response = client.put(
        f"/api/v1/pirs/{pir.id}",
        json={
            "name": "更新後的 PIR",
            "description": "更新後的描述",
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "PIR 更新成功"
    
    # 驗證已更新
    response = client.get(f"/api/v1/pirs/{pir.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "更新後的 PIR"


@pytest.mark.asyncio
async def test_delete_pir(client, db_session):
    """測試刪除 PIR"""
    # 先建立一個 PIR
    repository = PIRRepository(db_session)
    pir = PIR.create(
        name="測試 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
    )
    await repository.save(pir)
    
    # 刪除 PIR
    response = client.delete(f"/api/v1/pirs/{pir.id}")
    
    assert response.status_code == 204
    
    # 驗證已刪除
    response = client.get(f"/api/v1/pirs/{pir.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_toggle_pir(client, db_session):
    """測試切換 PIR 啟用狀態"""
    # 先建立一個 PIR
    repository = PIRRepository(db_session)
    pir = PIR.create(
        name="測試 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
        is_enabled=True,
    )
    await repository.save(pir)
    
    # 切換狀態
    response = client.patch(f"/api/v1/pirs/{pir.id}/toggle")
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_enabled"] is False
    assert "已停用" in data["message"]


@pytest.mark.asyncio
async def test_get_enabled_pirs(client, db_session):
    """測試查詢啟用的 PIR"""
    # 先建立多個 PIR
    repository = PIRRepository(db_session)
    
    enabled_pir = PIR.create(
        name="啟用的 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
        is_enabled=True,
    )
    await repository.save(enabled_pir)
    
    disabled_pir = PIR.create(
        name="停用的 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
        is_enabled=False,
    )
    await repository.save(disabled_pir)
    
    # 查詢啟用的 PIR
    response = client.get("/api/v1/pirs/enabled/list")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert all(pir["is_enabled"] for pir in data)

