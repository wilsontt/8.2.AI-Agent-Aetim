"""
分佈式追蹤基礎設施

實作分佈式追蹤，符合 plan.md 第 9.3.5 節的要求。
"""

import uuid
from contextvars import ContextVar
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
from shared_kernel.infrastructure.logging import get_logger

# 追蹤 ID 上下文變數
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

logger = get_logger(__name__)


def get_trace_id() -> Optional[str]:
    """
    取得當前請求的追蹤 ID
    
    Returns:
        追蹤 ID（UUID 字串）
    """
    return trace_id_var.get()


def generate_trace_id() -> str:
    """
    生成新的追蹤 ID
    
    Returns:
        追蹤 ID（UUID 字串）
    """
    return str(uuid.uuid4())


class TracingMiddleware(BaseHTTPMiddleware):
    """追蹤中介軟體"""

    async def dispatch(self, request: Request, call_next):
        """
        處理請求並加入追蹤 ID
        
        Args:
            request: FastAPI 請求物件
            call_next: 下一個中介軟體或路由處理器
        
        Returns:
            FastAPI 回應物件
        """
        # 從請求標頭取得追蹤 ID，或生成新的
        trace_id = request.headers.get("X-Trace-Id") or generate_trace_id()
        trace_id_var.set(trace_id)

        # 將追蹤 ID 加入請求狀態
        request.state.trace_id = trace_id

        # 記錄請求開始
        start_time = time.time()
        logger.info(
            "Request started",
            extra={
                "trace_id": trace_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
            },
        )

        try:
            # 處理請求
            response = await call_next(request)
            elapsed_time = time.time() - start_time

            # 將追蹤 ID 加入回應標頭
            response.headers["X-Trace-Id"] = trace_id

            # 記錄請求完成
            logger.info(
                "Request completed",
                extra={
                    "trace_id": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "elapsed_time": round(elapsed_time, 3),
                },
            )

            return response

        except Exception as e:
            elapsed_time = time.time() - start_time

            # 記錄請求錯誤
            logger.error(
                "Request failed",
                extra={
                    "trace_id": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "elapsed_time": round(elapsed_time, 3),
                },
                exc_info=True,
            )

            raise

