"""
健康檢查端點整合測試
"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.mark.integration
def test_health_check_endpoint():
    """測試健康檢查端點"""
    client = TestClient(app)
    response = client.get("/api/v1/health")
    
    assert response.status_code in [200, 503]  # 可能因為服務未啟動而返回 503
    data = response.json()
    
    assert "status" in data
    assert "timestamp" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "redis" in data["checks"]


@pytest.mark.integration
def test_health_check_response_format():
    """測試健康檢查回應格式"""
    client = TestClient(app)
    response = client.get("/api/v1/health")
    
    if response.status_code == 200:
        data = response.json()
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert isinstance(data["checks"], dict)

