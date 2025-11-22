"""
健康檢查端點單元測試
"""

import pytest
from fastapi.testclient import TestClient
from api.controllers.health import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router, prefix="/api/v1")


@pytest.mark.unit
def test_health_check_endpoint():
    """測試健康檢查端點"""
    client = TestClient(app)
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "redis" in data["checks"]

