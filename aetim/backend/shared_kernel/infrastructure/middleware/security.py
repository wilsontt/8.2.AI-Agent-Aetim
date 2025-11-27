"""
安全性中介軟體

提供安全性相關的中介軟體功能。
符合 T-5-4-3：安全性檢查
符合 NFR-006：輸入驗證
"""

from typing import Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from shared_kernel.infrastructure.logging import get_logger
import re

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    安全性標頭中介軟體
    
    添加安全性相關的 HTTP 標頭。
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        處理請求並添加安全性標頭
        
        Args:
            request: HTTP 請求
            call_next: 下一個中介軟體或路由處理器
        
        Returns:
            Response: HTTP 回應
        """
        response = await call_next(request)
        
        # 添加安全性標頭
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    輸入驗證中介軟體
    
    驗證和清理使用者輸入，防止 SQL 注入、XSS 等攻擊。
    符合 NFR-006：輸入驗證
    """
    
    # SQL 注入模式
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)",
        r"(--|#|/\*|\*/)",
        r"(\b(CHAR|CONCAT|SUBSTRING)\s*\()",
    ]
    
    # XSS 模式
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"<iframe[^>]*>.*?</iframe>",
        r"javascript:",
        r"on\w+\s*=",
        r"<img[^>]*onerror",
        r"<svg[^>]*onload",
    ]
    
    # 路徑遍歷模式
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e%5c",
    ]
    
    def __init__(self, app, enabled: bool = True):
        """
        初始化輸入驗證中介軟體
        
        Args:
            app: FastAPI 應用程式
            enabled: 是否啟用驗證
        """
        super().__init__(app)
        self.enabled = enabled
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        處理請求並驗證輸入
        
        Args:
            request: HTTP 請求
            call_next: 下一個中介軟體或路由處理器
        
        Returns:
            Response: HTTP 回應
        """
        if not self.enabled:
            return await call_next(request)
        
        # 驗證查詢參數
        for key, value in request.query_params.items():
            if self._is_malicious(value):
                logger.warning(
                    "偵測到惡意輸入",
                    extra={
                        "type": "query_param",
                        "key": key,
                        "value": value[:100],  # 限制日誌長度
                        "ip_address": request.client.host if request.client else None,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="無效的輸入參數",
                )
        
        # 驗證路徑參數
        for key, value in request.path_params.items():
            if self._is_malicious(str(value)):
                logger.warning(
                    "偵測到惡意輸入",
                    extra={
                        "type": "path_param",
                        "key": key,
                        "value": str(value)[:100],
                        "ip_address": request.client.host if request.client else None,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="無效的路徑參數",
                )
        
        return await call_next(request)
    
    def _is_malicious(self, value: str) -> bool:
        """
        檢查輸入是否包含惡意內容
        
        Args:
            value: 輸入值
        
        Returns:
            bool: 是否包含惡意內容
        """
        if not isinstance(value, str):
            value = str(value)
        
        value_lower = value.lower()
        
        # 檢查 SQL 注入
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        # 檢查 XSS
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        # 檢查路徑遍歷
        for pattern in self.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        return False

