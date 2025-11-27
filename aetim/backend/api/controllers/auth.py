"""
身份驗證 API 控制器

提供身份驗證相關的 API 端點。
符合 AC-022-1, AC-022-2, AC-022-3, AC-022-4。
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional
import secrets
from system_management.application.services.auth_service import AuthService
from system_management.application.dtos.auth_dto import (
    AuthorizationUrlResponse,
    CallbackRequest,
    LoginResponse,
    LogoutRequest,
)
from system_management.infrastructure.external_services.oauth2_service import OAuth2Config
from shared_kernel.infrastructure.dependencies import get_db_session
from shared_kernel.infrastructure.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["身份驗證"])


def get_oauth2_config() -> OAuth2Config:
    """
    取得 OAuth2 設定（從環境變數）
    
    Returns:
        OAuth2Config: OAuth2 設定
    """
    import os
    
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


def get_auth_service(
    db_session: AsyncSession = Depends(get_db_session),
    oauth2_config: OAuth2Config = Depends(get_oauth2_config),
) -> AuthService:
    """
    取得身份驗證服務
    
    Args:
        db_session: 資料庫 Session
        oauth2_config: OAuth2 設定
    
    Returns:
        AuthService: 身份驗證服務
    """
    from system_management.infrastructure.external_services.oauth2_service import (
        OAuth2Service,
        TokenValidator,
    )
    from system_management.infrastructure.persistence.audit_log_repository import (
        AuditLogRepository,
    )
    
    oauth2_service = OAuth2Service(oauth2_config)
    token_validator = TokenValidator(oauth2_service)
    audit_log_repository = AuditLogRepository(db_session)
    
    return AuthService(
        oauth2_service=oauth2_service,
        token_validator=token_validator,
        audit_log_repository=audit_log_repository,
        db_session=db_session,
    )


def get_client_ip(request: Request) -> Optional[str]:
    """
    取得客戶端 IP 位址
    
    Args:
        request: FastAPI Request
    
    Returns:
        Optional[str]: IP 位址
    """
    # 檢查 X-Forwarded-For header（用於反向代理）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # 檢查 X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 使用直接連線的 IP
    return request.client.host if request.client else None


@router.get("/authorize", response_model=AuthorizationUrlResponse)
async def get_authorization_url(
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    取得授權 URL
    
    符合 AC-022-1：整合 OIDC/OAuth 2.0 身份驗證提供者 (IdP)
    符合 AC-022-2：支援單一登入 (SSO) 功能
    
    Returns:
        AuthorizationUrlResponse: 授權 URL 回應
    """
    # 生成狀態參數（用於 CSRF 保護）
    state = secrets.token_urlsafe(32)
    
    authorization_url = auth_service.get_authorization_url(state)
    
    return AuthorizationUrlResponse(
        authorization_url=authorization_url,
        state=state,
    )


@router.post("/callback", response_model=LoginResponse)
async def handle_callback(
    request: CallbackRequest,
    http_request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    處理授權回調
    
    符合 AC-022-1：整合 OIDC/OAuth 2.0 身份驗證提供者 (IdP)
    符合 AC-022-3：登入失敗時顯示明確的錯誤訊息
    符合 AC-022-4：記錄所有登入嘗試的稽核日誌（成功與失敗）
    
    Args:
        request: 授權回調請求
        http_request: HTTP 請求（用於取得 IP 和 User-Agent）
        auth_service: 身份驗證服務
    
    Returns:
        LoginResponse: 登入回應
    
    Raises:
        HTTPException: 當授權碼無效或登入失敗時
    """
    try:
        # 取得 IP 和 User-Agent
        ip_address = get_client_ip(http_request)
        user_agent = http_request.headers.get("User-Agent")
        
        # 處理授權回調
        token_info, user_info, user = await auth_service.handle_callback(
            code=request.code,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # 構建回應
        from system_management.application.dtos.auth_dto import (
            TokenResponse,
            UserInfoResponse,
        )
        
        return LoginResponse(
            token=TokenResponse(
                access_token=token_info.access_token,
                token_type=token_info.token_type,
                expires_in=token_info.expires_in,
                refresh_token=token_info.refresh_token,
                id_token=token_info.id_token,
            ),
            user=UserInfoResponse(
                id=user.id,
                subject_id=user.subject_id,
                email=user.email,
                display_name=user.display_name,
                is_active=user.is_active,
            ),
        )
    except ValueError as e:
        # 符合 AC-022-3：登入失敗時顯示明確的錯誤訊息
        logger.warning("登入失敗", extra={"error": str(e)})
        raise HTTPException(
            status_code=401,
            detail=f"登入失敗: {str(e)}",
        )
    except Exception as e:
        logger.error("處理授權回調時發生錯誤", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="處理授權回調時發生錯誤",
        )


@router.post("/logout")
async def logout(
    request: LogoutRequest,
    http_request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    user_id: Optional[str] = None,  # 從 Token 中取得（需要中介軟體）
):
    """
    登出
    
    符合 AC-022-4：記錄登出操作
    
    Args:
        request: 登出請求
        http_request: HTTP 請求（用於取得 IP 和 User-Agent）
        auth_service: 身份驗證服務
        user_id: 使用者 ID（從 Token 中取得）
    
    Returns:
        dict: 登出成功回應
    """
    # 取得 IP 和 User-Agent
    ip_address = get_client_ip(http_request)
    user_agent = http_request.headers.get("User-Agent")
    
    if user_id:
        await auth_service.logout(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    return {"message": "登出成功"}


@router.get("/me", response_model=UserInfoResponse)
async def get_current_user(
    auth_service: AuthService = Depends(get_auth_service),
    token: Optional[str] = None,  # 從 Authorization header 中取得（需要中介軟體）
):
    """
    取得當前使用者資訊
    
    Args:
        auth_service: 身份驗證服務
        token: Access Token（從 Authorization header 中取得）
    
    Returns:
        UserInfoResponse: 使用者資訊回應
    
    Raises:
        HTTPException: 當 Token 無效或過期時
    """
    if not token:
        raise HTTPException(
            status_code=401,
            detail="未提供 Token",
        )
    
    try:
        user_info = await auth_service.validate_token(token)
        user = await auth_service.get_user_by_subject_id(user_info.sub)
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="使用者不存在",
            )
        
        from system_management.application.dtos.auth_dto import UserInfoResponse
        
        return UserInfoResponse(
            id=user.id,
            subject_id=user.subject_id,
            email=user.email,
            display_name=user.display_name,
            is_active=user.is_active,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Token 驗證失敗: {str(e)}",
        )

