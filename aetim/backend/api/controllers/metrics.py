"""
監控指標控制器

提供監控指標端點，符合 plan.md 第 9.3.3 節的要求。
"""

from fastapi import APIRouter, Response
from shared_kernel.infrastructure.monitoring import metrics_collector
from shared_kernel.infrastructure.monitoring import get_prometheus_metrics

router = APIRouter()


@router.get("/metrics")
async def get_metrics():
    """
    取得關鍵效能指標（KPI）
    
    回應格式：
    {
        "timestamp": "2025-11-21T10:00:00Z",
        "threat_collection": {
            "success_rate": 0.95,
            "average_duration": 120.5,
            "total_collected": 1500
        },
        "api": {
            "average_response_time": 0.5,
            "requests_per_minute": 100,
            "error_rate": 0.01
        },
        "database": {
            "query_count": 5000,
            "average_query_time": 0.1
        }
    }
    """
    return metrics_collector.get_metrics()


@router.get("/metrics/prometheus")
async def get_prometheus_metrics_endpoint():
    """
    取得 Prometheus 格式指標
    
    回應 Prometheus 格式的指標資料，可用於 Prometheus 收集。
    """
    metrics = get_prometheus_metrics()
    return Response(content=metrics, media_type="text/plain; version=0.0.4")

