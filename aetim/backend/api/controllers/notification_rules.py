"""
通知規則控制器

提供通知規則管理的 API 端點。
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Path,
    Request,
    Body,
)
from typing import List, Optional
from datetime import time
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from shared_kernel.infrastructure.database import get_db
from reporting_notification.application.services.notification_rule_service import (
    NotificationRuleService,
)
from reporting_notification.domain.value_objects.notification_type import NotificationType
from reporting_notification.infrastructure.persistence.notification_rule_repository import (
    NotificationRuleRepository,
)

router = APIRouter()


def get_notification_rule_service(
    db: AsyncSession = Depends(get_db),
) -> NotificationRuleService:
    """
    取得通知規則服務（依賴注入）
    
    Args:
        db: 資料庫會話
    
    Returns:
        NotificationRuleService: 通知規則服務實例
    """
    # 建立 Repository 實例
    repository = NotificationRuleRepository(db)
    
    # TODO: 注入 AuditLogService
    audit_log_service = None
    
    # 建立 Application Service
    return NotificationRuleService(
        repository=repository,
        audit_log_service=audit_log_service,
    )


class CreateNotificationRuleRequest(BaseModel):
    """建立通知規則請求 DTO"""
    notification_type: str = Field(..., description="通知類型（Critical/HighRiskDaily/Weekly）")
    recipients: List[str] = Field(..., description="收件人清單（Email 地址）")
    risk_score_threshold: Optional[float] = Field(None, ge=0.0, le=10.0, description="風險分數閾值")
    send_time: Optional[str] = Field(None, description="發送時間（HH:MM 格式）")
    is_enabled: bool = Field(True, description="是否啟用")


class UpdateNotificationRuleRequest(BaseModel):
    """更新通知規則請求 DTO"""
    recipients: Optional[List[str]] = Field(None, description="收件人清單（Email 地址）")
    risk_score_threshold: Optional[float] = Field(None, ge=0.0, le=10.0, description="風險分數閾值")
    send_time: Optional[str] = Field(None, description="發送時間（HH:MM 格式）")
    is_enabled: Optional[bool] = Field(None, description="是否啟用")


class NotificationRuleResponse(BaseModel):
    """通知規則回應 DTO"""
    id: str
    notification_type: str
    is_enabled: bool
    recipients: List[str]
    risk_score_threshold: Optional[float]
    send_time: Optional[str]
    created_at: str
    updated_at: str
    created_by: str
    updated_by: str


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_notification_rule(
    request_body: CreateNotificationRuleRequest = Body(...),
    request: Request = None,
    service: NotificationRuleService = Depends(get_notification_rule_service),
):
    """
    建立通知規則（AC-021-1）
    
    Args:
        request_body: 建立通知規則請求
        request: FastAPI Request 物件（用於取得 IP 位址和 User Agent）
        service: 通知規則服務
    
    Returns:
        NotificationRuleResponse: 建立的通知規則
    """
    try:
        # 解析通知類型
        try:
            notification_type = NotificationType.from_string(request_body.notification_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"無效的通知類型：{request_body.notification_type}",
            )
        
        # 解析發送時間
        send_time_obj = None
        if request_body.send_time:
            try:
                hour, minute = request_body.send_time.split(":")
                send_time_obj = time(int(hour), int(minute))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"無效的發送時間格式：{request_body.send_time}，應為 HH:MM",
                )
        
        # 取得使用者資訊（暫時使用預設值，未來可從認證系統取得）
        user_id = None  # TODO: 從認證系統取得
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        # 建立通知規則
        rule = await service.create_rule(
            notification_type=notification_type,
            recipients=request_body.recipients,
            risk_score_threshold=request_body.risk_score_threshold,
            send_time=send_time_obj,
            is_enabled=request_body.is_enabled,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return NotificationRuleResponse(
            id=rule.id,
            notification_type=rule.notification_type.value,
            is_enabled=rule.is_enabled,
            recipients=rule.recipients,
            risk_score_threshold=rule.risk_score_threshold,
            send_time=rule.send_time.strftime("%H:%M") if rule.send_time else None,
            created_at=rule.created_at.isoformat(),
            updated_at=rule.updated_at.isoformat(),
            created_by=rule.created_by,
            updated_by=rule.updated_by,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"建立通知規則失敗：{str(e)}",
        )


@router.get("/", response_model=List[NotificationRuleResponse])
async def get_notification_rules(
    service: NotificationRuleService = Depends(get_notification_rule_service),
):
    """
    查詢通知規則清單
    
    Args:
        service: 通知規則服務
    
    Returns:
        List[NotificationRuleResponse]: 通知規則清單
    """
    try:
        rules = await service.get_rules()
        
        return [
            NotificationRuleResponse(
                id=rule.id,
                notification_type=rule.notification_type.value,
                is_enabled=rule.is_enabled,
                recipients=rule.recipients,
                risk_score_threshold=rule.risk_score_threshold,
                send_time=rule.send_time.strftime("%H:%M") if rule.send_time else None,
                created_at=rule.created_at.isoformat(),
                updated_at=rule.updated_at.isoformat(),
                created_by=rule.created_by,
                updated_by=rule.updated_by,
            )
            for rule in rules
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢通知規則清單失敗：{str(e)}",
        )


@router.get("/{rule_id}", response_model=NotificationRuleResponse)
async def get_notification_rule(
    rule_id: str = Path(..., description="通知規則 ID"),
    service: NotificationRuleService = Depends(get_notification_rule_service),
):
    """
    依 ID 查詢通知規則
    
    Args:
        rule_id: 通知規則 ID
        service: 通知規則服務
    
    Returns:
        NotificationRuleResponse: 通知規則
    """
    try:
        rule = await service.get_rule_by_id(rule_id)
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到通知規則：{rule_id}",
            )
        
        return NotificationRuleResponse(
            id=rule.id,
            notification_type=rule.notification_type.value,
            is_enabled=rule.is_enabled,
            recipients=rule.recipients,
            risk_score_threshold=rule.risk_score_threshold,
            send_time=rule.send_time.strftime("%H:%M") if rule.send_time else None,
            created_at=rule.created_at.isoformat(),
            updated_at=rule.updated_at.isoformat(),
            created_by=rule.created_by,
            updated_by=rule.updated_by,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢通知規則失敗：{str(e)}",
        )


@router.put("/{rule_id}")
async def update_notification_rule(
    rule_id: str = Path(..., description="通知規則 ID"),
    request_body: UpdateNotificationRuleRequest = Body(...),
    request: Request = None,
    service: NotificationRuleService = Depends(get_notification_rule_service),
):
    """
    更新通知規則（AC-021-2, AC-021-3）
    
    Args:
        rule_id: 通知規則 ID
        request_body: 更新通知規則請求
        request: FastAPI Request 物件（用於取得 IP 位址和 User Agent）
        service: 通知規則服務
    
    Returns:
        NotificationRuleResponse: 更新後的通知規則
    """
    try:
        # 解析發送時間
        send_time_obj = None
        if request_body.send_time:
            try:
                hour, minute = request_body.send_time.split(":")
                send_time_obj = time(int(hour), int(minute))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"無效的發送時間格式：{request_body.send_time}，應為 HH:MM",
                )
        
        # 取得使用者資訊（暫時使用預設值，未來可從認證系統取得）
        user_id = None  # TODO: 從認證系統取得
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        # 更新通知規則
        rule = await service.update_rule(
            rule_id=rule_id,
            recipients=request_body.recipients,
            risk_score_threshold=request_body.risk_score_threshold,
            send_time=send_time_obj,
            is_enabled=request_body.is_enabled,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return NotificationRuleResponse(
            id=rule.id,
            notification_type=rule.notification_type.value,
            is_enabled=rule.is_enabled,
            recipients=rule.recipients,
            risk_score_threshold=rule.risk_score_threshold,
            send_time=rule.send_time.strftime("%H:%M") if rule.send_time else None,
            created_at=rule.created_at.isoformat(),
            updated_at=rule.updated_at.isoformat(),
            created_by=rule.created_by,
            updated_by=rule.updated_by,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新通知規則失敗：{str(e)}",
        )


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_rule(
    rule_id: str = Path(..., description="通知規則 ID"),
    request: Request = None,
    service: NotificationRuleService = Depends(get_notification_rule_service),
):
    """
    刪除通知規則
    
    Args:
        rule_id: 通知規則 ID
        request: FastAPI Request 物件（用於取得 IP 位址和 User Agent）
        service: 通知規則服務
    """
    try:
        # 取得使用者資訊（暫時使用預設值，未來可從認證系統取得）
        user_id = None  # TODO: 從認證系統取得
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        # 刪除通知規則
        await service.delete_rule(
            rule_id=rule_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除通知規則失敗：{str(e)}",
        )

