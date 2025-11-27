"""
系統設定 DTO

定義系統設定相關的資料傳輸物件。
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class SystemConfigurationDTO(BaseModel):
    """系統設定 DTO"""
    
    id: str
    key: str = Field(..., description="設定鍵")
    value: str = Field(..., description="設定值")
    category: str = Field(..., description="設定類別")
    description: Optional[str] = Field(None, description="設定說明")
    created_at: str
    updated_at: str
    updated_by: str
    
    class Config:
        from_attributes = True


class SystemConfigurationUpdateRequest(BaseModel):
    """系統設定更新請求"""
    
    key: str = Field(..., description="設定鍵")
    value: str = Field(..., description="設定值")
    description: Optional[str] = Field(None, description="設定說明")
    category: Optional[str] = Field(None, description="設定類別")


class SystemConfigurationBatchUpdateRequest(BaseModel):
    """系統設定批次更新請求"""
    
    configurations: List[SystemConfigurationUpdateRequest] = Field(
        ..., description="設定清單"
    )


class SystemConfigurationListResponse(BaseModel):
    """系統設定清單回應"""
    
    configurations: List[SystemConfigurationDTO]
    total: int

