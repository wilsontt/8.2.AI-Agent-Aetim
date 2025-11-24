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
from datetime import datetime
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
from analysis_assessment.application.services.threat_asset_association_service import (
    ThreatAssetAssociationService,
)
from analysis_assessment.application.dtos.association_dto import (
    AssociationAnalysisResponse,
    ThreatAssociationListResponse,
    ThreatAssetAssociationResponse,
    AssociationAnalysisLogResponse,
)
from analysis_assessment.application.dtos.risk_assessment_dto import (
    RiskCalculationResponse,
    RiskAssessmentDetailResponse,
    RiskAssessmentHistoryListResponse,
    RiskAssessmentHistoryResponse,
)
from analysis_assessment.application.services.risk_assessment_service import (
    RiskAssessmentService,
)
from analysis_assessment.domain.domain_services.association_analysis_service import (
    AssociationAnalysisService,
)
from analysis_assessment.domain.domain_services.risk_calculation_service import (
    RiskCalculationService,
)
from analysis_assessment.domain.domain_services.cvss_score_calculator import (
    CVSSScoreCalculator,
)
from analysis_assessment.domain.domain_services.weight_factor_calculator import (
    WeightFactorCalculator,
)
from analysis_assessment.domain.domain_services.risk_level_classifier import (
    RiskLevelClassifier,
)
from analysis_assessment.domain.domain_services.product_name_matcher import ProductNameMatcher
from analysis_assessment.domain.domain_services.version_matcher import VersionMatcher
from analysis_assessment.domain.interfaces.risk_assessment_repository import (
    IRiskAssessmentRepository,
)
from analysis_assessment.domain.interfaces.risk_assessment_history_repository import (
    IRiskAssessmentHistoryRepository,
)
from analysis_assessment.domain.interfaces.pir_repository import IPIRRepository
from analysis_assessment.infrastructure.persistence.risk_assessment_repository import (
    RiskAssessmentRepository,
)
from analysis_assessment.infrastructure.persistence.risk_assessment_history_repository import (
    RiskAssessmentHistoryRepository,
)
from analysis_assessment.infrastructure.persistence.pir_repository import PIRRepository
from threat_intelligence.infrastructure.persistence.threat_feed_repository import (
    ThreatFeedRepository,
)
from asset_management.infrastructure.persistence.asset_repository import AssetRepository

logger = get_logger(__name__)
router = APIRouter()


def get_risk_assessment_service(
    db: AsyncSession = Depends(get_db),
) -> RiskAssessmentService:
    """
    取得風險評估服務
    
    Args:
        db: 資料庫 Session
    
    Returns:
        RiskAssessmentService: 風險評估服務
    """
    threat_repository = ThreatRepository(db)
    threat_feed_repository = ThreatFeedRepository(db)
    asset_repository = AssetRepository(db)
    pir_repository = PIRRepository(db)
    risk_assessment_repository = RiskAssessmentRepository(db)
    history_repository = RiskAssessmentHistoryRepository(db)
    association_repository = ThreatAssetAssociationRepository(db)
    
    # 建立風險計算服務
    cvss_calculator = CVSSScoreCalculator()
    weight_calculator = WeightFactorCalculator()
    risk_classifier = RiskLevelClassifier()
    risk_calculation_service = RiskCalculationService(
        cvss_calculator=cvss_calculator,
        weight_calculator=weight_calculator,
        risk_classifier=risk_classifier,
    )
    
    return RiskAssessmentService(
        risk_calculation_service=risk_calculation_service,
        threat_repository=threat_repository,
        threat_feed_repository=threat_feed_repository,
        asset_repository=asset_repository,
        pir_repository=pir_repository,
        risk_assessment_repository=risk_assessment_repository,
        history_repository=history_repository,
        association_repository=association_repository,
    )


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


def get_threat_asset_association_service(
    db: AsyncSession = Depends(get_db),
) -> ThreatAssetAssociationService:
    """
    取得威脅-資產關聯服務
    
    Args:
        db: 資料庫 Session
    
    Returns:
        ThreatAssetAssociationService: 威脅-資產關聯服務
    """
    threat_repository = ThreatRepository(db)
    asset_repository = AssetRepository(db)
    association_repository = ThreatAssetAssociationRepository(db)
    product_name_matcher = ProductNameMatcher()
    version_matcher = VersionMatcher()
    association_analysis_service = AssociationAnalysisService(
        product_name_matcher=product_name_matcher,
        version_matcher=version_matcher,
    )
    return ThreatAssetAssociationService(
        threat_repository=threat_repository,
        asset_repository=asset_repository,
        association_repository=association_repository,
        association_analysis_service=association_analysis_service,
    )


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


@router.post(
    "/{threat_id}/analyze",
    response_model=AssociationAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="執行關聯分析",
    description="執行威脅與資產的關聯分析，並建立關聯記錄（AC-010-1 至 AC-010-4）",
    responses={
        200: {"description": "分析成功"},
        404: {"description": "威脅不存在"},
        500: {"description": "分析失敗"},
    },
)
async def analyze_threat_associations(
    threat_id: str = Path(..., description="威脅 ID"),
    association_service: ThreatAssetAssociationService = Depends(get_threat_asset_association_service),
) -> AssociationAnalysisResponse:
    """
    執行關聯分析（AC-010-1 至 AC-010-4）
    
    - **threat_id**: 威脅 ID
    
    此端點會：
    1. 執行威脅與所有資產的關聯分析
    2. 建立威脅-資產關聯記錄
    3. 更新威脅狀態為「已處理」
    
    回應包含：
    - 是否成功
    - 建立的關聯數量
    - 錯誤訊息列表（如果有）
    """
    try:
        result = await association_service.analyze_and_create_associations(threat_id)
        
        return AssociationAnalysisResponse(
            success=result["success"],
            threat_id=result["threat_id"],
            associations_created=result["associations_created"],
            errors=result.get("errors", []),
        )
        
    except ValueError as e:
        # 威脅不存在
        logger.warning(
            f"威脅不存在：{threat_id}",
            extra={"threat_id": threat_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"威脅不存在：{threat_id}",
        )
    except Exception as e:
        logger.error(
            f"執行關聯分析失敗：{str(e)}",
            extra={"threat_id": threat_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"執行關聯分析失敗：{str(e)}",
        )


@router.get(
    "/{threat_id}/associations",
    response_model=ThreatAssociationListResponse,
    status_code=status.HTTP_200_OK,
    summary="查詢威脅的關聯",
    description="查詢威脅的所有關聯資產（AC-011-1），支援分頁、排序、篩選",
    responses={
        200: {"description": "查詢成功"},
        404: {"description": "威脅不存在"},
    },
)
async def get_threat_associations(
    threat_id: str = Path(..., description="威脅 ID"),
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁筆數"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="最小信心分數"),
    match_type: Optional[str] = Query(None, description="匹配類型篩選"),
    sort_by: Optional[str] = Query("match_confidence", description="排序欄位（match_confidence, created_at）"),
    sort_order: str = Query("desc", description="排序順序（asc, desc）"),
    association_service: ThreatAssetAssociationService = Depends(get_threat_asset_association_service),
) -> ThreatAssociationListResponse:
    """
    查詢威脅的關聯（AC-011-1）
    
    - **threat_id**: 威脅 ID
    - **page**: 頁碼（預設 1）
    - **page_size**: 每頁筆數（預設 20，最大 100）
    - **min_confidence**: 最小信心分數（可選，0.0-1.0）
    - **match_type**: 匹配類型篩選（可選）
    - **sort_by**: 排序欄位（match_confidence, created_at，預設 match_confidence）
    - **sort_order**: 排序順序（asc 或 desc，預設 desc）
    
    回應包含：
    - 關聯清單
    - 分頁資訊
    """
    try:
        # 取得所有關聯
        associations = await association_service.get_associations_by_threat_id(threat_id)
        
        # 篩選
        filtered_associations = associations
        if min_confidence is not None:
            filtered_associations = [
                a for a in filtered_associations
                if a["match_confidence"] >= min_confidence
            ]
        if match_type:
            filtered_associations = [
                a for a in filtered_associations
                if a["match_type"] == match_type
            ]
        
        # 排序
        reverse = sort_order.lower() == "desc"
        if sort_by == "match_confidence":
            filtered_associations.sort(key=lambda x: x["match_confidence"], reverse=reverse)
        elif sort_by == "created_at":
            filtered_associations.sort(
                key=lambda x: x["created_at"] or datetime.min,
                reverse=reverse
            )
        
        # 分頁
        total = len(filtered_associations)
        total_pages = (total + page_size - 1) // page_size
        start = (page - 1) * page_size
        end = start + page_size
        paginated_associations = filtered_associations[start:end]
        
        # 轉換為回應格式
        association_responses = [
            ThreatAssetAssociationResponse(
                id=assoc["id"],
                threat_id=assoc["threat_id"],
                asset_id=assoc["asset_id"],
                match_confidence=assoc["match_confidence"],
                match_type=assoc["match_type"],
                match_details=assoc["match_details"],
                created_at=datetime.fromisoformat(assoc["created_at"]) if assoc["created_at"] else None,
            )
            for assoc in paginated_associations
        ]
        
        return ThreatAssociationListResponse(
            items=association_responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
        
    except Exception as e:
        logger.error(
            f"查詢威脅關聯失敗：{str(e)}",
            extra={"threat_id": threat_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢威脅關聯失敗：{str(e)}",
        )


@router.get(
    "/{threat_id}/associations/analysis-log",
    response_model=AssociationAnalysisLogResponse,
    status_code=status.HTTP_200_OK,
    summary="查詢分析日誌",
    description="查詢關聯分析的執行日誌（AC-010-5）",
    responses={
        200: {"description": "查詢成功"},
        404: {"description": "威脅不存在"},
    },
)
async def get_association_analysis_log(
    threat_id: str = Path(..., description="威脅 ID"),
    db: AsyncSession = Depends(get_db),
    association_service: ThreatAssetAssociationService = Depends(get_threat_asset_association_service),
) -> AssociationAnalysisLogResponse:
    """
    查詢分析日誌（AC-010-5）
    
    - **threat_id**: 威脅 ID
    
    回應包含：
    - 分析開始時間
    - 分析完成時間
    - 建立的關聯數量
    - 錯誤訊息列表
    - 分析狀態
    """
    try:
        # 取得威脅以判斷狀態
        threat_service = get_threat_service(db)
        threat_result = await threat_service.get_threat_by_id(threat_id)
        
        if not threat_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"威脅不存在：{threat_id}",
            )
        
        # 取得關聯
        associations = await association_service.get_associations_by_threat_id(threat_id)
        
        # 判斷分析狀態
        threat_status = threat_result.status
        if threat_status == "Processed":
            analysis_status = "completed"
        elif threat_status == "Analyzing":
            analysis_status = "in_progress"
        else:
            analysis_status = "not_started"
        
        return AssociationAnalysisLogResponse(
            threat_id=threat_id,
            associations_created=len(associations),
            status=analysis_status,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"查詢分析日誌失敗：{str(e)}",
            extra={"threat_id": threat_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢分析日誌失敗：{str(e)}",
        )


@router.post(
    "/{threat_id}/calculate-risk",
    response_model=RiskCalculationResponse,
    status_code=status.HTTP_200_OK,
    summary="計算風險分數",
    description="計算威脅的風險分數（AC-012-1 至 AC-012-5）",
    responses={
        200: {"description": "計算成功"},
        404: {"description": "威脅不存在"},
        500: {"description": "計算失敗"},
    },
)
async def calculate_risk(
    threat_id: str = Path(..., description="威脅 ID"),
    risk_service: RiskAssessmentService = Depends(get_risk_assessment_service),
    db: AsyncSession = Depends(get_db),
) -> RiskCalculationResponse:
    """
    計算風險分數（AC-012-1 至 AC-012-5）
    
    - **threat_id**: 威脅 ID
    
    此端點會：
    1. 計算威脅的風險分數（考慮所有加權因子）
    2. 儲存風險評估
    3. 儲存歷史記錄
    
    回應包含：
    - 是否成功
    - 風險評估 ID
    - 最終風險分數
    - 風險等級
    - 計算時間
    """
    try:
        # 取得威脅以驗證存在
        threat_service = get_threat_service(db)
        threat = await threat_service.get_threat_by_id(threat_id)
        if not threat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"威脅不存在：{threat_id}",
            )
        
        # 取得威脅的第一個關聯（用於建立風險評估）
        association_service = get_threat_asset_association_service(db)
        associations = await association_service.get_associations_by_threat_id(threat_id)
        
        # 使用第一個關聯的 ID，如果沒有關聯則使用臨時 ID
        # 注意：如果沒有關聯，風險評估仍然可以計算（只是沒有資產加權）
        threat_asset_association_id = (
            associations[0]["id"] if associations and len(associations) > 0 else f"temp-{threat_id}"
        )
        
        # 計算並儲存風險評估
        risk_assessment = await risk_service.calculate_and_save_risk(
            threat_id=threat_id,
            threat_asset_association_id=threat_asset_association_id,
        )
        
        return RiskCalculationResponse(
            success=True,
            threat_id=threat_id,
            risk_assessment_id=risk_assessment.id,
            final_risk_score=risk_assessment.final_risk_score,
            risk_level=risk_assessment.risk_level,
            calculated_at=risk_assessment.created_at,
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        error_msg = str(e)
        logger.warning(
            f"計算風險分數失敗：{error_msg}",
            extra={"threat_id": threat_id, "error": error_msg}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )
    except Exception as e:
        logger.error(
            f"計算風險分數失敗：{str(e)}",
            extra={"threat_id": threat_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"計算風險分數失敗：{str(e)}",
        )


@router.get(
    "/{threat_id}/risk-assessment",
    response_model=RiskAssessmentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="查詢風險評估",
    description="查詢威脅的風險評估詳情（AC-013-1, AC-013-2）",
    responses={
        200: {"description": "查詢成功"},
        404: {"description": "威脅不存在或沒有風險評估"},
        500: {"description": "查詢失敗"},
    },
)
async def get_risk_assessment(
    threat_id: str = Path(..., description="威脅 ID"),
    risk_service: RiskAssessmentService = Depends(get_risk_assessment_service),
) -> RiskAssessmentDetailResponse:
    """
    查詢風險評估詳情（AC-013-1, AC-013-2）
    
    - **threat_id**: 威脅 ID
    
    回應包含：
    - 基礎 CVSS 分數
    - 各加權因子的貢獻（資產重要性、受影響數量、PIR 符合度、CISA KEV）
    - 最終風險分數
    - 風險等級
    - 計算公式說明
    """
    try:
        risk_assessment = await risk_service.get_risk_assessment_by_threat_id(threat_id)
        
        if not risk_assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"威脅 {threat_id} 沒有風險評估記錄",
            )
        
        # 解析計算公式
        calculation_formula = None
        if risk_assessment.calculation_details:
            calculation_formula = risk_assessment.calculation_details.get(
                "calculation_formula"
            )
        
        return RiskAssessmentDetailResponse(
            id=risk_assessment.id,
            threat_id=risk_assessment.threat_id,
            threat_asset_association_id=risk_assessment.threat_asset_association_id,
            base_cvss_score=risk_assessment.base_cvss_score,
            asset_importance_weight=risk_assessment.asset_importance_weight,
            affected_asset_count=risk_assessment.affected_asset_count,
            asset_count_weight=risk_assessment.asset_count_weight,
            pir_match_weight=risk_assessment.pir_match_weight,
            cisa_kev_weight=risk_assessment.cisa_kev_weight,
            final_risk_score=risk_assessment.final_risk_score,
            risk_level=risk_assessment.risk_level,
            calculation_details=risk_assessment.calculation_details,
            calculation_formula=calculation_formula,
            created_at=risk_assessment.created_at,
            updated_at=risk_assessment.updated_at,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"查詢風險評估失敗：{str(e)}",
            extra={"threat_id": threat_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢風險評估失敗：{str(e)}",
        )


@router.get(
    "/{threat_id}/risk-assessment/history",
    response_model=RiskAssessmentHistoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="查詢風險評估歷史",
    description="查詢威脅的風險評估歷史記錄（AC-013-3）",
    responses={
        200: {"description": "查詢成功"},
        404: {"description": "威脅不存在或沒有風險評估"},
        500: {"description": "查詢失敗"},
    },
)
async def get_risk_assessment_history(
    threat_id: str = Path(..., description="威脅 ID"),
    start_time: Optional[datetime] = Query(
        None, description="開始時間（ISO 8601 格式）"
    ),
    end_time: Optional[datetime] = Query(
        None, description="結束時間（ISO 8601 格式）"
    ),
    risk_service: RiskAssessmentService = Depends(get_risk_assessment_service),
) -> RiskAssessmentHistoryListResponse:
    """
    查詢風險評估歷史記錄（AC-013-3）
    
    - **threat_id**: 威脅 ID
    - **start_time**: 開始時間（可選，ISO 8601 格式）
    - **end_time**: 結束時間（可選，ISO 8601 格式）
    
    回應包含：
    - 歷史記錄清單
    - 總數
    """
    try:
        # 先取得風險評估
        risk_assessment = await risk_service.get_risk_assessment_by_threat_id(threat_id)
        
        if not risk_assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"威脅 {threat_id} 沒有風險評估記錄",
            )
        
        # 查詢歷史記錄
        histories = await risk_service.get_risk_assessment_history(
            risk_assessment_id=risk_assessment.id,
            start_time=start_time,
            end_time=end_time,
        )
        
        # 轉換為回應格式
        history_responses = []
        for history in histories:
            calculation_details = None
            if history.get("calculation_details"):
                try:
                    import json
                    calculation_details = json.loads(history["calculation_details"])
                except (json.JSONDecodeError, TypeError):
                    calculation_details = None
            
            history_responses.append(
                RiskAssessmentHistoryResponse(
                    id=history["id"],
                    risk_assessment_id=history["risk_assessment_id"],
                    base_cvss_score=history["base_cvss_score"],
                    asset_importance_weight=history["asset_importance_weight"],
                    asset_count_weight=history["asset_count_weight"],
                    pir_match_weight=history.get("pir_match_weight"),
                    cisa_kev_weight=history.get("cisa_kev_weight"),
                    final_risk_score=history["final_risk_score"],
                    risk_level=history["risk_level"],
                    calculation_details=calculation_details,
                    calculated_at=datetime.fromisoformat(history["calculated_at"])
                    if history.get("calculated_at")
                    else datetime.utcnow(),
                )
            )
        
        return RiskAssessmentHistoryListResponse(
            items=history_responses,
            total=len(history_responses),
            threat_id=threat_id,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"查詢風險評估歷史失敗：{str(e)}",
            extra={"threat_id": threat_id, "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢風險評估歷史失敗：{str(e)}",
        )
