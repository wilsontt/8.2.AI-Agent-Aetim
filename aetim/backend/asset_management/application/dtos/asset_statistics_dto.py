"""
資產統計 DTO

定義資產統計相關的資料傳輸物件。
"""

from typing import Dict
from pydantic import BaseModel, Field


class AssetStatisticsResponse(BaseModel):
    """資產統計回應"""
    
    total_count: int = Field(..., description="資產總數")
    by_type: Dict[str, int] = Field(..., description="依資產類型統計")
    by_sensitivity: Dict[str, int] = Field(..., description="依資料敏感度統計")
    by_criticality: Dict[str, int] = Field(..., description="依業務關鍵性統計")
    affected_assets: Dict[str, float] = Field(..., description="受威脅影響的資產統計")
    public_facing_count: int = Field(..., description="對外暴露資產數量")

