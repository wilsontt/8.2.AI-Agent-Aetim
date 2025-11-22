"""
報告控制器

提供報告相關的 API 端點。
"""

from fastapi import APIRouter

router = APIRouter()


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

