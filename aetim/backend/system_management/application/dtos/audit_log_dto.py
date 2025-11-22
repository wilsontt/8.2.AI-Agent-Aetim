"""
稽核日誌 DTO

定義稽核日誌相關的資料傳輸物件。
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class AuditLogResponse(BaseModel):
    """稽核日誌回應"""
    
    id: str
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """稽核日誌清單回應"""
    
    data: list[AuditLogResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class AuditLogFilterRequest(BaseModel):
    """稽核日誌篩選請求"""
    
    user_id: Optional[str] = Field(None, description="使用者 ID")
    action: Optional[str] = Field(None, description="操作類型（CREATE/UPDATE/DELETE/IMPORT/VIEW/TOGGLE/EXPORT）")
    resource_type: Optional[str] = Field(None, description="資源類型（Asset/PIR/ThreatFeed 等）")
    resource_id: Optional[str] = Field(None, description="資源 ID")
    start_date: Optional[datetime] = Field(None, description="開始日期")
    end_date: Optional[datetime] = Field(None, description="結束日期")
    page: int = Field(1, ge=1, description="頁碼（從 1 開始）")
    page_size: int = Field(20, ge=1, le=100, description="每頁筆數")
    sort_by: Optional[str] = Field(None, description="排序欄位（created_at/action/resource_type）")
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="排序方向（asc/desc）")
    
    @validator("action")
    def validate_action(cls, v):
        """驗證操作類型"""
        if v is not None:
            valid_actions = ["CREATE", "UPDATE", "DELETE", "IMPORT", "VIEW", "TOGGLE", "EXPORT"]
            if v.upper() not in valid_actions:
                raise ValueError(f"操作類型必須為以下之一：{', '.join(valid_actions)}")
        return v.upper() if v else None

