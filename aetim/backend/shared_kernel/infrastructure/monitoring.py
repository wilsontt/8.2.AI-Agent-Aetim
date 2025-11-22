"""
監控指標收集

實作監控指標收集，符合 plan.md 第 9.3.3 節的要求。
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from typing import Dict, Any
from datetime import datetime

# 定義 Prometheus 指標
api_requests_total = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status_code"],
)

api_request_duration = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
)

threat_collection_total = Counter(
    "threat_collection_total",
    "Total threat collections",
    ["source", "status"],
)

threat_collection_duration = Histogram(
    "threat_collection_duration_seconds",
    "Threat collection duration in seconds",
    ["source"],
)

active_connections = Gauge(
    "active_connections",
    "Number of active connections",
)

database_query_duration = Histogram(
    "database_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
)


class MetricsCollector:
    """監控指標收集器"""

    def __init__(self):
        self._metrics: Dict[str, Any] = {
            "threat_collection": {
                "success_rate": 0.0,
                "average_duration": 0.0,
                "total_collected": 0,
            },
            "api": {
                "average_response_time": 0.0,
                "requests_per_minute": 0,
                "error_rate": 0.0,
            },
            "database": {
                "query_count": 0,
                "average_query_time": 0.0,
            },
        }

    def record_api_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ):
        """記錄 API 請求"""
        api_requests_total.labels(
            method=method, endpoint=endpoint, status_code=status_code
        ).inc()
        api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def record_threat_collection(
        self, source: str, status: str, duration: float
    ):
        """記錄威脅收集"""
        threat_collection_total.labels(source=source, status=status).inc()
        threat_collection_duration.labels(source=source).observe(duration)

    def record_database_query(self, operation: str, duration: float):
        """記錄資料庫查詢"""
        database_query_duration.labels(operation=operation).observe(duration)

    def get_metrics(self) -> Dict[str, Any]:
        """取得所有指標"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            **self._metrics,
        }

    def get_prometheus_metrics(self) -> str:
        """取得 Prometheus 格式指標"""
        return generate_latest().decode("utf-8")


# 全域指標收集器實例
metrics_collector = MetricsCollector()

