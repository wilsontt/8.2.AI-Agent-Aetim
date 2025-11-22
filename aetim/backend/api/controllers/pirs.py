"""
PIR 管理控制器

提供 PIR 管理相關的 API 端點。
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
from analysis_assessment.application.services.pir_service import PIRService
from analysis_assessment.application.dtos.pir_dto import (
    CreatePIRRequest,
    UpdatePIRRequest,
    PIRResponse,
    PIRListResponse,
)
from analysis_assessment.infrastructure.persistence.pir_repository import PIRRepository

logger = get_logger(__name__)
router = APIRouter()


def get_pir_service(db: AsyncSession = Depends(get_db)) -> PIRService:
    """
    取得 PIR 服務
    
    Args:
        db: 資料庫 Session
    
    Returns:
        PIRService: PIR 服務
    """
    repository = PIRRepository(db)
    return PIRService(repository)


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_pir(
    request: CreatePIRRequest,
    service: PIRService = Depends(get_pir_service),
    user_id: str = "system",  # TODO: 從認證中介軟體取得
) -> dict:
    """
    建立 PIR
    
    Args:
        request: 建立 PIR 請求
        service: PIR 服務
        user_id: 使用者 ID（預設 "system"）
    
    Returns:
        dict: 包含 PIR ID 的回應
    
    Raises:
        HTTPException: 當輸入參數無效時
    """
    try:
        pir_id = await service.create_pir(request, user_id=user_id)
        return {"id": pir_id, "message": "PIR 建立成功"}
    except ValueError as e:
        logger.warning("建立 PIR 失敗", extra={"error": str(e), "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e)},
        )
    except Exception as e:
        logger.error("建立 PIR 時發生錯誤", extra={"error": str(e), "user_id": user_id}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "建立 PIR 時發生內部錯誤"},
        )


@router.get("", response_model=PIRListResponse)
async def get_pirs(
    page: int = Query(1, ge=1, description="頁碼（從 1 開始）"),
    page_size: int = Query(20, ge=1, le=100, description="每頁筆數"),
    sort_by: Optional[str] = Query(None, description="排序欄位（name、priority、created_at 等）"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="排序方向（asc/desc）"),
    service: PIRService = Depends(get_pir_service),
) -> PIRListResponse:
    """
    查詢 PIR 清單（支援分頁、排序）
    
    Args:
        page: 頁碼（從 1 開始）
        page_size: 每頁筆數（預設 20，最大 100）
        sort_by: 排序欄位
        sort_order: 排序方向（asc/desc）
        service: PIR 服務
    
    Returns:
        PIRListResponse: PIR 清單回應
    """
    try:
        return await service.get_pirs(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except ValueError as e:
        logger.warning("查詢 PIR 清單失敗", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e)},
        )
    except Exception as e:
        logger.error("查詢 PIR 清單時發生錯誤", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "查詢 PIR 清單時發生內部錯誤"},
        )


@router.get("/{pir_id}", response_model=PIRResponse)
async def get_pir_by_id(
    pir_id: str,
    service: PIRService = Depends(get_pir_service),
) -> PIRResponse:
    """
    查詢 PIR 詳情
    
    Args:
        pir_id: PIR ID
        service: PIR 服務
    
    Returns:
        PIRResponse: PIR 回應
    
    Raises:
        HTTPException: 當 PIR 不存在時
    """
    try:
        pir = await service.get_pir_by_id(pir_id)
        if not pir:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": f"PIR ID {pir_id} 不存在"},
            )
        return pir
    except HTTPException:
        raise
    except Exception as e:
        logger.error("查詢 PIR 詳情時發生錯誤", extra={"error": str(e), "pir_id": pir_id}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "查詢 PIR 詳情時發生內部錯誤"},
        )


@router.put("/{pir_id}", response_model=dict)
async def update_pir(
    pir_id: str,
    request: UpdatePIRRequest,
    service: PIRService = Depends(get_pir_service),
    user_id: str = "system",  # TODO: 從認證中介軟體取得
) -> dict:
    """
    更新 PIR
    
    Args:
        pir_id: PIR ID
        request: 更新 PIR 請求
        service: PIR 服務
        user_id: 使用者 ID（預設 "system"）
    
    Returns:
        dict: 成功回應
    
    Raises:
        HTTPException: 當 PIR 不存在或輸入參數無效時
    """
    try:
        await service.update_pir(pir_id, request, user_id=user_id)
        return {"id": pir_id, "message": "PIR 更新成功"}
    except ValueError as e:
        logger.warning("更新 PIR 失敗", extra={"error": str(e), "pir_id": pir_id, "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(e)},
        )
    except Exception as e:
        logger.error("更新 PIR 時發生錯誤", extra={"error": str(e), "pir_id": pir_id, "user_id": user_id}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "更新 PIR 時發生內部錯誤"},
        )


@router.delete("/{pir_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pir(
    pir_id: str,
    service: PIRService = Depends(get_pir_service),
    user_id: str = "system",  # TODO: 從認證中介軟體取得
) -> None:
    """
    刪除 PIR
    
    Args:
        pir_id: PIR ID
        service: PIR 服務
        user_id: 使用者 ID（預設 "system"）
    
    Raises:
        HTTPException: 當 PIR 不存在時
    """
    try:
        await service.delete_pir(pir_id, user_id=user_id)
    except ValueError as e:
        logger.warning("刪除 PIR 失敗", extra={"error": str(e), "pir_id": pir_id, "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": str(e)},
        )
    except Exception as e:
        logger.error("刪除 PIR 時發生錯誤", extra={"error": str(e), "pir_id": pir_id, "user_id": user_id}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "刪除 PIR 時發生內部錯誤"},
        )


@router.patch("/{pir_id}/toggle", response_model=dict)
async def toggle_pir(
    pir_id: str,
    service: PIRService = Depends(get_pir_service),
    user_id: str = "system",  # TODO: 從認證中介軟體取得
) -> dict:
    """
    切換 PIR 啟用狀態
    
    Args:
        pir_id: PIR ID
        service: PIR 服務
        user_id: 使用者 ID（預設 "system"）
    
    Returns:
        dict: 包含更新後狀態的回應
    
    Raises:
        HTTPException: 當 PIR 不存在時
    """
    try:
        await service.toggle_pir(pir_id, user_id=user_id)
        
        # 取得更新後的 PIR 以回傳狀態
        pir = await service.get_pir_by_id(pir_id)
        if not pir:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": f"PIR ID {pir_id} 不存在"},
            )
        
        return {
            "id": pir_id,
            "is_enabled": pir.is_enabled,
            "message": f"PIR 已{'啟用' if pir.is_enabled else '停用'}",
        }
    except ValueError as e:
        logger.warning("切換 PIR 啟用狀態失敗", extra={"error": str(e), "pir_id": pir_id, "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": str(e)},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("切換 PIR 啟用狀態時發生錯誤", extra={"error": str(e), "pir_id": pir_id, "user_id": user_id}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "切換 PIR 啟用狀態時發生內部錯誤"},
        )


@router.get("/enabled/list", response_model=list[PIRResponse])
async def get_enabled_pirs(
    service: PIRService = Depends(get_pir_service),
) -> list[PIRResponse]:
    """
    查詢啟用的 PIR
    
    Args:
        service: PIR 服務
    
    Returns:
        list[PIRResponse]: 啟用的 PIR 清單
    """
    try:
        return await service.get_enabled_pirs()
    except Exception as e:
        logger.error("查詢啟用的 PIR 時發生錯誤", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "查詢啟用的 PIR 時發生內部錯誤"},
        )

