"""
威脅 DTO

定義威脅相關的資料傳輸物件。
"""

from typing import Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class ThreatProductResponse(BaseModel):
    """威脅產品回應"""
    
    id: str
    product_name: str
    product_version: Optional[str] = None
    product_type: Optional[str] = None
    original_text: Optional[str] = None


class ThreatResponse(BaseModel):
    """威脅回應"""
    
    id: str
    threat_feed_id: str
    title: str
    description: Optional[str] = None
    cve_id: Optional[str] = None
    cvss_base_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    severity: Optional[str] = None
    status: str
    source_url: Optional[str] = None
    published_date: Optional[datetime] = None
    collected_at: Optional[datetime] = None
    products: List[ThreatProductResponse] = []
    ttps: List[str] = []
    iocs: Dict[str, List[str]] = {}
    created_at: datetime
    updated_at: datetime


class ThreatListResponse(BaseModel):
    """威脅清單回應"""
    
    items: List[ThreatResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ThreatSearchParams(BaseModel):
    """威脅搜尋參數"""
    
    query: str = Field(..., description="搜尋關鍵字")
    page: int = Field(1, ge=1, description="頁碼")
    page_size: int = Field(100, ge=1, le=1000, description="每頁筆數")


class ThreatListParams(BaseModel):
    """威脅清單查詢參數"""
    
    page: int = Field(1, ge=1, description="頁碼")
    page_size: int = Field(100, ge=1, le=1000, description="每頁筆數")
    status: Optional[str] = Field(None, description="狀態篩選")
    threat_feed_id: Optional[str] = Field(None, description="威脅情資來源 ID 篩選")
    cve_id: Optional[str] = Field(None, description="CVE 編號篩選")
    product_name: Optional[str] = Field(None, description="產品名稱篩選")
    min_cvss_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="最小 CVSS 分數")
    max_cvss_score: Optional[float] = Field(None, ge=0.0, le=10.0, description="最大 CVSS 分數")
    sort_by: Optional[str] = Field(None, description="排序欄位（created_at, updated_at, cvss_base_score, published_date）")
    sort_order: str = Field("desc", description="排序順序（asc, desc）")


class UpdateThreatStatusRequest(BaseModel):
    """更新威脅狀態請求"""
    
    status: str = Field(..., description="新狀態（New, Analyzing, Processed, Closed）")


class ThreatDetailResponse(BaseModel):
    """威脅詳細回應（包含關聯的資產）"""
    
    threat: ThreatResponse
    associated_assets: List[Dict] = Field(default_factory=list, description="關聯的資產清單")

