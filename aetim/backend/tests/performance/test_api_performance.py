"""
API 效能測試

測試 API 回應時間是否符合 NFR-001 要求（≤ 2 秒）。
符合 T-5-4-2：效能優化
"""

import pytest
import time
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """建立測試客戶端"""
    return TestClient(app)


def test_health_check_performance(client: TestClient):
    """測試健康檢查 API 回應時間"""
    start_time = time.time()
    response = client.get("/api/v1/health")
    elapsed_time = time.time() - start_time
    
    assert response.status_code == 200
    assert elapsed_time < 2.0, f"健康檢查 API 回應時間 {elapsed_time:.2f} 秒超過 2 秒"


def test_system_status_performance(client: TestClient):
    """測試系統狀態 API 回應時間"""
    start_time = time.time()
    response = client.get("/api/v1/system-status")
    elapsed_time = time.time() - start_time
    
    # 應該返回 401（未認證）或 200（已認證）
    assert response.status_code in [200, 401]
    assert elapsed_time < 2.0, f"系統狀態 API 回應時間 {elapsed_time:.2f} 秒超過 2 秒"


def test_threat_statistics_performance(client: TestClient):
    """測試威脅統計 API 回應時間"""
    endpoints = [
        "/api/v1/statistics/threats/trend",
        "/api/v1/statistics/threats/risk-distribution",
        "/api/v1/statistics/threats/affected-assets",
        "/api/v1/statistics/threats/sources",
    ]
    
    for endpoint in endpoints:
        start_time = time.time()
        response = client.get(endpoint)
        elapsed_time = time.time() - start_time
        
        # 應該返回 401（未認證）或 200（已認證）
        assert response.status_code in [200, 401]
        assert elapsed_time < 2.0, f"{endpoint} API 回應時間 {elapsed_time:.2f} 秒超過 2 秒"


def test_asset_statistics_performance(client: TestClient):
    """測試資產統計 API 回應時間"""
    start_time = time.time()
    response = client.get("/api/v1/statistics/assets")
    elapsed_time = time.time() - start_time
    
    # 應該返回 401（未認證）或 200（已認證）
    assert response.status_code in [200, 401]
    assert elapsed_time < 2.0, f"資產統計 API 回應時間 {elapsed_time:.2f} 秒超過 2 秒"


def test_audit_logs_performance(client: TestClient):
    """測試稽核日誌 API 回應時間"""
    start_time = time.time()
    response = client.get("/api/v1/audit-logs?page=1&page_size=20")
    elapsed_time = time.time() - start_time
    
    # 應該返回 401（未認證）或 200（已認證）
    assert response.status_code in [200, 401]
    assert elapsed_time < 2.0, f"稽核日誌 API 回應時間 {elapsed_time:.2f} 秒超過 2 秒"


def test_concurrent_requests_performance(client: TestClient):
    """測試並發請求效能"""
    import concurrent.futures
    
    def make_request():
        return client.get("/api/v1/health")
    
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    elapsed_time = time.time() - start_time
    
    # 所有請求應該成功
    assert all(r.status_code == 200 for r in results)
    # 10 個並發請求應該在合理時間內完成（例如 5 秒內）
    assert elapsed_time < 5.0, f"10 個並發請求耗時 {elapsed_time:.2f} 秒超過 5 秒"

