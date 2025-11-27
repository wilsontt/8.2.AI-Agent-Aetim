"""
授權裝飾器

提供 FastAPI 路由的授權裝飾器。
符合 AC-023-4：在 API 層級驗證權限，防止未授權存取
"""

from functools import wraps
from typing import Callable, List, Optional
from fastapi import HTTPException, Request, Depends
from ...application.services.authorization_service import AuthorizationService
from ...domain.value_objects.role_name import RoleName
from ...domain.value_objects.permission_name import PermissionName
from shared_kernel.infrastructure.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


def get_authorization_service(
    db_session: AsyncSession = Depends(get_db),
) -> AuthorizationService:
    """
    取得授權服務
    
    Args:
        db_session: 資料庫 Session
    
    Returns:
        AuthorizationService: 授權服務
    """
    from ...infrastructure.persistence.audit_log_repository import AuditLogRepository
    
    audit_log_repository = AuditLogRepository(db_session)
    return AuthorizationService(db_session, audit_log_repository)


def get_current_user_id(request: Request) -> Optional[str]:
    """
    從請求中取得使用者 ID（由 AuthenticationMiddleware 設定）
    
    符合 AC-023-4：在 API 層級驗證權限，防止未授權存取
    
    Args:
        request: FastAPI Request
    
    Returns:
        Optional[str]: 使用者 ID
    
    Raises:
        HTTPException: 當未提供使用者資訊時
    """
    if hasattr(request.state, "user_id"):
        return request.state.user_id
    
    # 如果中介軟體未設定使用者 ID，表示未通過身份驗證
    raise HTTPException(
        status_code=401,
        detail="未提供使用者資訊",
    )


def require_role(*roles: RoleName):
    """
    角色授權裝飾器
    
    符合 AC-023-4：在 API 層級驗證權限，防止未授權存取
    
    Args:
        *roles: 允許的角色名稱（可多個）
    
    Returns:
        Callable: 裝飾器函數
    """
    role_names = [role.value for role in roles]
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            request: Request,
            authorization_service: AuthorizationService = Depends(get_authorization_service),
            *args,
            **kwargs,
        ):
            # 取得使用者 ID
            user_id = get_current_user_id(request)
            
            if not user_id:
                raise HTTPException(
                    status_code=401,
                    detail="未提供使用者資訊",
                )
            
            # 取得 IP 和 User-Agent
            ip_address = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
            user_agent = request.headers.get("User-Agent")
            
            # 檢查角色
            has_role = False
            for role_name in role_names:
                if await authorization_service.check_role(
                    user_id=user_id,
                    role_name=role_name,
                    resource_type=func.__name__,
                    ip_address=ip_address,
                    user_agent=user_agent,
                ):
                    has_role = True
                    break
            
            if not has_role:
                raise HTTPException(
                    status_code=403,
                    detail=f"需要以下角色之一：{', '.join(role_names)}",
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_permission(*permissions: PermissionName):
    """
    權限授權裝飾器
    
    符合 AC-023-4：在 API 層級驗證權限，防止未授權存取
    
    Args:
        *permissions: 允許的權限名稱（可多個）
    
    Returns:
        Callable: 裝飾器函數
    """
    permission_names = [permission.value for permission in permissions]
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            request: Request,
            authorization_service: AuthorizationService = Depends(get_authorization_service),
            *args,
            **kwargs,
        ):
            # 取得使用者 ID
            user_id = get_current_user_id(request)
            
            if not user_id:
                raise HTTPException(
                    status_code=401,
                    detail="未提供使用者資訊",
                )
            
            # 取得 IP 和 User-Agent
            ip_address = request.headers.get("X-Forwarded-For", request.client.host if request.client else None)
            user_agent = request.headers.get("User-Agent")
            
            # 檢查權限
            has_permission = False
            for permission_name in permission_names:
                if await authorization_service.check_permission(
                    user_id=user_id,
                    permission=permission_name,
                    resource_type=func.__name__,
                    ip_address=ip_address,
                    user_agent=user_agent,
                ):
                    has_permission = True
                    break
            
            if not has_permission:
                raise HTTPException(
                    status_code=403,
                    detail=f"需要以下權限之一：{', '.join(permission_names)}",
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator

