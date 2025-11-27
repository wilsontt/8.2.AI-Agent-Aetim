"""
威脅統計 DTO

定義威脅統計相關的資料傳輸物件。
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ThreatTrendDataPoint(BaseModel):
    """威脅趨勢資料點"""
    
    date: str = Field(..., description="日期")
    count: int = Field(..., description="威脅數量")


class ThreatTrendResponse(BaseModel):
    """威脅趨勢回應"""
    
    data: List[ThreatTrendDataPoint] = Field(..., description="趨勢資料")
    start_date: str = Field(..., description="開始日期")
    end_date: str = Field(..., description="結束日期")
    interval: str = Field(..., description="時間間隔")


class RiskDistributionResponse(BaseModel):
    """風險分數分布回應"""
    
    distribution: Dict[str, int] = Field(..., description="風險等級分布")
    total: int = Field(..., description="總數")


class AffectedAssetStatisticsResponse(BaseModel):
    """受影響資產統計回應"""
    
    by_type: Dict[str, int] = Field(..., description="依資產類型統計")
    by_importance: Dict[str, int] = Field(..., description="依資產重要性統計")


class ThreatSourceStatisticsDataPoint(BaseModel):
    """威脅來源統計資料點"""
    
    source_name: str = Field(..., description="來源名稱")
    priority: str = Field(..., description="優先級")
    count: int = Field(..., description="威脅數量")


class ThreatSourceStatisticsResponse(BaseModel):
    """威脅來源統計回應"""
    
    data: List[ThreatSourceStatisticsDataPoint] = Field(..., description="來源統計資料")

