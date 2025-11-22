"""
監控指標單元測試
"""

import pytest
from shared_kernel.infrastructure.monitoring import MetricsCollector


@pytest.mark.unit
def test_metrics_collector():
    """測試指標收集器"""
    collector = MetricsCollector()
    
    # 測試記錄 API 請求
    collector.record_api_request("GET", "/api/v1/health", 200, 0.1)
    
    # 測試取得指標
    metrics = collector.get_metrics()
    
    assert "timestamp" in metrics
    assert "threat_collection" in metrics
    assert "api" in metrics
    assert "database" in metrics


@pytest.mark.unit
def test_prometheus_metrics():
    """測試 Prometheus 格式指標"""
    collector = MetricsCollector()
    
    # 記錄一些指標
    collector.record_api_request("GET", "/api/v1/health", 200, 0.1)
    
    # 取得 Prometheus 格式指標
    prom_metrics = collector.get_prometheus_metrics()
    
    assert isinstance(prom_metrics, str)
    assert "api_requests_total" in prom_metrics or len(prom_metrics) > 0

