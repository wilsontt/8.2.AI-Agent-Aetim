"""
API 速率限制中介軟體

實作 API 速率限制，防止濫用。
符合 T-5-4-3：安全性檢查
符合 NFR-006：API 速率限制
"""

from typing import Callable, Dict
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from shared_kernel.infrastructure.logging import get_logger
from datetime import datetime, timedelta
from collections import defaultdict

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    API 速率限制中介軟體
    
    限制每個 IP 的請求速率。
    符合 NFR-006：API 速率限制（防止濫用）
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        """
        初始化速率限制中介軟體
        
        Args:
            app: FastAPI 應用程式
            requests_per_minute: 每分鐘允許的請求數（預設 60）
            requests_per_hour: 每小時允許的請求數（預設 1000）
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.request_times: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        處理請求並檢查速率限制
        
        Args:
            request: HTTP 請求
            call_next: 下一個中介軟體或路由處理器
        
        Returns:
            Response: HTTP 回應
        """
        # 取得客戶端 IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 跳過健康檢查端點
        if request.url.path in ["/api/v1/health", "/health"]:
            return await call_next(request)
        
        # 檢查速率限制
        now = datetime.utcnow()
        
        # 清理過期的請求記錄
        self._cleanup_old_requests(client_ip, now)
        
        # 檢查每分鐘限制
        minute_ago = now - timedelta(minutes=1)
        recent_requests = [
            req_time for req_time in self.request_times[client_ip]
            if req_time > minute_ago
        ]
        
        if len(recent_requests) >= self.requests_per_minute:
            logger.warning(
                "API 速率限制觸發（每分鐘）",
                extra={
                    "client_ip": client_ip,
                    "requests": len(recent_requests),
                    "limit": self.requests_per_minute,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"請求過於頻繁，請稍後再試（每分鐘最多 {self.requests_per_minute} 次請求）",
                headers={"Retry-After": "60"},
            )
        
        # 檢查每小時限制
        hour_ago = now - timedelta(hours=1)
        hourly_requests = [
            req_time for req_time in self.request_times[client_ip]
            if req_time > hour_ago
        ]
        
        if len(hourly_requests) >= self.requests_per_hour:
            logger.warning(
                "API 速率限制觸發（每小時）",
                extra={
                    "client_ip": client_ip,
                    "requests": len(hourly_requests),
                    "limit": self.requests_per_hour,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"請求過於頻繁，請稍後再試（每小時最多 {self.requests_per_hour} 次請求）",
                headers={"Retry-After": "3600"},
            )
        
        # 記錄請求時間
        self.request_times[client_ip].append(now)
        
        # 處理請求
        response = await call_next(request)
        
        # 添加速率限制標頭
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(recent_requests) - 1
        )
        
        return response
    
    def _cleanup_old_requests(self, client_ip: str, now: datetime) -> None:
        """
        清理過期的請求記錄
        
        Args:
            client_ip: 客戶端 IP
            now: 當前時間
        """
        hour_ago = now - timedelta(hours=1)
        self.request_times[client_ip] = [
            req_time for req_time in self.request_times[client_ip]
            if req_time > hour_ago
        ]

