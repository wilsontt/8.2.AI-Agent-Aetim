"""
AI 服務健康檢查測試
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.mark.unit
def test_health_check():
    """測試 AI 服務健康檢查端點"""
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ai-service"
    assert "version" in data


@pytest.mark.unit
def test_health_check_v1():
    """測試 AI 服務健康檢查端點（API v1）"""
    client = TestClient(app)
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "ai-service"

