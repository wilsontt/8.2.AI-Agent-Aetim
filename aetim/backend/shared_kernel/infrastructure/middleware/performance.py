"""
效能監控中介軟體

記錄 API 回應時間和效能指標。
符合 T-5-4-2：效能優化
符合 NFR-008：指標監控
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from shared_kernel.infrastructure.logging import get_logger
from prometheus_client import Histogram, Counter

logger = get_logger(__name__)

# Prometheus 指標
api_request_duration = Histogram(
    "api_request_duration_seconds",
    "API 請求處理時間（秒）",
    ["method", "endpoint", "status_code"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)

api_request_count = Counter(
    "api_request_total",
    "API 請求總數",
    ["method", "endpoint", "status_code"],
)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    效能監控中介軟體
    
    記錄 API 回應時間和效能指標。
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        處理請求並記錄效能指標
        
        Args:
            request: HTTP 請求
            call_next: 下一個中介軟體或路由處理器
        
        Returns:
            Response: HTTP 回應
        """
        start_time = time.time()
        
        # 處理請求
        response = await call_next(request)
        
        # 計算處理時間
        elapsed_time = time.time() - start_time
        
        # 取得端點資訊
        endpoint = request.url.path
        method = request.method
        status_code = response.status_code
        
        # 記錄 Prometheus 指標
        api_request_duration.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
        ).observe(elapsed_time)
        
        api_request_count.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
        ).inc()
        
        # 記錄日誌（如果回應時間超過閾值）
        if elapsed_time > 2.0:
            logger.warning(
                "API 回應時間超過閾值",
                extra={
                    "method": method,
                    "endpoint": endpoint,
                    "status_code": status_code,
                    "elapsed_time": elapsed_time,
                },
            )
        
        # 添加回應時間標頭
        response.headers["X-Response-Time"] = f"{elapsed_time:.3f}"
        
        return response

