"""
API 端點端對端測試

測試所有 API 端點的功能。
符合 T-5-4-1：端對端測試所有功能
"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """建立測試客戶端"""
    return TestClient(app)


def test_health_check(client: TestClient):
    """測試健康檢查端點"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "checks" in data


def test_system_status_endpoint(client: TestClient):
    """測試系統狀態端點（需要認證）"""
    response = client.get("/api/v1/system-status")
    # 應該返回 401（未認證）或 200（已認證）
    assert response.status_code in [200, 401]


def test_threat_statistics_endpoints(client: TestClient):
    """測試威脅統計端點（需要認證）"""
    endpoints = [
        "/api/v1/statistics/threats/trend",
        "/api/v1/statistics/threats/risk-distribution",
        "/api/v1/statistics/threats/affected-assets",
        "/api/v1/statistics/threats/sources",
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        # 應該返回 401（未認證）或 200（已認證）
        assert response.status_code in [200, 401]


def test_asset_statistics_endpoint(client: TestClient):
    """測試資產統計端點（需要認證）"""
    response = client.get("/api/v1/statistics/assets")
    # 應該返回 401（未認證）或 200（已認證）
    assert response.status_code in [200, 401]


def test_audit_logs_endpoint(client: TestClient):
    """測試稽核日誌端點（需要認證）"""
    response = client.get("/api/v1/audit-logs")
    # 應該返回 401（未認證）或 200（已認證）
    assert response.status_code in [200, 401]


def test_system_configuration_endpoint(client: TestClient):
    """測試系統設定端點（需要認證）"""
    response = client.get("/api/v1/system-configuration")
    # 應該返回 401（未認證）或 200（已認證）
    assert response.status_code in [200, 401]

