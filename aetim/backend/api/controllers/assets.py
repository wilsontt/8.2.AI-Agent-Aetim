"""
資產管理控制器

提供資產管理相關的 API 端點。
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    UploadFile,
    File,
    status,
)
from fastapi.responses import JSONResponse
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from shared_kernel.infrastructure.database import get_db
from shared_kernel.infrastructure.logging import get_logger
from asset_management.application.services import AssetService, AssetImportService
from asset_management.application.dtos.asset_dto import (
    CreateAssetRequest,
    UpdateAssetRequest,
    AssetResponse,
    AssetListResponse,
    AssetSearchRequest,
    ImportPreviewResponse,
    ImportResultResponse,
)
from asset_management.infrastructure.persistence import AssetRepository
from asset_management.domain.domain_services.asset_parsing_service import AssetParsingService

logger = get_logger(__name__)
router = APIRouter()


def get_asset_service(db: AsyncSession = Depends(get_db)) -> AssetService:
    """
    取得資產服務
    
    Args:
        db: 資料庫 Session
    
    Returns:
        AssetService: 資產服務
    """
    repository = AssetRepository(db)
    parsing_service = AssetParsingService()
    return AssetService(repository, parsing_service)


def get_asset_import_service(
    asset_service: AssetService = Depends(get_asset_service),
) -> AssetImportService:
    """
    取得資產匯入服務
    
    Args:
        asset_service: 資產服務
    
    Returns:
        AssetImportService: 資產匯入服務
    """
    return AssetImportService(asset_service)


@router.post(
    "",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="建立資產",
    description="建立新的資產記錄",
    responses={
        201: {
            "description": "資產建立成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": "guid",
                        "message": "資產建立成功",
                    }
                }
            },
        },
        400: {"description": "請求參數錯誤"},
        422: {"description": "驗證錯誤"},
    },
)
async def create_asset(
    request: CreateAssetRequest,
    asset_service: AssetService = Depends(get_asset_service),
    user_id: str = "system",  # TODO: 從認證中介軟體取得
) -> dict:
    """
    建立資產
    
    - **host_name**: 主機名稱（必填）
    - **operating_system**: 作業系統（含版本）（必填）
    - **running_applications**: 運行的應用程式（含版本）（必填）
    - **owner**: 負責人（必填）
    - **data_sensitivity**: 資料敏感度（高/中/低）（必填）
    - **business_criticality**: 業務關鍵性（高/中/低）（必填）
    - **ip**: IP 位址（可選）
    - **item**: 資產項目編號（可選）
    - **is_public_facing**: 是否對外暴露（預設 False）
    """
    try:
        asset_id = await asset_service.create_asset(request, user_id)
        logger.info("資產建立成功", extra={"asset_id": asset_id, "user_id": user_id})
        return {
            "id": asset_id,
            "message": "資產建立成功",
        }
    except ValueError as e:
        logger.error("資產建立失敗", extra={"error": str(e), "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_REQUEST", "message": str(e)},
        )
    except Exception as e:
        logger.error("資產建立失敗", extra={"error": str(e), "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "資產建立失敗"},
        )


@router.get(
    "",
    response_model=AssetListResponse,
    summary="查詢資產清單",
    description="查詢資產清單，支援分頁、排序和篩選",
    responses={
        200: {"description": "查詢成功"},
        400: {"description": "請求參數錯誤"},
    },
)
async def list_assets(
    page: int = Query(1, ge=1, description="頁碼（從 1 開始）"),
    page_size: int = Query(20, ge=20, description="每頁筆數（至少 20）"),
    sort_by: Optional[str] = Query(None, description="排序欄位（host_name、owner、created_at 等）"),
    sort_order: str = Query("asc", description="排序方向（asc/desc）"),
    # 篩選參數
    product_name: Optional[str] = Query(None, description="產品名稱（模糊搜尋）"),
    product_version: Optional[str] = Query(None, description="產品版本（模糊搜尋）"),
    product_type: Optional[str] = Query(None, description="產品類型（OS/Application）"),
    is_public_facing: Optional[bool] = Query(None, description="是否對外暴露"),
    data_sensitivity: Optional[str] = Query(None, description="資料敏感度（高/中/低）"),
    business_criticality: Optional[str] = Query(None, description="業務關鍵性（高/中/低）"),
    asset_service: AssetService = Depends(get_asset_service),
) -> AssetListResponse:
    """
    查詢資產清單
    
    支援分頁、排序和篩選功能。
    
    - **page**: 頁碼（從 1 開始）
    - **page_size**: 每頁筆數（至少 20）
    - **sort_by**: 排序欄位
    - **sort_order**: 排序方向（asc/desc）
    - **product_name**: 產品名稱（模糊搜尋）
    - **product_version**: 產品版本（模糊搜尋）
    - **product_type**: 產品類型
    - **is_public_facing**: 是否對外暴露
    - **data_sensitivity**: 資料敏感度
    - **business_criticality**: 業務關鍵性
    """
    try:
        # 如果有篩選條件，使用搜尋功能
        if any([
            product_name,
            product_version,
            product_type,
            is_public_facing is not None,
            data_sensitivity,
            business_criticality,
        ]):
            search_request = AssetSearchRequest(
                product_name=product_name,
                product_version=product_version,
                product_type=product_type,
                is_public_facing=is_public_facing,
                data_sensitivity=data_sensitivity,
                business_criticality=business_criticality,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order,
            )
            return await asset_service.search_assets(search_request)
        else:
            # 否則使用一般查詢
            return await asset_service.get_assets(
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order,
            )
    except ValueError as e:
        logger.error("查詢資產清單失敗", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_REQUEST", "message": str(e)},
        )
    except Exception as e:
        logger.error("查詢資產清單失敗", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "查詢資產清單失敗"},
        )


@router.get(
    "/{asset_id}",
    response_model=AssetResponse,
    summary="查詢資產詳情",
    description="取得單一資產的完整資訊",
    responses={
        200: {"description": "查詢成功"},
        404: {"description": "資產不存在"},
    },
)
async def get_asset(
    asset_id: str,
    asset_service: AssetService = Depends(get_asset_service),
) -> AssetResponse:
    """
    查詢資產詳情
    
    - **asset_id**: 資產 ID
    """
    asset = await asset_service.get_asset_by_id(asset_id)
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ASSET_NOT_FOUND", "message": f"資產 ID {asset_id} 不存在"},
        )
    
    return asset


@router.put(
    "/{asset_id}",
    response_model=dict,
    summary="更新資產",
    description="完整更新資產資訊",
    responses={
        200: {"description": "更新成功"},
        404: {"description": "資產不存在"},
        400: {"description": "請求參數錯誤"},
    },
)
async def update_asset(
    asset_id: str,
    request: UpdateAssetRequest,
    asset_service: AssetService = Depends(get_asset_service),
    user_id: str = "system",  # TODO: 從認證中介軟體取得
) -> dict:
    """
    更新資產
    
    - **asset_id**: 資產 ID
    - 所有欄位都是可選的，只更新提供的欄位
    """
    try:
        await asset_service.update_asset(asset_id, request, user_id)
        logger.info("資產更新成功", extra={"asset_id": asset_id, "user_id": user_id})
        return {
            "id": asset_id,
            "message": "資產更新成功",
        }
    except ValueError as e:
        logger.error("資產更新失敗", extra={"asset_id": asset_id, "error": str(e), "user_id": user_id})
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ASSET_NOT_FOUND", "message": str(e)},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_REQUEST", "message": str(e)},
        )
    except Exception as e:
        logger.error("資產更新失敗", extra={"asset_id": asset_id, "error": str(e), "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "資產更新失敗"},
        )


@router.delete(
    "/{asset_id}",
    response_model=dict,
    summary="刪除資產",
    description="刪除資產（需要確認）",
    responses={
        200: {"description": "刪除成功"},
        404: {"description": "資產不存在"},
        400: {"description": "未確認刪除"},
    },
)
async def delete_asset(
    asset_id: str,
    confirm: bool = Query(False, description="確認刪除（必須為 true）"),
    asset_service: AssetService = Depends(get_asset_service),
    user_id: str = "system",  # TODO: 從認證中介軟體取得
) -> dict:
    """
    刪除資產
    
    - **asset_id**: 資產 ID
    - **confirm**: 確認刪除（必須為 true）
    """
    try:
        await asset_service.delete_asset(asset_id, user_id, confirm=confirm)
        logger.info("資產刪除成功", extra={"asset_id": asset_id, "user_id": user_id})
        return {
            "id": asset_id,
            "message": "資產刪除成功",
        }
    except ValueError as e:
        logger.error("資產刪除失敗", extra={"asset_id": asset_id, "error": str(e), "user_id": user_id})
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "ASSET_NOT_FOUND", "message": str(e)},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_REQUEST", "message": str(e)},
        )
    except Exception as e:
        logger.error("資產刪除失敗", extra={"asset_id": asset_id, "error": str(e), "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "資產刪除失敗"},
        )


@router.post(
    "/batch-delete",
    response_model=dict,
    summary="批次刪除資產",
    description="批次刪除多筆資產（需要確認）",
    responses={
        200: {"description": "批次刪除完成"},
        400: {"description": "未確認刪除或請求參數錯誤"},
    },
)
async def batch_delete_assets(
    asset_ids: list[str],
    confirm: bool = Query(False, description="確認刪除（必須為 true）"),
    asset_service: AssetService = Depends(get_asset_service),
    user_id: str = "system",  # TODO: 從認證中介軟體取得
) -> dict:
    """
    批次刪除資產
    
    - **asset_ids**: 資產 ID 清單
    - **confirm**: 確認刪除（必須為 true）
    """
    try:
        result = await asset_service.batch_delete_assets(asset_ids, user_id, confirm=confirm)
        logger.info("批次刪除完成", extra={
            "total_count": len(asset_ids),
            "success_count": result["success_count"],
            "failure_count": result["failure_count"],
            "user_id": user_id,
        })
        return {
            "message": "批次刪除完成",
            "success_count": result["success_count"],
            "failure_count": result["failure_count"],
            "errors": result.get("errors", []),
        }
    except ValueError as e:
        logger.error("批次刪除失敗", extra={"error": str(e), "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_REQUEST", "message": str(e)},
        )
    except Exception as e:
        logger.error("批次刪除失敗", extra={"error": str(e), "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "批次刪除失敗"},
        )


@router.post(
    "/import",
    response_model=ImportResultResponse,
    summary="匯入資產",
    description="從 CSV 檔案匯入資產清冊（檔案大小限制 ≤ 10MB）",
    responses={
        200: {"description": "匯入完成"},
        400: {"description": "檔案格式錯誤或檔案過大"},
        422: {"description": "驗證錯誤"},
    },
)
async def import_assets(
    file: UploadFile = File(..., description="CSV 檔案（≤ 10MB）"),
    asset_import_service: AssetImportService = Depends(get_asset_import_service),
    user_id: str = "system",  # TODO: 從認證中介軟體取得
) -> ImportResultResponse:
    """
    匯入資產
    
    - **file**: CSV 檔案（≤ 10MB）
    - CSV 檔案必須包含必要欄位：主機名稱、作業系統(含版本)、運行的應用程式(含版本)、負責人、資料敏感度、是否對外(Public-facing)、業務關鍵性
    """
    # 檢查檔案大小（10MB = 10 * 1024 * 1024 bytes）
    MAX_FILE_SIZE = 10 * 1024 * 1024
    file_content = await file.read()
    
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": f"檔案大小超過限制（最大 {MAX_FILE_SIZE / 1024 / 1024}MB）",
            },
        )
    
    # 檢查檔案類型
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_FILE_TYPE", "message": "檔案必須為 CSV 格式"},
        )
    
    try:
        # 讀取 CSV 內容
        csv_content = file_content.decode("utf-8-sig")  # 處理 BOM
        
        # 執行匯入
        result = await asset_import_service.import_assets(csv_content, user_id)
        
        logger.info("資產匯入完成", extra={
            "total_count": result.total_count,
            "success_count": result.success_count,
            "failure_count": result.failure_count,
            "user_id": user_id,
        })
        
        return result
    
    except ValueError as e:
        logger.error("資產匯入失敗", extra={"error": str(e), "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_CSV_FORMAT", "message": str(e)},
        )
    except Exception as e:
        logger.error("資產匯入失敗", extra={"error": str(e), "user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "資產匯入失敗"},
        )


@router.post(
    "/import/preview",
    response_model=ImportPreviewResponse,
    summary="預覽匯入資料",
    description="預覽 CSV 檔案匯入資料，不執行實際匯入",
    responses={
        200: {"description": "預覽成功"},
        400: {"description": "檔案格式錯誤或檔案過大"},
    },
)
async def preview_import(
    file: UploadFile = File(..., description="CSV 檔案（≤ 10MB）"),
    max_preview_rows: int = Query(10, ge=1, le=100, description="最大預覽行數（1-100）"),
    asset_import_service: AssetImportService = Depends(get_asset_import_service),
) -> ImportPreviewResponse:
    """
    預覽匯入資料
    
    - **file**: CSV 檔案（≤ 10MB）
    - **max_preview_rows**: 最大預覽行數（1-100）
    """
    # 檢查檔案大小
    MAX_FILE_SIZE = 10 * 1024 * 1024
    file_content = await file.read()
    
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": f"檔案大小超過限制（最大 {MAX_FILE_SIZE / 1024 / 1024}MB）",
            },
        )
    
    # 檢查檔案類型
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_FILE_TYPE", "message": "檔案必須為 CSV 格式"},
        )
    
    try:
        # 讀取 CSV 內容
        csv_content = file_content.decode("utf-8-sig")  # 處理 BOM
        
        # 執行預覽
        preview = await asset_import_service.preview_import(csv_content, max_preview_rows)
        
        return preview
    
    except ValueError as e:
        logger.error("匯入預覽失敗", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_CSV_FORMAT", "message": str(e)},
        )
    except Exception as e:
        logger.error("匯入預覽失敗", extra={"error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "匯入預覽失敗"},
        )
