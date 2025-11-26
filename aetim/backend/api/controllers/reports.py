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
from datetime import datetime

router = APIRouter()


class ReportListResponse(BaseModel):
    """報告清單回應"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


class ReportDetailResponse(BaseModel):
    """報告詳細回應"""
    id: str
    report_type: str
    title: str
    file_path: Optional[str] = None
    file_format: str
    metadata: Optional[Dict[str, Any]] = None
    ticket_status: Optional[str] = None
    created_at: str
    updated_at: str
    created_by: str


class GenerateReportRequest(BaseModel):
    """生成報告請求"""
    report_type: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    file_format: Optional[str] = "HTML"


class GenerateReportResponse(BaseModel):
    """生成報告回應"""
    report_id: str
    status: str
    message: Optional[str] = None


class ReportContentResponse(BaseModel):
    """報告內容回應"""
    content: str


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


@router.get("/", response_model=ReportListResponse)
async def list_reports(
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁數量"),
    report_type: Optional[str] = Query(None, description="報告類型"),
    file_format: Optional[str] = Query(None, description="檔案格式"),
    ticket_status: Optional[str] = Query(None, description="工單狀態"),
    start_date: Optional[str] = Query(None, description="開始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="結束日期（YYYY-MM-DD）"),
    sort_by: str = Query("generated_at", description="排序欄位"),
    sort_order: str = Query("desc", description="排序順序（asc/desc）"),
    report_service: ReportService = Depends(get_report_service),
):
    """
    取得報告清單
    
    Args:
        page: 頁碼
        page_size: 每頁數量
        report_type: 報告類型篩選
        file_format: 檔案格式篩選
        ticket_status: 工單狀態篩選
        start_date: 開始日期篩選
        end_date: 結束日期篩選
        sort_by: 排序欄位
        sort_order: 排序順序
        report_service: 報告服務
    
    Returns:
        ReportListResponse: 報告清單回應
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
        
        # 解析檔案格式
        file_format_enum = None
        if file_format:
            try:
                file_format_enum = FileFormat.from_string(file_format)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"無效的檔案格式：{file_format}",
                )
        
        # 解析工單狀態
        ticket_status_enum = None
        if ticket_status:
            try:
                ticket_status_enum = TicketStatus.from_string(ticket_status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"無效的工單狀態：{ticket_status}",
                )
        
        # 解析日期
        start_date_obj = None
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"無效的開始日期格式：{start_date}，應為 YYYY-MM-DD",
                )
        
        end_date_obj = None
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"無效的結束日期格式：{end_date}，應為 YYYY-MM-DD",
                )
        
        # 查詢報告
        result = await report_service.get_reports(
            report_type=report_type_enum,
            file_format=file_format_enum,
            ticket_status=ticket_status_enum,
            start_date=start_date_obj,
            end_date=end_date_obj,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        
        # 轉換為回應格式
        items = []
        for report in result["items"]:
            items.append({
                "id": report.id,
                "report_type": report.report_type.value,
                "title": report.title,
                "file_path": report.file_path,
                "file_format": report.file_format.value,
                "metadata": report.metadata,
                "ticket_status": report.ticket_status.value if report.ticket_status else None,
                "created_at": report.generated_at.isoformat() if report.generated_at else report.created_at.isoformat(),
                "updated_at": report.updated_at.isoformat(),
                "created_by": report.created_by,
            })
        
        return ReportListResponse(
            items=items,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢報告清單失敗：{str(e)}",
        )


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: str = Path(..., description="報告 ID"),
    report_service: ReportService = Depends(get_report_service),
):
    """
    取得單一報告
    
    Args:
        report_id: 報告 ID
        report_service: 報告服務
    
    Returns:
        ReportDetailResponse: 報告詳細回應
    """
    try:
        report = await report_service.get_report_by_id(report_id)
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到報告：{report_id}",
            )
        
        return ReportDetailResponse(
            id=report.id,
            report_type=report.report_type.value,
            title=report.title,
            file_path=report.file_path,
            file_format=report.file_format.value,
            metadata=report.metadata,
            ticket_status=report.ticket_status.value if report.ticket_status else None,
            created_at=report.generated_at.isoformat() if report.generated_at else report.created_at.isoformat(),
            updated_at=report.updated_at.isoformat(),
            created_by=report.created_by,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢報告失敗：{str(e)}",
        )


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


@router.post("/generate", response_model=GenerateReportResponse)
async def generate_report(
    request_body: GenerateReportRequest = Body(...),
    report_service: ReportService = Depends(get_report_service),
):
    """
    生成報告
    
    Args:
        request_body: 生成報告請求
        report_service: 報告服務
    
    Returns:
        GenerateReportResponse: 生成報告回應
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
        
        # 解析檔案格式
        file_format = FileFormat.HTML
        if request_body.file_format:
            try:
                file_format = FileFormat.from_string(request_body.file_format)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"無效的檔案格式：{request_body.file_format}",
                )
        
        # 生成報告
        if report_type == ReportType.CISO_WEEKLY:
            # 解析日期範圍
            period_start = datetime.utcnow()
            period_end = datetime.utcnow()
            
            if request_body.start_date:
                try:
                    period_start = datetime.strptime(request_body.start_date, "%Y-%m-%d")
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"無效的開始日期格式：{request_body.start_date}",
                    )
            
            if request_body.end_date:
                try:
                    period_end = datetime.strptime(request_body.end_date, "%Y-%m-%d")
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"無效的結束日期格式：{request_body.end_date}",
                    )
            
            report = await report_service.generate_ciso_weekly_report(
                period_start=period_start,
                period_end=period_end,
                file_format=file_format,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支援的報告類型：{report_type.value}",
            )
        
        return GenerateReportResponse(
            report_id=report.id,
            status="success",
            message="報告生成成功",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成報告失敗：{str(e)}",
        )


@router.get("/{report_id}/download")
async def download_report(
    report_id: str = Path(..., description="報告 ID"),
    format: Optional[str] = Query(None, description="檔案格式（可選）"),
    report_service: ReportService = Depends(get_report_service),
):
    """
    下載報告檔案
    
    Args:
        report_id: 報告 ID
        format: 檔案格式（可選）
        report_service: 報告服務
    
    Returns:
        Response: 檔案下載回應
    """
    try:
        # 解析檔案格式
        file_format = None
        if format:
            try:
                file_format = FileFormat.from_string(format.upper())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"無效的檔案格式：{format}",
                )
        
        # 取得報告檔案內容
        file_content = await report_service.download_report(report_id, file_format)
        
        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到報告檔案：{report_id}",
            )
        
        # 取得報告資訊以決定 Content-Type
        report = await report_service.get_report_by_id(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到報告：{report_id}",
            )
        
        target_format = file_format or report.file_format
        content_type_map = {
            FileFormat.HTML: "text/html",
            FileFormat.PDF: "application/pdf",
            FileFormat.TEXT: "text/plain",
            FileFormat.JSON: "application/json",
        }
        content_type = content_type_map.get(target_format, "application/octet-stream")
        
        return Response(
            content=file_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{report.title}.{target_format.get_file_extension()}"',
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下載報告失敗：{str(e)}",
        )


@router.get("/{report_id}/content", response_model=ReportContentResponse)
async def get_report_content(
    report_id: str = Path(..., description="報告 ID"),
    report_service: ReportService = Depends(get_report_service),
):
    """
    取得報告內容（用於預覽）
    
    Args:
        report_id: 報告 ID
        report_service: 報告服務
    
    Returns:
        ReportContentResponse: 報告內容回應
    """
    try:
        content = await report_service.get_report_content(report_id)
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"找不到報告內容：{report_id}",
            )
        
        return ReportContentResponse(content=content)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢報告內容失敗：{str(e)}",
        )

