"""
關聯分析 DTO

定義關聯分析相關的資料傳輸物件。
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AssociationAnalysisResponse(BaseModel):
    """關聯分析回應"""
    
    success: bool
    threat_id: str
    associations_created: int
    errors: List[str] = []


class ThreatAssetAssociationResponse(BaseModel):
    """威脅-資產關聯回應"""
    
    id: str
    threat_id: str
    asset_id: str
    match_confidence: float = Field(..., ge=0.0, le=1.0, description="匹配信心分數（0.0-1.0）")
    match_type: str = Field(..., description="匹配類型（exact_product_exact_version, fuzzy_product_exact_version 等）")
    match_details: Optional[Dict[str, Any]] = Field(None, description="匹配詳情（JSON 格式）")
    created_at: Optional[datetime] = None


class ThreatAssociationListResponse(BaseModel):
    """威脅關聯清單回應"""
    
    items: List[ThreatAssetAssociationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AssetThreatAssociationResponse(BaseModel):
    """資產-威脅關聯回應（包含威脅資訊）"""
    
    id: str
    threat_id: str
    asset_id: str
    match_confidence: float = Field(..., ge=0.0, le=1.0, description="匹配信心分數（0.0-1.0）")
    match_type: str = Field(..., description="匹配類型")
    match_details: Optional[Dict[str, Any]] = Field(None, description="匹配詳情")
    created_at: Optional[datetime] = None
    # 威脅資訊
    threat_title: Optional[str] = None
    threat_cve_id: Optional[str] = None
    threat_cvss_base_score: Optional[float] = None
    threat_severity: Optional[str] = None
    threat_status: Optional[str] = None


class AssetThreatAssociationListResponse(BaseModel):
    """資產威脅關聯清單回應"""
    
    items: List[AssetThreatAssociationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AssociationAnalysisLogResponse(BaseModel):
    """關聯分析日誌回應"""
    
    threat_id: str
    analysis_started_at: Optional[datetime] = None
    analysis_completed_at: Optional[datetime] = None
    associations_created: int = 0
    associations_deleted: int = 0
    errors: List[str] = []
    status: str = Field(..., description="分析狀態（in_progress, completed, failed）")

