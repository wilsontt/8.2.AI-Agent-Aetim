"""
稽核日誌中介軟體

自動記錄 API 請求的稽核日誌。
提取使用者資訊、IP 位址、User Agent。
"""

from typing import Callable, Optional
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from system_management.application.services.audit_log_service import AuditLogService
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    稽核日誌中介軟體
    
    自動記錄 API 請求的稽核日誌。
    提取使用者資訊、IP 位址、User Agent。
    """
    
    # 不需要記錄的端點（健康檢查、指標等）
    EXCLUDED_PATHS = [
        "/health",
        "/metrics",
        "/docs",
        "/openapi.json",
        "/redoc",
    ]
    
    # 需要記錄的操作類型映射（HTTP 方法 -> 操作類型）
    ACTION_MAPPING = {
        "GET": "VIEW",
        "POST": "CREATE",
        "PUT": "UPDATE",
        "PATCH": "UPDATE",
        "DELETE": "DELETE",
    }
    
    def __init__(self, app: ASGIApp, audit_log_service: Optional[AuditLogService] = None):
        """
        初始化中介軟體
        
        Args:
            app: ASGI 應用程式
            audit_log_service: 稽核日誌服務（可選，如果為 None 則不記錄）
        """
        super().__init__(app)
        self.audit_log_service = audit_log_service
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        處理請求並記錄稽核日誌
        
        Args:
            request: HTTP 請求
            call_next: 下一個中介軟體或路由處理器
        
        Returns:
            Response: HTTP 回應
        """
        # 檢查是否需要記錄
        if not self._should_log(request):
            return await call_next(request)
        
        # 如果沒有稽核日誌服務，跳過記錄
        if not self.audit_log_service:
            return await call_next(request)
        
        # 提取請求資訊
        user_id = self._extract_user_id(request)
        action = self._extract_action(request)
        resource_type = self._extract_resource_type(request)
        resource_id = self._extract_resource_id(request)
        ip_address = self._extract_ip_address(request)
        user_agent = self._extract_user_agent(request)
        
        # 處理請求
        response = await call_next(request)
        
        # 只記錄成功的操作（2xx、3xx 狀態碼）
        if response.status_code < 400:
            try:
                # 記錄稽核日誌（非同步，不阻塞回應）
                await self.audit_log_service.log_action(
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    details={
                        "method": request.method,
                        "path": str(request.url.path),
                        "status_code": response.status_code,
                    },
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            except Exception as e:
                # 記錄錯誤但不影響請求處理
                logger.error(
                    "記錄稽核日誌失敗",
                    extra={
                        "error": str(e),
                        "path": str(request.url.path),
                    },
                    exc_info=True,
                )
        
        return response
    
    def _should_log(self, request: Request) -> bool:
        """
        判斷是否需要記錄稽核日誌
        
        Args:
            request: HTTP 請求
        
        Returns:
            bool: 是否需要記錄
        """
        # 排除不需要記錄的端點
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return False
        
        # 只記錄 API 端點（/api/v1/...）
        if not path.startswith("/api/v1/"):
            return False
        
        # 只記錄會改變狀態的操作（POST、PUT、PATCH、DELETE）
        # GET 請求通常不需要記錄（除非特別要求）
        if request.method == "GET":
            return False
        
        return True
    
    def _extract_user_id(self, request: Request) -> Optional[str]:
        """
        提取使用者 ID
        
        Args:
            request: HTTP 請求
        
        Returns:
            Optional[str]: 使用者 ID
        """
        # 從請求狀態中提取使用者資訊（如果已通過身份驗證）
        # 這裡假設身份驗證中介軟體會將使用者資訊存入 request.state
        if hasattr(request.state, "user_id"):
            return request.state.user_id
        
        # 也可以從 JWT token 中提取（如果有的話）
        # 這裡暫時返回 None，實際實作時需要根據身份驗證機制調整
        return None
    
    def _extract_action(self, request: Request) -> str:
        """
        提取操作類型
        
        Args:
            request: HTTP 請求
        
        Returns:
            str: 操作類型
        """
        return self.ACTION_MAPPING.get(request.method, "VIEW")
    
    def _extract_resource_type(self, request: Request) -> str:
        """
        提取資源類型
        
        Args:
            request: HTTP 請求
        
        Returns:
            str: 資源類型
        """
        # 從路徑中提取資源類型（例如：/api/v1/assets -> Asset）
        path = request.url.path
        if path.startswith("/api/v1/"):
            parts = path[len("/api/v1/"):].split("/")
            if parts:
                resource = parts[0]
                # 轉換為 PascalCase（例如：assets -> Asset）
                return resource.capitalize().rstrip("s") if resource.endswith("s") else resource.capitalize()
        
        return "Unknown"
    
    def _extract_resource_id(self, request: Request) -> Optional[str]:
        """
        提取資源 ID
        
        Args:
            request: HTTP 請求
        
        Returns:
            Optional[str]: 資源 ID
        """
        # 從路徑中提取資源 ID（例如：/api/v1/assets/123 -> 123）
        path = request.url.path
        if path.startswith("/api/v1/"):
            parts = path[len("/api/v1/"):].split("/")
            if len(parts) >= 2:
                # 假設第二個部分是資源 ID（UUID 格式）
                resource_id = parts[1]
                # 驗證是否為有效的 UUID 格式（36 個字元，包含連字號）
                if len(resource_id) == 36 and resource_id.count("-") == 4:
                    return resource_id
        
        return None
    
    def _extract_ip_address(self, request: Request) -> Optional[str]:
        """
        提取 IP 位址
        
        Args:
            request: HTTP 請求
        
        Returns:
            Optional[str]: IP 位址
        """
        # 從請求標頭中提取真實 IP（考慮代理伺服器）
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # 取第一個 IP（真實客戶端 IP）
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 使用客戶端 IP
        if request.client:
            return request.client.host
        
        return None
    
    def _extract_user_agent(self, request: Request) -> Optional[str]:
        """
        提取 User Agent
        
        Args:
            request: HTTP 請求
        
        Returns:
            Optional[str]: User Agent
        """
        return request.headers.get("User-Agent")

