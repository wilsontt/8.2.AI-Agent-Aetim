"""
OAuth2/OIDC 服務

提供 OAuth2/OIDC 身份驗證功能。
支援授權碼流程 (Authorization Code Flow) 和 Token 驗證。
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
from jose import jwt, JWTError
from pydantic import BaseModel, Field
from shared_kernel.infrastructure.logging import get_logger
import os

logger = get_logger(__name__)


class OAuth2Config(BaseModel):
    """OAuth2 設定"""
    
    client_id: str = Field(..., description="Client ID")
    client_secret: str = Field(..., description="Client Secret")
    authorization_endpoint: str = Field(..., description="授權端點 URL")
    token_endpoint: str = Field(..., description="Token 端點 URL")
    userinfo_endpoint: str = Field(..., description="使用者資訊端點 URL")
    redirect_uri: str = Field(..., description="重定向 URI")
    scopes: list[str] = Field(default=["openid", "profile", "email"], description="請求的 Scope")
    issuer: Optional[str] = Field(None, description="IdP Issuer URL（用於 Token 驗證）")
    jwks_uri: Optional[str] = Field(None, description="JWKS URI（用於 Token 驗證）")


class TokenInfo(BaseModel):
    """Token 資訊"""
    
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    scope: Optional[str] = None


class UserInfo(BaseModel):
    """使用者資訊"""
    
    sub: str = Field(..., description="Subject ID")
    email: str = Field(..., description="Email 地址")
    name: Optional[str] = Field(None, description="顯示名稱")
    preferred_username: Optional[str] = Field(None, description="使用者名稱")
    given_name: Optional[str] = Field(None, description="名字")
    family_name: Optional[str] = Field(None, description="姓氏")
    picture: Optional[str] = Field(None, description="頭像 URL")


class OAuth2Service:
    """
    OAuth2/OIDC 服務
    
    提供 OAuth2/OIDC 身份驗證功能，包括：
    - 生成授權 URL
    - 交換授權碼為 Token
    - 驗證 Token
    - 取得使用者資訊
    """
    
    def __init__(self, config: OAuth2Config):
        """
        初始化 OAuth2 服務
        
        Args:
            config: OAuth2 設定
        """
        self.config = config
        self._jwks_cache: Optional[Dict[str, Any]] = None
        self._jwks_cache_expiry: Optional[datetime] = None
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        生成授權 URL
        
        符合 AC-022-1：整合 OIDC/OAuth 2.0 身份驗證提供者 (IdP)
        符合 AC-022-2：支援單一登入 (SSO) 功能
        
        Args:
            state: 狀態參數（用於 CSRF 保護，可選）
        
        Returns:
            str: 授權 URL
        """
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.config.scopes),
        }
        
        if state:
            params["state"] = state
        
        # 構建授權 URL
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        authorization_url = f"{self.config.authorization_endpoint}?{query_string}"
        
        logger.info(
            "生成授權 URL",
            extra={
                "authorization_endpoint": self.config.authorization_endpoint,
                "redirect_uri": self.config.redirect_uri,
            }
        )
        
        return authorization_url
    
    async def exchange_code_for_token(self, code: str) -> TokenInfo:
        """
        使用授權碼交換 Access Token
        
        Args:
            code: 授權碼
        
        Returns:
            TokenInfo: Token 資訊
        
        Raises:
            ValueError: 當授權碼無效或交換失敗時
        """
        try:
            async with httpx.AsyncClient() as client:
                data = {
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.config.redirect_uri,
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                }
                
                response = await client.post(
                    self.config.token_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                
                response.raise_for_status()
                token_data = response.json()
                
                return TokenInfo(
                    access_token=token_data["access_token"],
                    token_type=token_data.get("token_type", "Bearer"),
                    expires_in=token_data.get("expires_in", 3600),
                    refresh_token=token_data.get("refresh_token"),
                    id_token=token_data.get("id_token"),
                    scope=token_data.get("scope"),
                )
        except httpx.HTTPStatusError as e:
            logger.error(
                "交換授權碼失敗",
                extra={
                    "status_code": e.response.status_code,
                    "response": e.response.text,
                }
            )
            raise ValueError(f"交換授權碼失敗: {e.response.status_code}")
        except Exception as e:
            logger.error("交換授權碼時發生錯誤", extra={"error": str(e)}, exc_info=True)
            raise ValueError(f"交換授權碼時發生錯誤: {str(e)}")
    
    async def get_user_info(self, access_token: str) -> UserInfo:
        """
        取得使用者資訊
        
        Args:
            access_token: Access Token
        
        Returns:
            UserInfo: 使用者資訊
        
        Raises:
            ValueError: 當 Token 無效或取得使用者資訊失敗時
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.config.userinfo_endpoint,
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                
                response.raise_for_status()
                user_data = response.json()
                
                return UserInfo(
                    sub=user_data["sub"],
                    email=user_data.get("email", ""),
                    name=user_data.get("name"),
                    preferred_username=user_data.get("preferred_username"),
                    given_name=user_data.get("given_name"),
                    family_name=user_data.get("family_name"),
                    picture=user_data.get("picture"),
                )
        except httpx.HTTPStatusError as e:
            logger.error(
                "取得使用者資訊失敗",
                extra={
                    "status_code": e.response.status_code,
                    "response": e.response.text,
                }
            )
            raise ValueError(f"取得使用者資訊失敗: {e.response.status_code}")
        except Exception as e:
            logger.error("取得使用者資訊時發生錯誤", extra={"error": str(e)}, exc_info=True)
            raise ValueError(f"取得使用者資訊時發生錯誤: {str(e)}")
    
    async def _get_jwks(self) -> Dict[str, Any]:
        """
        取得 JWKS（JSON Web Key Set）
        
        Returns:
            Dict[str, Any]: JWKS 資料
        """
        # 檢查快取
        if self._jwks_cache and self._jwks_cache_expiry and datetime.utcnow() < self._jwks_cache_expiry:
            return self._jwks_cache
        
        if not self.config.jwks_uri:
            raise ValueError("JWKS URI 未設定")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.config.jwks_uri)
                response.raise_for_status()
                jwks = response.json()
                
                # 快取 1 小時
                self._jwks_cache = jwks
                self._jwks_cache_expiry = datetime.utcnow() + timedelta(hours=1)
                
                return jwks
        except Exception as e:
            logger.error("取得 JWKS 失敗", extra={"error": str(e)}, exc_info=True)
            raise ValueError(f"取得 JWKS 失敗: {str(e)}")


class TokenValidator:
    """
    Token 驗證器
    
    提供 Token 驗證功能，包括：
    - 驗證 Token 有效性
    - 檢查 Token 過期時間
    - 解析 Token 取得使用者資訊
    """
    
    def __init__(self, oauth2_service: OAuth2Service):
        """
        初始化 Token 驗證器
        
        Args:
            oauth2_service: OAuth2 服務（用於取得 JWKS）
        """
        self.oauth2_service = oauth2_service
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        驗證 Access Token
        
        Args:
            token: Access Token
        
        Returns:
            Dict[str, Any]: Token 內容（包含使用者資訊）
        
        Raises:
            ValueError: 當 Token 無效或過期時
        """
        try:
            # 如果沒有設定 Issuer 或 JWKS URI，則不驗證簽章（僅用於開發環境）
            if not self.oauth2_service.config.issuer or not self.oauth2_service.config.jwks_uri:
                logger.warning("Issuer 或 JWKS URI 未設定，跳過 Token 簽章驗證")
                # 僅解析 Token（不驗證簽章）
                decoded = jwt.decode(
                    token,
                    options={"verify_signature": False},
                )
                return decoded
            
            # 取得 JWKS
            jwks = await self.oauth2_service._get_jwks()
            
            # 驗證 Token
            decoded = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                audience=self.oauth2_service.config.client_id,
                issuer=self.oauth2_service.config.issuer,
            )
            
            # 檢查過期時間
            exp = decoded.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                raise ValueError("Token 已過期")
            
            return decoded
        except JWTError as e:
            logger.error("Token 驗證失敗", extra={"error": str(e)})
            raise ValueError(f"Token 驗證失敗: {str(e)}")
        except Exception as e:
            logger.error("驗證 Token 時發生錯誤", extra={"error": str(e)}, exc_info=True)
            raise ValueError(f"驗證 Token 時發生錯誤: {str(e)}")
    
    def extract_user_info_from_token(self, token_data: Dict[str, Any]) -> UserInfo:
        """
        從 Token 資料中提取使用者資訊
        
        Args:
            token_data: Token 內容
        
        Returns:
            UserInfo: 使用者資訊
        """
        return UserInfo(
            sub=token_data.get("sub", ""),
            email=token_data.get("email", ""),
            name=token_data.get("name"),
            preferred_username=token_data.get("preferred_username"),
            given_name=token_data.get("given_name"),
            family_name=token_data.get("family_name"),
            picture=token_data.get("picture"),
        )

