"""
威脅管理控制器

提供威脅管理相關的 API 端點。
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
    Path,
)
from fastapi.responses import JSONResponse
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from shared_kernel.infrastructure.database import get_db
from shared_kernel.infrastructure.logging import get_logger
from threat_intelligence.application.services.threat_service import ThreatService
from threat_intelligence.application.dtos.threat_dto import (
    ThreatResponse,
    ThreatListResponse,
    ThreatSearchParams,
    ThreatListParams,
    UpdateThreatStatusRequest,
    ThreatDetailResponse,
)
from threat_intelligence.infrastructure.persistence.threat_repository import ThreatRepository
from threat_intelligence.infrastructure.persistence.threat_asset_association_repository import (
    ThreatAssetAssociationRepository,
)

logger = get_logger(__name__)
router = APIRouter()


def get_threat_service(db: AsyncSession = Depends(get_db)) -> ThreatService:
    """
    取得威脅服務
    
    Args:
        db: 資料庫 Session
    
    Returns:
        ThreatService: 威脅服務
    """
    threat_repository = ThreatRepository(db)
    association_repository = ThreatAssetAssociationRepository(db)
    return ThreatService(threat_repository, association_repository)


@router.get(
    "",
    response_model=ThreatListResponse,
    status_code=status.HTTP_200_OK,
    summary="查詢威脅清單",
    description="查詢威脅清單，支援分頁、排序、篩選",
    responses={
        200: {"description": "查詢成功"},
        400: {"description": "請求參數錯誤"},
    },
)
async def get_threats(
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(100, ge=1, le=1000, description="每頁筆數"),
    status: Optional[str] = Query(None, description="狀態篩選（New, Analyzing, Processed, Closed）"),
    threat_feed_id: Optional[str] = Query(None, description="威脅情資來源 ID 篩選"),
    cve_id: Optional[str] = Query(None, description="CVE 編號篩選"),
    product_name: Optional[str] = Query(None, description="產品名稱篩選"),
    min_cvss_score: Optional[float] = Query(None, ge=0.0, le=10.0, description="最小 CVSS 分數"),
    max_cvss_score: Optional[float] = Query(None, ge=0.0, le=10.0, description="最大 CVSS 分數"),
    sort_by: Optional[str] = Query(None, description="排序欄位（created_at, updated_at, cvss_base_score, published_date）"),
    sort_order: str = Query("desc", description="排序順序（asc, desc）"),
    threat_service: ThreatService = Depends(get_threat_service),
) -> ThreatListResponse:
    """
    查詢威脅清單
    
    - **page**: 頁碼（預設 1）
    - **page_size**: 每頁筆數（預設 100，最大 1000）
    - **status**: 狀態篩選（可選）
    - **threat_feed_id**: 威脅情資來源 ID 篩選（可選）
    - **cve_id**: CVE 編號篩選（可選）
    - **product_name**: 產品名稱篩選（可選）
    - **min_cvss_score**: 最小 CVSS 分數（可選，0.0-10.0）
    - **max_cvss_score**: 最大 CVSS 分數（可選，0.0-10.0）
    - **sort_by**: 排序欄位（可選）
    - **sort_order**: 排序順序（asc 或 desc，預設 desc）
    """
    try:
        result = await threat_service.get_threats(
            page=page,
            page_size=page_size,
            status=status,
            threat_feed_id=threat_feed_id,
            cve_id=cve_id,
            product_name=product_name,
            min_cvss_score=min_cvss_score,
            max_cvss_score=max_cvss_score,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        
        # 轉換為回應格式
        threat_responses = [
            ThreatResponse(
                id=threat.id,
                threat_feed_id=threat.threat_feed_id,
                title=threat.title,
                description=threat.description,
                cve_id=threat.cve_id,
                cvss_base_score=threat.cvss_base_score,
                cvss_vector=threat.cvss_vector,
                severity=threat.severity.value if threat.severity else None,
                status=threat.status.value,
                source_url=threat.source_url,
                published_date=threat.published_date,
                collected_at=threat.collected_at,
                products=[
                    {
                        "id": p.id,
                        "product_name": p.product_name,
                        "product_version": p.product_version,
                        "product_type": p.product_type,
                        "original_text": p.original_text,
                    }
                    for p in threat.products
                ],
                ttps=threat.ttps,
                iocs=threat.iocs,
                created_at=threat.created_at,
                updated_at=threat.updated_at,
            )
            for threat in result["items"]
        ]
        
        return ThreatListResponse(
            items=threat_responses,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )
        
    except Exception as e:
        logger.error(
            f"查詢威脅清單失敗：{str(e)}",
            extra={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢威脅清單失敗：{str(e)}",
        )


@router.get(
    "/{threat_id}",
    response_model=ThreatDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="查詢威脅詳情",
    description="查詢威脅詳情，包含關聯的資產清單",
    responses={
        200: {"description": "查詢成功"},
        404: {"description": "威脅不存在"},
    },
)
async def get_threat_by_id(
    threat_id: str = Path(..., description="威脅 ID"),
    threat_service: ThreatService = Depends(get_threat_service),
) -> ThreatDetailResponse:
    """
    查詢威脅詳情
    
    - **threat_id**: 威脅 ID
    
    回應包含：
    - 完整威脅資訊
    - 關聯的資產清單
    """
    try:
        result = await threat_service.get_threat_with_associations(threat_id)
        
        threat = result["threat"]
        threat_response = ThreatResponse(
            id=threat.id,
            threat_feed_id=threat.threat_feed_id,
            title=threat.title,
            description=threat.description,
            cve_id=threat.cve_id,
            cvss_base_score=threat.cvss_base_score,
            cvss_vector=threat.cvss_vector,
            severity=threat.severity.value if threat.severity else None,
            status=threat.status.value,
            source_url=threat.source_url,
            published_date=threat.published_date,
            collected_at=threat.collected_at,
            products=[
                {
                    "id": p.id,
                    "product_name": p.product_name,
                    "product_version": p.product_version,
                    "product_type": p.product_type,
                    "original_text": p.original_text,
                }
                for p in threat.products
            ],
            ttps=threat.ttps,
            iocs=threat.iocs,
            created_at=threat.created_at,
            updated_at=threat.updated_at,
        )
        
        return ThreatDetailResponse(
            threat=threat_response,
            associated_assets=result["associated_assets"],
        )
        
    except ValueError as e:
        logger.warning(
            f"威脅不存在：{threat_id}",
            extra={"threat_id": threat_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"查詢威脅詳情失敗：{str(e)}",
            extra={"threat_id": threat_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢威脅詳情失敗：{str(e)}",
        )


@router.get(
    "/search",
    response_model=ThreatListResponse,
    status_code=status.HTTP_200_OK,
    summary="搜尋威脅",
    description="全文搜尋威脅（標題、描述）",
    responses={
        200: {"description": "搜尋成功"},
        400: {"description": "請求參數錯誤"},
    },
)
async def search_threats(
    query: str = Query(..., min_length=1, description="搜尋關鍵字"),
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(100, ge=1, le=1000, description="每頁筆數"),
    threat_service: ThreatService = Depends(get_threat_service),
) -> ThreatListResponse:
    """
    搜尋威脅
    
    - **query**: 搜尋關鍵字（必填，至少 1 個字元）
    - **page**: 頁碼（預設 1）
    - **page_size**: 每頁筆數（預設 100，最大 1000）
    
    在威脅的標題和描述中搜尋關鍵字。
    """
    try:
        result = await threat_service.search_threats(
            query=query,
            page=page,
            page_size=page_size,
        )
        
        # 轉換為回應格式
        threat_responses = [
            ThreatResponse(
                id=threat.id,
                threat_feed_id=threat.threat_feed_id,
                title=threat.title,
                description=threat.description,
                cve_id=threat.cve_id,
                cvss_base_score=threat.cvss_base_score,
                cvss_vector=threat.cvss_vector,
                severity=threat.severity.value if threat.severity else None,
                status=threat.status.value,
                source_url=threat.source_url,
                published_date=threat.published_date,
                collected_at=threat.collected_at,
                products=[
                    {
                        "id": p.id,
                        "product_name": p.product_name,
                        "product_version": p.product_version,
                        "product_type": p.product_type,
                        "original_text": p.original_text,
                    }
                    for p in threat.products
                ],
                ttps=threat.ttps,
                iocs=threat.iocs,
                created_at=threat.created_at,
                updated_at=threat.updated_at,
            )
            for threat in result["items"]
        ]
        
        return ThreatListResponse(
            items=threat_responses,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )
        
    except Exception as e:
        logger.error(
            f"搜尋威脅失敗：{str(e)}",
            extra={"query": query, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜尋威脅失敗：{str(e)}",
        )


@router.put(
    "/{threat_id}/status",
    response_model=ThreatResponse,
    status_code=status.HTTP_200_OK,
    summary="更新威脅狀態",
    description="更新威脅狀態（AC-014-3）",
    responses={
        200: {"description": "更新成功"},
        400: {"description": "請求參數錯誤或狀態轉換不合法"},
        404: {"description": "威脅不存在"},
    },
)
async def update_threat_status(
    threat_id: str = Path(..., description="威脅 ID"),
    request: UpdateThreatStatusRequest = ...,
    threat_service: ThreatService = Depends(get_threat_service),
) -> ThreatResponse:
    """
    更新威脅狀態（AC-014-3）
    
    - **threat_id**: 威脅 ID
    - **status**: 新狀態（New, Analyzing, Processed, Closed）
    
    狀態轉換規則：
    - New -> Analyzing, Processed, Closed
    - Analyzing -> Processed, Closed
    - Processed -> Closed
    - Closed -> （不可轉換）
    """
    try:
        threat = await threat_service.update_threat_status(
            threat_id=threat_id,
            new_status=request.status,
        )
        
        return ThreatResponse(
            id=threat.id,
            threat_feed_id=threat.threat_feed_id,
            title=threat.title,
            description=threat.description,
            cve_id=threat.cve_id,
            cvss_base_score=threat.cvss_base_score,
            cvss_vector=threat.cvss_vector,
            severity=threat.severity.value if threat.severity else None,
            status=threat.status.value,
            source_url=threat.source_url,
            published_date=threat.published_date,
            collected_at=threat.collected_at,
            products=[
                {
                    "id": p.id,
                    "product_name": p.product_name,
                    "product_version": p.product_version,
                    "product_type": p.product_type,
                    "original_text": p.original_text,
                }
                for p in threat.products
            ],
            ttps=threat.ttps,
            iocs=threat.iocs,
            created_at=threat.created_at,
            updated_at=threat.updated_at,
        )
        
    except ValueError as e:
        error_msg = str(e)
        if "找不到威脅" in error_msg:
            logger.warning(
                f"威脅不存在：{threat_id}",
                extra={"threat_id": threat_id, "error": error_msg}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            )
        else:
            # 狀態轉換不合法
            logger.warning(
                f"狀態轉換不合法：{threat_id} -> {request.status}",
                extra={"threat_id": threat_id, "new_status": request.status, "error": error_msg}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg,
            )
    except Exception as e:
        logger.error(
            f"更新威脅狀態失敗：{str(e)}",
            extra={"threat_id": threat_id, "new_status": request.status, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新威脅狀態失敗：{str(e)}",
        )
