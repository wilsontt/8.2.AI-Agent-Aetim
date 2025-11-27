"""
身份驗證 DTO

定義身份驗證相關的資料傳輸物件。
"""

from typing import Optional
from pydantic import BaseModel, Field


class AuthorizationUrlResponse(BaseModel):
    """授權 URL 回應"""
    
    authorization_url: str = Field(..., description="授權 URL")
    state: Optional[str] = Field(None, description="狀態參數（用於 CSRF 保護）")


class CallbackRequest(BaseModel):
    """授權回調請求"""
    
    code: str = Field(..., description="授權碼")
    state: Optional[str] = Field(None, description="狀態參數（用於 CSRF 保護）")


class TokenResponse(BaseModel):
    """Token 回應"""
    
    access_token: str = Field(..., description="Access Token")
    token_type: str = Field(default="Bearer", description="Token 類型")
    expires_in: int = Field(..., description="過期時間（秒）")
    refresh_token: Optional[str] = Field(None, description="Refresh Token")
    id_token: Optional[str] = Field(None, description="ID Token")


class UserInfoResponse(BaseModel):
    """使用者資訊回應"""
    
    id: str = Field(..., description="使用者 ID")
    subject_id: str = Field(..., description="Subject ID")
    email: str = Field(..., description="Email 地址")
    display_name: str = Field(..., description="顯示名稱")
    is_active: bool = Field(..., description="是否啟用")


class LoginResponse(BaseModel):
    """登入回應"""
    
    token: TokenResponse = Field(..., description="Token 資訊")
    user: UserInfoResponse = Field(..., description="使用者資訊")


class LogoutRequest(BaseModel):
    """登出請求"""
    
    pass

