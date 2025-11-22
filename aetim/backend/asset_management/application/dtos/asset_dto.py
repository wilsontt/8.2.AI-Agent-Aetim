"""
資產 DTO

定義資產相關的資料傳輸物件。
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator
from datetime import datetime


class CreateAssetRequest(BaseModel):
    """建立資產請求"""
    
    host_name: str = Field(..., description="主機名稱")
    ip: Optional[str] = Field(None, description="IP 位址或 IP 範圍")
    item: Optional[int] = Field(None, description="資產項目編號")
    operating_system: str = Field(..., description="作業系統（含版本）")
    running_applications: str = Field(..., description="運行的應用程式（含版本）")
    owner: str = Field(..., description="負責人")
    data_sensitivity: str = Field(..., description="資料敏感度（高/中/低）")
    is_public_facing: bool = Field(False, description="是否對外暴露")
    business_criticality: str = Field(..., description="業務關鍵性（高/中/低）")
    
    @validator("data_sensitivity")
    def validate_data_sensitivity(cls, v):
        """驗證資料敏感度"""
        if v not in ["高", "中", "低"]:
            raise ValueError("資料敏感度必須為「高」、「中」或「低」")
        return v
    
    @validator("business_criticality")
    def validate_business_criticality(cls, v):
        """驗證業務關鍵性"""
        if v not in ["高", "中", "低"]:
            raise ValueError("業務關鍵性必須為「高」、「中」或「低」")
        return v


class UpdateAssetRequest(BaseModel):
    """更新資產請求"""
    
    host_name: Optional[str] = Field(None, description="主機名稱")
    ip: Optional[str] = Field(None, description="IP 位址或 IP 範圍")
    operating_system: Optional[str] = Field(None, description="作業系統（含版本）")
    running_applications: Optional[str] = Field(None, description="運行的應用程式（含版本）")
    owner: Optional[str] = Field(None, description="負責人")
    data_sensitivity: Optional[str] = Field(None, description="資料敏感度（高/中/低）")
    is_public_facing: Optional[bool] = Field(None, description="是否對外暴露")
    business_criticality: Optional[str] = Field(None, description="業務關鍵性（高/中/低）")
    
    @validator("data_sensitivity")
    def validate_data_sensitivity(cls, v):
        """驗證資料敏感度"""
        if v is not None and v not in ["高", "中", "低"]:
            raise ValueError("資料敏感度必須為「高」、「中」或「低」")
        return v
    
    @validator("business_criticality")
    def validate_business_criticality(cls, v):
        """驗證業務關鍵性"""
        if v is not None and v not in ["高", "中", "低"]:
            raise ValueError("業務關鍵性必須為「高」、「中」或「低」")
        return v


class ProductResponse(BaseModel):
    """產品回應"""
    
    id: str
    product_name: str
    product_version: Optional[str]
    product_type: Optional[str]
    original_text: Optional[str]


class AssetResponse(BaseModel):
    """資產回應"""
    
    id: str
    host_name: str
    ip: Optional[str]
    item: Optional[int]
    operating_system: str
    running_applications: str
    owner: str
    data_sensitivity: str
    is_public_facing: bool
    business_criticality: str
    products: List[ProductResponse]
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    
    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    """資產清單回應"""
    
    data: List[AssetResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class AssetSearchRequest(BaseModel):
    """資產搜尋請求"""
    
    product_name: Optional[str] = Field(None, description="產品名稱（模糊搜尋）")
    product_version: Optional[str] = Field(None, description="產品版本（模糊搜尋）")
    product_type: Optional[str] = Field(None, description="產品類型（OS/Application）")
    is_public_facing: Optional[bool] = Field(None, description="是否對外暴露")
    data_sensitivity: Optional[str] = Field(None, description="資料敏感度（高/中/低）")
    business_criticality: Optional[str] = Field(None, description="業務關鍵性（高/中/低）")
    page: int = Field(1, ge=1, description="頁碼（從 1 開始）")
    page_size: int = Field(20, ge=20, description="每頁筆數（至少 20）")
    sort_by: Optional[str] = Field(None, description="排序欄位")
    sort_order: str = Field("asc", description="排序方向（asc/desc）")
    
    @validator("data_sensitivity")
    def validate_data_sensitivity(cls, v):
        """驗證資料敏感度"""
        if v is not None and v not in ["高", "中", "低"]:
            raise ValueError("資料敏感度必須為「高」、「中」或「低」")
        return v
    
    @validator("business_criticality")
    def validate_business_criticality(cls, v):
        """驗證業務關鍵性"""
        if v is not None and v not in ["高", "中", "低"]:
            raise ValueError("業務關鍵性必須為「高」、「中」或「低」")
        return v


class ImportPreviewResponse(BaseModel):
    """匯入預覽回應"""
    
    total_count: int
    valid_count: int
    invalid_count: int
    preview_data: List[dict]
    errors: List[dict]


class ImportResultResponse(BaseModel):
    """匯入結果回應"""
    
    total_count: int
    success_count: int
    failure_count: int
    results: List[dict]

