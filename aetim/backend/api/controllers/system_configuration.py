"""
系統設定 API 控制器

提供系統設定管理的 API 端點。
符合 AC-024-1, AC-024-2, AC-024-3, AC-024-4, AC-024-5。
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from system_management.application.services.system_configuration_service import (
    SystemConfigurationService,
)
from system_management.application.dtos.system_configuration_dto import (
    SystemConfigurationDTO,
    SystemConfigurationUpdateRequest,
    SystemConfigurationBatchUpdateRequest,
    SystemConfigurationListResponse,
)
from system_management.infrastructure.persistence.system_configuration_repository import (
    SystemConfigurationRepository,
)
from system_management.infrastructure.persistence.audit_log_repository import (
    AuditLogRepository,
)
from system_management.infrastructure.decorators.authorization import (
    require_permission,
    get_current_user_id,
)
from system_management.domain.value_objects.permission_name import PermissionName
from shared_kernel.infrastructure.database import get_db
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/system-configurations", tags=["系統設定"])


def get_system_configuration_service(
    db_session: AsyncSession = Depends(get_db),
) -> SystemConfigurationService:
    """
    取得系統設定服務
    
    Args:
        db_session: 資料庫 Session
    
    Returns:
        SystemConfigurationService: 系統設定服務
    """
    repository = SystemConfigurationRepository(db_session)
    audit_log_repository = AuditLogRepository(db_session)
    return SystemConfigurationService(repository, audit_log_repository)


def get_client_ip(request: Request) -> Optional[str]:
    """
    取得客戶端 IP 位址
    
    Args:
        request: HTTP 請求
    
    Returns:
        Optional[str]: IP 位址
    """
    return request.headers.get("X-Forwarded-For", request.client.host if request.client else None)


@router.get("", response_model=SystemConfigurationListResponse)
@require_permission(PermissionName.SYSTEM_CONFIG_VIEW)
async def get_configurations(
    category: Optional[str] = None,
    service: SystemConfigurationService = Depends(get_system_configuration_service),
):
    """
    取得系統設定清單
    
    符合 AC-024-1：提供系統設定的集中管理介面
    
    Args:
        category: 設定類別（可選）
        service: 系統設定服務
    
    Returns:
        SystemConfigurationListResponse: 系統設定清單
    """
    configs = await service.get_configuration(category=category)
    
    if isinstance(configs, list):
        return SystemConfigurationListResponse(
            configurations=[
                SystemConfigurationDTO.model_validate(config) for config in configs
            ],
            total=len(configs),
        )
    else:
        return SystemConfigurationListResponse(
            configurations=[],
            total=0,
        )


@router.get("/{key}", response_model=SystemConfigurationDTO)
@require_permission(PermissionName.SYSTEM_CONFIG_VIEW)
async def get_configuration(
    key: str,
    service: SystemConfigurationService = Depends(get_system_configuration_service),
):
    """
    取得單一系統設定
    
    符合 AC-024-1：提供系統設定的集中管理介面
    
    Args:
        key: 設定鍵
        service: 系統設定服務
    
    Returns:
        SystemConfigurationDTO: 系統設定
    
    Raises:
        HTTPException: 當設定不存在時
    """
    config = await service.get_configuration(key=key)
    
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"系統設定 '{key}' 不存在",
        )
    
    return SystemConfigurationDTO.model_validate(config)


@router.put("/{key}", response_model=SystemConfigurationDTO)
@require_permission(PermissionName.SYSTEM_CONFIG_UPDATE)
async def update_configuration(
    key: str,
    request_data: SystemConfigurationUpdateRequest,
    http_request: Request,
    service: SystemConfigurationService = Depends(get_system_configuration_service),
):
    """
    更新系統設定
    
    符合 AC-024-3：在儲存設定前要求使用者確認（明確的交易儲存）
    符合 AC-024-5：記錄所有設定變更的稽核日誌
    
    Args:
        key: 設定鍵
        request_data: 更新請求資料
        http_request: HTTP 請求
        service: 系統設定服務
    
    Returns:
        SystemConfigurationDTO: 更新後的系統設定
    
    Raises:
        HTTPException: 當設定鍵不匹配時
    """
    if key != request_data.key:
        raise HTTPException(
            status_code=400,
            detail="URL 中的設定鍵與請求資料不匹配",
        )
    
    # 取得使用者 ID
    user_id = get_current_user_id(http_request)
    
    # 取得 IP 和 User-Agent
    ip_address = get_client_ip(http_request)
    user_agent = http_request.headers.get("User-Agent")
    
    config = await service.update_configuration(
        key=request_data.key,
        value=request_data.value,
        description=request_data.description,
        category=request_data.category or "general",
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return SystemConfigurationDTO.model_validate(config)


@router.post("/batch", response_model=List[SystemConfigurationDTO])
@require_permission(PermissionName.SYSTEM_CONFIG_UPDATE)
async def update_configurations_batch(
    request_data: SystemConfigurationBatchUpdateRequest,
    http_request: Request,
    service: SystemConfigurationService = Depends(get_system_configuration_service),
):
    """
    批次更新系統設定
    
    符合 AC-024-3：在儲存設定前要求使用者確認（明確的交易儲存）
    符合 AC-024-5：記錄所有設定變更的稽核日誌
    
    Args:
        request_data: 批次更新請求資料
        http_request: HTTP 請求
        service: 系統設定服務
    
    Returns:
        List[SystemConfigurationDTO]: 更新後的系統設定清單
    """
    # 取得使用者 ID
    user_id = get_current_user_id(http_request)
    
    # 取得 IP 和 User-Agent
    ip_address = get_client_ip(http_request)
    user_agent = http_request.headers.get("User-Agent")
    
    configs = await service.update_configurations_batch(
        configurations=[
            {
                "key": config.key,
                "value": config.value,
                "description": config.description,
                "category": config.category or "general",
            }
            for config in request_data.configurations
        ],
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return [SystemConfigurationDTO.model_validate(config) for config in configs]


@router.delete("/{key}")
@require_permission(PermissionName.SYSTEM_CONFIG_UPDATE)
async def delete_configuration(
    key: str,
    http_request: Request,
    service: SystemConfigurationService = Depends(get_system_configuration_service),
):
    """
    刪除系統設定
    
    符合 AC-024-5：記錄所有設定變更的稽核日誌
    
    Args:
        key: 設定鍵
        http_request: HTTP 請求
        service: 系統設定服務
    
    Returns:
        dict: 刪除結果
    
    Raises:
        HTTPException: 當設定不存在時
    """
    # 取得使用者 ID
    user_id = get_current_user_id(http_request)
    
    # 取得 IP 和 User-Agent
    ip_address = get_client_ip(http_request)
    user_agent = http_request.headers.get("User-Agent")
    
    success = await service.delete_configuration(
        key=key,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"系統設定 '{key}' 不存在",
        )
    
    return {"message": "系統設定已刪除", "key": key}

