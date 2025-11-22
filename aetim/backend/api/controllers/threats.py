"""
威脅情資控制器

提供威脅情資相關的 API 端點。
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_threats():
    """取得威脅清單"""
    # TODO: 實作威脅清單查詢
    return {"threats": []}


@router.get("/{threat_id}")
async def get_threat(threat_id: str):
    """取得單一威脅"""
    # TODO: 實作威脅查詢
    return {"threat_id": threat_id}

