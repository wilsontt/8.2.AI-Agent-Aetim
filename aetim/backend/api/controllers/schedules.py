"""
排程控制器

提供週報排程相關的 API 端點。
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
    Path,
    Body,
)
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from datetime import datetime

from shared_kernel.infrastructure.database import get_db
from reporting_notification.infrastructure.persistence.report_schedule_repository import (
    ReportScheduleRepository,
)
from reporting_notification.domain.value_objects.report_type import ReportType

router = APIRouter()


class ScheduleResponse(BaseModel):
    """排程回應 DTO"""
    id: str
    report_type: str
    cron_expression: str
    is_enabled: bool
    recipients: List[str]
    file_format: str
    timezone: str
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    created_at: str
    updated_at: str


class ScheduleListResponse(BaseModel):
    """排程列表回應 DTO"""
    items: List[ScheduleResponse]
    total: int


class CreateScheduleRequest(BaseModel):
    """建立排程請求 DTO"""
    report_type: str = Field(..., description="報告類型（CISO_Weekly/IT_Ticket）")
    cron_expression: str = Field(..., description="Cron 表達式（例如：0 9 * * 1）")
    recipients: List[str] = Field(..., description="收件人清單")
    file_format: str = Field(default="HTML", description="檔案格式（HTML/PDF）")
    timezone: str = Field(default="Asia/Taipei", description="時區設定")
    is_enabled: bool = Field(default=True, description="是否啟用")


class UpdateScheduleRequest(BaseModel):
    """更新排程請求 DTO"""
    cron_expression: Optional[str] = Field(None, description="Cron 表達式")
    recipients: Optional[List[str]] = Field(None, description="收件人清單")
    file_format: Optional[str] = Field(None, description="檔案格式")
    timezone: Optional[str] = Field(None, description="時區設定")
    is_enabled: Optional[bool] = Field(None, description="是否啟用")


def get_schedule_repository(db: AsyncSession = Depends(get_db)) -> ReportScheduleRepository:
    """取得排程 Repository"""
    return ReportScheduleRepository(db)


def _schedule_to_response(schedule) -> ScheduleResponse:
    """轉換 Schedule 領域模型為回應 DTO"""
    return ScheduleResponse(
        id=schedule.id,
        report_type=schedule.report_type.value,
        cron_expression=schedule.cron_expression,
        is_enabled=schedule.is_enabled,
        recipients=schedule.recipients,
        file_format=schedule.file_format,
        timezone=schedule.timezone,
        last_run_at=schedule.last_run_at.isoformat() if schedule.last_run_at else None,
        next_run_at=schedule.next_run_at.isoformat() if schedule.next_run_at else None,
        created_at=schedule.created_at.isoformat(),
        updated_at=schedule.updated_at.isoformat(),
    )


@router.get("/", response_model=ScheduleListResponse)
async def list_schedules(
    report_type: Optional[str] = Query(None, description="報告類型篩選"),
    repository: ReportScheduleRepository = Depends(get_schedule_repository),
):
    """
    取得排程列表
    
    Args:
        report_type: 報告類型篩選（可選）
        repository: 排程 Repository
    
    Returns:
        ScheduleListResponse: 排程列表回應
    """
    try:
        # 解析報告類型
        report_type_enum = None
        if report_type:
            try:
                report_type_enum = ReportType.from_string(report_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"無效的報告類型：{report_type}",
                )
        
        # 查詢排程
        if report_type_enum:
            schedules = await repository.get_by_report_type(report_type_enum)
        else:
            schedules = await repository.get_all_enabled()
            # 也包含未啟用的排程
            disabled = await repository.get_all()
            schedules = disabled  # 返回所有排程
        
        # 轉換為回應格式
        items = [_schedule_to_response(schedule) for schedule in schedules]
        
        return ScheduleListResponse(
            items=items,
            total=len(items),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢排程列表失敗：{str(e)}",
        )


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: str = Path(..., description="排程 ID"),
    repository: ReportScheduleRepository = Depends(get_schedule_repository),
):
    """
    取得單一排程詳情
    
    Args:
        schedule_id: 排程 ID
        repository: 排程 Repository
    
    Returns:
        ScheduleResponse: 排程詳情回應
    """
    try:
        schedule = await repository.get_by_id(schedule_id)
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到排程：{schedule_id}",
            )
        
        return _schedule_to_response(schedule)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢排程失敗：{str(e)}",
        )


@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    request_body: CreateScheduleRequest = Body(...),
    repository: ReportScheduleRepository = Depends(get_schedule_repository),
):
    """
    建立新排程
    
    Args:
        request_body: 建立排程請求
        repository: 排程 Repository
    
    Returns:
        ScheduleResponse: 建立的排程
    """
    try:
        # 解析報告類型
        try:
            report_type = ReportType.from_string(request_body.report_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"無效的報告類型：{request_body.report_type}",
            )
        
        # 導入 ReportSchedule
        from reporting_notification.domain.aggregates.report_schedule import ReportSchedule
        
        # 建立排程
        schedule = ReportSchedule.create(
            report_type=report_type,
            cron_expression=request_body.cron_expression,
            recipients=request_body.recipients,
            file_format=request_body.file_format,
            timezone=request_body.timezone,
            is_enabled=request_body.is_enabled,
        )
        
        # 儲存到資料庫
        await repository.save(schedule)
        
        return _schedule_to_response(schedule)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"建立排程失敗：{str(e)}",
        )


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str = Path(..., description="排程 ID"),
    request_body: UpdateScheduleRequest = Body(...),
    repository: ReportScheduleRepository = Depends(get_schedule_repository),
):
    """
    更新排程
    
    Args:
        schedule_id: 排程 ID
        request_body: 更新排程請求
        repository: 排程 Repository
    
    Returns:
        ScheduleResponse: 更新後的排程
    """
    try:
        # 取得現有排程
        schedule = await repository.get_by_id(schedule_id)
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到排程：{schedule_id}",
            )
        
        # 更新排程
        schedule.update_schedule(
            cron_expression=request_body.cron_expression,
            recipients=request_body.recipients,
            file_format=request_body.file_format,
            timezone=request_body.timezone,
            is_enabled=request_body.is_enabled,
        )
        
        # 儲存到資料庫
        await repository.save(schedule)
        
        return _schedule_to_response(schedule)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新排程失敗：{str(e)}",
        )


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: str = Path(..., description="排程 ID"),
    repository: ReportScheduleRepository = Depends(get_schedule_repository),
):
    """
    刪除排程
    
    Args:
        schedule_id: 排程 ID
        repository: 排程 Repository
    """
    try:
        # 檢查排程是否存在
        schedule = await repository.get_by_id(schedule_id)
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到排程：{schedule_id}",
            )
        
        # 刪除排程
        await repository.delete(schedule_id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除排程失敗：{str(e)}",
        )
