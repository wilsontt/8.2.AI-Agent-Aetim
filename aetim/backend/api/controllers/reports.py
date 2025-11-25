"""
報告控制器

提供報告相關的 API 端點。
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
    Path,
    Request,
    Body,
)
from fastapi.responses import Response
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from shared_kernel.infrastructure.database import get_db
from reporting_notification.application.services.report_service import ReportService
from reporting_notification.domain.value_objects.file_format import FileFormat
from reporting_notification.domain.value_objects.report_type import ReportType
from reporting_notification.domain.value_objects.ticket_status import TicketStatus
from reporting_notification.domain.domain_services.report_generation_service import (
    ReportGenerationService,
)
from reporting_notification.domain.interfaces.report_repository import IReportRepository
from reporting_notification.infrastructure.persistence.report_repository import (
    ReportRepository,
)
from reporting_notification.infrastructure.external_services.ai_summary_service import (
    AISummaryService,
)
from reporting_notification.infrastructure.services.template_renderer import (
    TemplateRenderer,
)
from threat_intelligence.domain.interfaces.threat_repository import IThreatRepository
from threat_intelligence.infrastructure.persistence.threat_repository import (
    ThreatRepository,
)
from analysis_assessment.domain.interfaces.risk_assessment_repository import (
    IRiskAssessmentRepository,
)
from analysis_assessment.infrastructure.persistence.risk_assessment_repository import (
    RiskAssessmentRepository,
)
from asset_management.domain.interfaces.asset_repository import IAssetRepository
from asset_management.infrastructure.persistence.asset_repository import AssetRepository
from threat_intelligence.infrastructure.persistence.threat_asset_association_repository import (
    ThreatAssetAssociationRepository,
)
from pydantic import BaseModel

router = APIRouter()


def get_report_service(db: AsyncSession = Depends(get_db)) -> ReportService:
    """
    取得報告服務（依賴注入）
    
    Args:
        db: 資料庫會話
    
    Returns:
        ReportService: 報告服務實例
    """
    # 建立 Repository 實例
    report_repository = ReportRepository(db)
    threat_repository = ThreatRepository(db)
    risk_assessment_repository = RiskAssessmentRepository(db)
    asset_repository = AssetRepository(db)
    threat_asset_association_repository = ThreatAssetAssociationRepository(db)
    
    # 建立 Domain Service
    report_generation_service = ReportGenerationService(
        threat_repository=threat_repository,
        risk_assessment_repository=risk_assessment_repository,
        asset_repository=asset_repository,
        threat_asset_association_repository=threat_asset_association_repository,
    )
    
    # 建立 Infrastructure Service
    ai_summary_service = AISummaryService(
        base_url="http://localhost:8001",  # TODO: 從設定檔讀取
        timeout=30,
    )
    template_renderer = TemplateRenderer()
    
    # 建立 Application Service
    return ReportService(
        report_generation_service=report_generation_service,
        report_repository=report_repository,
        ai_summary_service=ai_summary_service,
        threat_asset_association_repository=threat_asset_association_repository,
        asset_repository=asset_repository,
        template_renderer=template_renderer,
    )


@router.get("/")
async def list_reports():
    """取得報告清單"""
    # TODO: 實作報告清單查詢
    return {"reports": []}


@router.get("/{report_id}")
async def get_report(report_id: str):
    """取得單一報告"""
    # TODO: 實作報告查詢
    return {"report_id": report_id}


@router.get("/tickets/{ticket_id}/export")
async def export_ticket(
    ticket_id: str = Path(..., description="工單 ID"),
    format: Optional[str] = Query(None, description="檔案格式（TEXT/JSON）"),
    request: Request = None,
    report_service: ReportService = Depends(get_report_service),
):
    """
    匯出單一工單（AC-017-4）
    
    Args:
        ticket_id: 工單 ID
        format: 檔案格式（可選，TEXT 或 JSON）
        request: FastAPI Request 物件（用於取得 IP 位址和 User Agent）
        report_service: 報告服務
    
    Returns:
        Response: 檔案下載回應
    """
    try:
        # 決定檔案格式
        file_format = None
        if format:
            try:
                file_format = FileFormat.from_string(format.upper())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"無效的檔案格式：{format}",
                )
        
        # 取得使用者資訊（暫時使用預設值，未來可從認證系統取得）
        user_id = None  # TODO: 從認證系統取得
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        # 匯出工單
        export_result = await report_service.export_ticket(
            ticket_id=ticket_id,
            file_format=file_format,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # 返回檔案下載回應
        return Response(
            content=export_result["file_content"],
            media_type=export_result["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{export_result["file_name"]}"',
            },
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"匯出工單失敗：{str(e)}",
        )


class BatchExportRequest(BaseModel):
    """批次匯出請求 DTO"""
    ticket_ids: List[str]


@router.post("/tickets/export-batch")
async def export_tickets_batch(
    request_body: BatchExportRequest,
    request: Request = None,
    report_service: ReportService = Depends(get_report_service),
):
    """
    批次匯出工單（AC-018-1, AC-018-2）
    
    Args:
        request_body: 批次匯出請求（包含工單 ID 清單）
        request: FastAPI Request 物件（用於取得 IP 位址和 User Agent）
        report_service: 報告服務
    
    Returns:
        Response: JSON 檔案下載回應
    """
    try:
        # 取得使用者資訊（暫時使用預設值，未來可從認證系統取得）
        user_id = None  # TODO: 從認證系統取得
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        # 批次匯出工單
        export_result = await report_service.export_tickets_batch(
            ticket_ids=request_body.ticket_ids,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        # 返回檔案下載回應
        return Response(
            content=export_result["file_content"],
            media_type=export_result["content_type"],
            headers={
                "Content-Disposition": f'attachment; filename="{export_result["file_name"]}"',
            },
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批次匯出工單失敗：{str(e)}",
        )


class UpdateTicketStatusRequest(BaseModel):
    """更新工單狀態請求 DTO"""
    status: str = Field(..., description="新狀態（待處理/處理中/已完成/已關閉）")


@router.put("/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: str = Path(..., description="工單 ID"),
    request_body: UpdateTicketStatusRequest = Body(...),
    request: Request = None,
    report_service: ReportService = Depends(get_report_service),
):
    """
    更新工單狀態（AC-017-5）
    
    Args:
        ticket_id: 工單 ID
        request_body: 更新狀態請求（包含新狀態）
        request: FastAPI Request 物件（用於取得 IP 位址和 User Agent）
        report_service: 報告服務
    
    Returns:
        Dict: 更新結果
    """
    try:
        # 解析狀態
        try:
            new_status = TicketStatus.from_string(request_body.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"無效的工單狀態：{request_body.status}",
            )
        
        # 取得使用者資訊（暫時使用預設值，未來可從認證系統取得）
        user_id = None  # TODO: 從認證系統取得
        ip_address = request.client.host if request else None
        user_agent = request.headers.get("user-agent") if request else None
        
        # 更新工單狀態
        report = await report_service.update_ticket_status(
            ticket_id=ticket_id,
            new_status=new_status,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        return {
            "success": True,
            "ticket_id": ticket_id,
            "status": report.ticket_status.value if report.ticket_status else None,
            "message": "工單狀態已更新",
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新工單狀態失敗：{str(e)}",
        )

