"""
威脅情資來源 DTO

定義威脅情資來源相關的資料傳輸物件。
"""

from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class CreateThreatFeedRequest(BaseModel):
    """建立威脅情資來源請求"""
    
    name: str = Field(..., description="來源名稱（CISA KEV、NVD 等）")
    description: Optional[str] = Field(None, description="來源描述")
    priority: str = Field(..., description="優先級（P0/P1/P2/P3）")
    collection_frequency: str = Field(..., description="收集頻率（每小時/每日/每週/每月）")
    collection_strategy: Optional[str] = Field(None, description="收集策略說明")
    api_key: Optional[str] = Field(None, description="API 金鑰（加密儲存）")
    is_enabled: bool = Field(True, description="是否啟用")
    
    @validator("priority")
    def validate_priority(cls, v):
        """驗證優先級"""
        if v not in ["P0", "P1", "P2", "P3"]:
            raise ValueError("優先級必須為 P0、P1、P2 或 P3")
        return v
    
    @validator("collection_frequency")
    def validate_collection_frequency(cls, v):
        """驗證收集頻率"""
        valid_frequencies = ["每小時", "每日", "每週", "每月"]
        if v not in valid_frequencies:
            raise ValueError(f"收集頻率必須為以下之一：{', '.join(valid_frequencies)}")
        return v


class UpdateThreatFeedRequest(BaseModel):
    """更新威脅情資來源請求"""
    
    name: Optional[str] = Field(None, description="來源名稱")
    description: Optional[str] = Field(None, description="來源描述")
    priority: Optional[str] = Field(None, description="優先級（P0/P1/P2/P3）")
    collection_frequency: Optional[str] = Field(None, description="收集頻率")
    collection_strategy: Optional[str] = Field(None, description="收集策略說明")
    api_key: Optional[str] = Field(None, description="API 金鑰")
    
    @validator("priority")
    def validate_priority(cls, v):
        """驗證優先級"""
        if v is not None and v not in ["P0", "P1", "P2", "P3"]:
            raise ValueError("優先級必須為 P0、P1、P2 或 P3")
        return v
    
    @validator("collection_frequency")
    def validate_collection_frequency(cls, v):
        """驗證收集頻率"""
        if v is not None:
            valid_frequencies = ["每小時", "每日", "每週", "每月"]
            if v not in valid_frequencies:
                raise ValueError(f"收集頻率必須為以下之一：{', '.join(valid_frequencies)}")
        return v


class ThreatFeedResponse(BaseModel):
    """威脅情資來源回應"""
    
    id: str
    name: str
    description: Optional[str]
    priority: str
    is_enabled: bool
    collection_frequency: Optional[str]
    collection_strategy: Optional[str]
    last_collection_time: Optional[datetime]
    last_collection_status: Optional[str]
    last_collection_error: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    
    class Config:
        from_attributes = True


class ThreatFeedListResponse(BaseModel):
    """威脅情資來源清單回應"""
    
    data: list[ThreatFeedResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class CollectionStatusResponse(BaseModel):
    """收集狀態回應"""
    
    threat_feed_id: str
    name: str
    last_collection_time: Optional[datetime]
    last_collection_status: Optional[str]
    last_collection_error: Optional[str]
    is_enabled: bool
    collection_frequency: Optional[str]

