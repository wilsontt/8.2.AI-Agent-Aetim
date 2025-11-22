"""
PIR DTO

定義 PIR 相關的資料傳輸物件。
"""

from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class CreatePIRRequest(BaseModel):
    """建立 PIR 請求"""
    
    name: str = Field(..., description="PIR 名稱")
    description: str = Field(..., description="PIR 描述")
    priority: str = Field(..., description="優先級（高/中/低）")
    condition_type: str = Field(..., description="條件類型（產品名稱、CVE 編號、威脅類型等）")
    condition_value: str = Field(..., description="條件值")
    is_enabled: bool = Field(True, description="是否啟用")
    
    @validator("priority")
    def validate_priority(cls, v):
        """驗證優先級"""
        if v not in ["高", "中", "低"]:
            raise ValueError("優先級必須為「高」、「中」或「低」")
        return v
    
    @validator("condition_type")
    def validate_condition_type(cls, v):
        """驗證條件類型"""
        valid_types = ["產品名稱", "CVE 編號", "威脅類型", "CVSS 分數"]
        if v not in valid_types:
            raise ValueError(f"條件類型必須為以下之一：{', '.join(valid_types)}")
        return v


class UpdatePIRRequest(BaseModel):
    """更新 PIR 請求"""
    
    name: Optional[str] = Field(None, description="PIR 名稱")
    description: Optional[str] = Field(None, description="PIR 描述")
    priority: Optional[str] = Field(None, description="優先級（高/中/低）")
    condition_type: Optional[str] = Field(None, description="條件類型")
    condition_value: Optional[str] = Field(None, description="條件值")
    
    @validator("priority")
    def validate_priority(cls, v):
        """驗證優先級"""
        if v is not None and v not in ["高", "中", "低"]:
            raise ValueError("優先級必須為「高」、「中」或「低」")
        return v


class PIRResponse(BaseModel):
    """PIR 回應"""
    
    id: str
    name: str
    description: str
    priority: str
    condition_type: str
    condition_value: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str
    
    class Config:
        from_attributes = True


class PIRListResponse(BaseModel):
    """PIR 清單回應"""
    
    data: list[PIRResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

