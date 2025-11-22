"""
AI 服務健康檢查測試
"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.mark.unit
def test_health_check():
    """測試 AI 服務健康檢查端點"""
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

