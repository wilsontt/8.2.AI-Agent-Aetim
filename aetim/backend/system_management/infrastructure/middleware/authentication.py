"""
身份驗證中介軟體

提供 FastAPI 的身份驗證中介軟體。
符合 AC-023-4：在 API 層級驗證權限，防止未授權存取
"""

from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import HTTPException
from ...application.services.auth_service import AuthService
from ...infrastructure.external_services.oauth2_service import OAuth2Config, TokenValidator
from shared_kernel.infrastructure.database import AsyncSessionLocal
from shared_kernel.infrastructure.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
import os

logger = get_logger(__name__)


def get_oauth2_config() -> OAuth2Config:
    """
    取得 OAuth2 設定（從環境變數）
    
    Returns:
        OAuth2Config: OAuth2 設定
    """
    return OAuth2Config(
        client_id=os.getenv("OAUTH2_CLIENT_ID", ""),
        client_secret=os.getenv("OAUTH2_CLIENT_SECRET", ""),
        authorization_endpoint=os.getenv("OAUTH2_AUTHORIZATION_ENDPOINT", ""),
        token_endpoint=os.getenv("OAUTH2_TOKEN_ENDPOINT", ""),
        userinfo_endpoint=os.getenv("OAUTH2_USERINFO_ENDPOINT", ""),
        redirect_uri=os.getenv("OAUTH2_REDIRECT_URI", ""),
        scopes=os.getenv("OAUTH2_SCOPES", "openid profile email").split(),
        issuer=os.getenv("OAUTH2_ISSUER"),
        jwks_uri=os.getenv("OAUTH2_JWKS_URI"),
    )


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    身份驗證中介軟體
    
    提供 Token 驗證和使用者上下文設定功能。
    符合 AC-023-4：在 API 層級驗證權限，防止未授權存取
    """
    
    # 不需要身份驗證的路徑
    EXCLUDED_PATHS = [
        "/api/v1/health",
        "/api/v1/metrics",
        "/api/v1/auth/authorize",
        "/api/v1/auth/callback",
        "/docs",
        "/openapi.json",
        "/redoc",
    ]
    
    def __init__(self, app: Callable):
        """
        初始化身份驗證中介軟體
        
        Args:
            app: FastAPI 應用程式
        """
        super().__init__(app)
        self.oauth2_config = get_oauth2_config()
        from ...infrastructure.external_services.oauth2_service import OAuth2Service
        oauth2_service = OAuth2Service(self.oauth2_config)
        self.token_validator = TokenValidator(oauth2_service)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        處理請求
        
        Args:
            request: HTTP 請求
            call_next: 下一個中介軟體或路由處理器
        
        Returns:
            Response: HTTP 回應
        """
        # 檢查是否為排除的路徑
        if any(request.url.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # 提取 Token
        token = self._extract_token(request)
        
        if not token:
            # 未提供 Token，返回 401
            return JSONResponse(
                status_code=401,
                content={"detail": "未提供身份驗證 Token"},
            )
        
        try:
            # 驗證 Token
            token_data = await self.token_validator.validate_token(token)
            
            # 取得使用者實體
            async with AsyncSessionLocal() as db_session:
                from ...infrastructure.persistence.models import User
                from sqlalchemy import select
                
                result = await db_session.execute(
                    select(User).where(User.subject_id == token_data.get("sub"))
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "使用者不存在"},
                    )
                
                # 設定使用者上下文
                request.state.user_id = user.id
                request.state.user = user
                request.state.token = token
                
                # 繼續處理請求
                return await call_next(request)
        except ValueError as e:
            # Token 驗證失敗，返回 401
            logger.warning(
                "Token 驗證失敗",
                extra={
                    "path": request.url.path,
                    "error": str(e),
                }
            )
            return JSONResponse(
                status_code=401,
                content={"detail": f"Token 驗證失敗: {str(e)}"},
            )
        except Exception as e:
            # 其他錯誤，返回 500
            logger.error(
                "身份驗證中介軟體發生錯誤",
                extra={
                    "path": request.url.path,
                    "error": str(e),
                },
                exc_info=True,
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "身份驗證處理失敗"},
            )
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """
        從請求中提取 Token
        
        Args:
            request: HTTP 請求
        
        Returns:
            Optional[str]: Token 字串，如果不存在則返回 None
        """
        # 從 Authorization header 提取 Token
        authorization = request.headers.get("Authorization")
        
        if not authorization:
            return None
        
        # 檢查格式：Bearer <token>
        if not authorization.startswith("Bearer "):
            return None
        
        return authorization[7:]  # 移除 "Bearer " 前綴

