"""
資產管理控制器

提供資產管理相關的 API 端點。
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_assets():
    """取得資產清單"""
    # TODO: 實作資產清單查詢
    return {"assets": []}


@router.post("/")
async def create_asset():
    """建立新資產"""
    # TODO: 實作資產建立
    return {"message": "Asset created"}


@router.get("/{asset_id}")
async def get_asset(asset_id: str):
    """取得單一資產"""
    # TODO: 實作資產查詢
    return {"asset_id": asset_id}

