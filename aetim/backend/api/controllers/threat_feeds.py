"""
威脅情資來源管理控制器

提供威脅情資來源管理相關的 API 端點。
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from fastapi.responses import JSONResponse
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from shared_kernel.infrastructure.database import get_db
from shared_kernel.infrastructure.logging import get_logger
from threat_intelligence.application.services.threat_feed_service import ThreatFeedService
from threat_intelligence.application.dtos.threat_feed_dto import (
    CreateThreatFeedRequest,
    UpdateThreatFeedRequest,
    ThreatFeedResponse,
    ThreatFeedListResponse,
    CollectionStatusResponse,
)
from threat_intelligence.infrastructure.persistence.threat_feed_repository import ThreatFeedRepository

logger = get_logger(__name__)
router = APIRouter()


def get_threat_feed_service(db: AsyncSession = Depends(get_db)) -> ThreatFeedService:
    """
    取得威脅情資來源服務
    
    Args:
        db: 資料庫 Session
    
    Returns:
        ThreatFeedService: 威脅情資來源服務
    """
    repository = ThreatFeedRepository(db)
    return ThreatFeedService(repository)


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_threat_feed(
    request: CreateThreatFeedRequest,
    service: ThreatFeedService = Depends(get_threat_feed_service),
    user_id: str = "system",  # TODO: 從認證中介軟體取得
) -> dict:
    """
    建立威脅情資來源
    
    Args:
        request: 建立威脅情資來源請求
        service: 威脅情資來源服務
        user_id: 使用者 ID（預設 "system"）
    
    Returns:
        dict: 包含威脅情資來源 ID 的回應
    
    Raises:
        HTTPException: 當輸入參數無效時
    """
    try:
        threat_feed_id = await service.create_threat_feed(request, user_id=user_id)
        return {"id": threat_feed_id, "message": "威脅情資來源建立成功"}
    except ValueError as e:
        logger.warning("建立威脅情資來源失敗", extra={"error": str(e), "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e)},
        )
    except Exception as e:
        logger.error("建立威脅情資來源時發生錯誤", extra={"error": str(e), "user_id": user_id}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "建立威脅情資來源時發生內部錯誤"},
        )


@router.get("", response_model=ThreatFeedListResponse)
async def get_threat_feeds(
    page: int = Query(1, ge=1, description="頁碼（從 1 開始）"),
    page_size: int = Query(20, ge=1, le=100, description="每頁筆數"),
    sort_by: Optional[str] = Query(None, description="排序欄位（name、priority、created_at 等）"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="排序方向（asc/desc）"),
    service: ThreatFeedService = Depends(get_threat_feed_service),
) -> ThreatFeedListResponse:
    """
    查詢威脅情資來源清單（支援分頁、排序）
    
    Args:
        page: 頁碼（從 1 開始）
        page_size: 每頁筆數（預設 20，最大 100）
        sort_by: 排序欄位
        sort_order: 排序方向（asc/desc）
        service: 威脅情資來源服務
    
    Returns:
        ThreatFeedListResponse: 威脅情資來源清單回應
    """
    try:
        return await service.get_threat_feeds(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except ValueError as e:
        logger.warning("查詢威脅情資來源清單失敗", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e)},
        )
    except Exception as e:
        logger.error("查詢威脅情資來源清單時發生錯誤", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "查詢威脅情資來源清單時發生內部錯誤"},
        )


@router.get("/{threat_feed_id}", response_model=ThreatFeedResponse)
async def get_threat_feed_by_id(
    threat_feed_id: str,
    service: ThreatFeedService = Depends(get_threat_feed_service),
) -> ThreatFeedResponse:
    """
    查詢威脅情資來源詳情
    
    Args:
        threat_feed_id: 威脅情資來源 ID
        service: 威脅情資來源服務
    
    Returns:
        ThreatFeedResponse: 威脅情資來源回應
    
    Raises:
        HTTPException: 當威脅情資來源不存在時
    """
    try:
        threat_feed = await service.get_threat_feed_by_id(threat_feed_id)
        if not threat_feed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": f"威脅情資來源 ID {threat_feed_id} 不存在"},
            )
        return threat_feed
    except HTTPException:
        raise
    except Exception as e:
        logger.error("查詢威脅情資來源詳情時發生錯誤", extra={"error": str(e), "threat_feed_id": threat_feed_id}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "查詢威脅情資來源詳情時發生內部錯誤"},
        )


@router.put("/{threat_feed_id}", response_model=dict)
async def update_threat_feed(
    threat_feed_id: str,
    request: UpdateThreatFeedRequest,
    service: ThreatFeedService = Depends(get_threat_feed_service),
    user_id: str = "system",  # TODO: 從認證中介軟體取得
) -> dict:
    """
    更新威脅情資來源
    
    Args:
        threat_feed_id: 威脅情資來源 ID
        request: 更新威脅情資來源請求
        service: 威脅情資來源服務
        user_id: 使用者 ID（預設 "system"）
    
    Returns:
        dict: 成功回應
    
    Raises:
        HTTPException: 當威脅情資來源不存在或輸入參數無效時
    """
    try:
        await service.update_threat_feed(threat_feed_id, request, user_id=user_id)
        return {"id": threat_feed_id, "message": "威脅情資來源更新成功"}
    except ValueError as e:
        logger.warning("更新威脅情資來源失敗", extra={"error": str(e), "threat_feed_id": threat_feed_id, "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e)},
        )
    except Exception as e:
        logger.error("更新威脅情資來源時發生錯誤", extra={"error": str(e), "threat_feed_id": threat_feed_id, "user_id": user_id}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "更新威脅情資來源時發生內部錯誤"},
        )


@router.delete("/{threat_feed_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_threat_feed(
    threat_feed_id: str,
    service: ThreatFeedService = Depends(get_threat_feed_service),
    user_id: str = "system",  # TODO: 從認證中介軟體取得
) -> None:
    """
    刪除威脅情資來源
    
    Args:
        threat_feed_id: 威脅情資來源 ID
        service: 威脅情資來源服務
        user_id: 使用者 ID（預設 "system"）
    
    Raises:
        HTTPException: 當威脅情資來源不存在時
    """
    try:
        await service.delete_threat_feed(threat_feed_id, user_id=user_id)
    except ValueError as e:
        logger.warning("刪除威脅情資來源失敗", extra={"error": str(e), "threat_feed_id": threat_feed_id, "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": str(e)},
        )
    except Exception as e:
        logger.error("刪除威脅情資來源時發生錯誤", extra={"error": str(e), "threat_feed_id": threat_feed_id, "user_id": user_id}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "刪除威脅情資來源時發生內部錯誤"},
        )


@router.patch("/{threat_feed_id}/toggle", response_model=dict)
async def toggle_threat_feed(
    threat_feed_id: str,
    service: ThreatFeedService = Depends(get_threat_feed_service),
    user_id: str = "system",  # TODO: 從認證中介軟體取得
) -> dict:
    """
    切換威脅情資來源啟用狀態
    
    Args:
        threat_feed_id: 威脅情資來源 ID
        service: 威脅情資來源服務
        user_id: 使用者 ID（預設 "system"）
    
    Returns:
        dict: 包含更新後狀態的回應
    
    Raises:
        HTTPException: 當威脅情資來源不存在時
    """
    try:
        await service.toggle_threat_feed(threat_feed_id, user_id=user_id)
        
        # 取得更新後的威脅情資來源以回傳狀態
        threat_feed = await service.get_threat_feed_by_id(threat_feed_id)
        if not threat_feed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": f"威脅情資來源 ID {threat_feed_id} 不存在"},
            )
        
        return {
            "id": threat_feed_id,
            "is_enabled": threat_feed.is_enabled,
            "message": f"威脅情資來源已{'啟用' if threat_feed.is_enabled else '停用'}",
        }
    except ValueError as e:
        logger.warning("切換威脅情資來源啟用狀態失敗", extra={"error": str(e), "threat_feed_id": threat_feed_id, "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": str(e)},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("切換威脅情資來源啟用狀態時發生錯誤", extra={"error": str(e), "threat_feed_id": threat_feed_id, "user_id": user_id}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "切換威脅情資來源啟用狀態時發生內部錯誤"},
        )


@router.get("/{threat_feed_id}/status", response_model=CollectionStatusResponse)
async def get_collection_status(
    threat_feed_id: str,
    service: ThreatFeedService = Depends(get_threat_feed_service),
) -> CollectionStatusResponse:
    """
    查詢威脅情資來源的收集狀態
    
    Args:
        threat_feed_id: 威脅情資來源 ID
        service: 威脅情資來源服務
    
    Returns:
        CollectionStatusResponse: 收集狀態回應
    
    Raises:
        HTTPException: 當威脅情資來源不存在時
    """
    try:
        statuses = await service.get_collection_status(threat_feed_id=threat_feed_id)
        if not statuses:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": f"威脅情資來源 ID {threat_feed_id} 不存在"},
            )
        return statuses[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("查詢收集狀態時發生錯誤", extra={"error": str(e), "threat_feed_id": threat_feed_id}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "查詢收集狀態時發生內部錯誤"},
        )


@router.get("/status/list", response_model=list[CollectionStatusResponse])
async def get_all_collection_status(
    service: ThreatFeedService = Depends(get_threat_feed_service),
) -> list[CollectionStatusResponse]:
    """
    查詢所有啟用的威脅情資來源的收集狀態
    
    Args:
        service: 威脅情資來源服務
    
    Returns:
        list[CollectionStatusResponse]: 收集狀態清單
    """
    try:
        return await service.get_collection_status()
    except Exception as e:
        logger.error("查詢所有收集狀態時發生錯誤", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "查詢所有收集狀態時發生內部錯誤"},
        )

