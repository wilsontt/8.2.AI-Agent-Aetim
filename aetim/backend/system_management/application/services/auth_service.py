"""
身份驗證服務

提供身份驗證相關的應用層服務，包括：
- 登入處理
- Token 驗證
- 使用者資訊管理
- 稽核日誌記錄
"""

from typing import Optional
from datetime import datetime
from ...infrastructure.external_services.oauth2_service import (
    OAuth2Service,
    OAuth2Config,
    TokenInfo,
    UserInfo,
    TokenValidator,
)
from ...domain.interfaces.audit_log_repository import IAuditLogRepository
from ...domain.entities.audit_log import AuditLog
from ...infrastructure.persistence.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared_kernel.infrastructure.logging import get_logger
import uuid

logger = get_logger(__name__)


class AuthService:
    """
    身份驗證服務
    
    提供身份驗證相關的應用層服務。
    符合 AC-022-1, AC-022-2, AC-022-3, AC-022-4。
    """
    
    def __init__(
        self,
        oauth2_service: OAuth2Service,
        token_validator: TokenValidator,
        audit_log_repository: IAuditLogRepository,
        db_session: AsyncSession,
    ):
        """
        初始化身份驗證服務
        
        Args:
            oauth2_service: OAuth2 服務
            token_validator: Token 驗證器
            audit_log_repository: 稽核日誌 Repository
            db_session: 資料庫 Session
        """
        self.oauth2_service = oauth2_service
        self.token_validator = token_validator
        self.audit_log_repository = audit_log_repository
        self.db_session = db_session
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        取得授權 URL
        
        符合 AC-022-1：整合 OIDC/OAuth 2.0 身份驗證提供者 (IdP)
        符合 AC-022-2：支援單一登入 (SSO) 功能
        
        Args:
            state: 狀態參數（用於 CSRF 保護，可選）
        
        Returns:
            str: 授權 URL
        """
        return self.oauth2_service.get_authorization_url(state)
    
    async def handle_callback(
        self,
        code: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> tuple[TokenInfo, UserInfo, User]:
        """
        處理授權回調
        
        符合 AC-022-1：整合 OIDC/OAuth 2.0 身份驗證提供者 (IdP)
        符合 AC-022-4：記錄所有登入嘗試的稽核日誌（成功與失敗）
        
        Args:
            code: 授權碼
            ip_address: IP 位址（可選）
            user_agent: User Agent（可選）
        
        Returns:
            tuple[TokenInfo, UserInfo, User]: Token 資訊、使用者資訊、使用者實體
        
        Raises:
            ValueError: 當授權碼無效或登入失敗時
        """
        try:
            # 交換授權碼為 Token
            token_info = await self.oauth2_service.exchange_code_for_token(code)
            
            # 取得使用者資訊
            user_info = await self.oauth2_service.get_user_info(token_info.access_token)
            
            # 取得或建立使用者
            user = await self._get_or_create_user(user_info)
            
            # 更新最後登入時間
            user.last_login_at = datetime.utcnow()
            await self.db_session.commit()
            
            # 記錄登入成功的稽核日誌（AC-022-4）
            audit_log = AuditLog.create(
                user_id=user.id,
                action="LOGIN",
                resource_type="Auth",
                resource_id=None,
                details={"status": "success", "ip_address": ip_address},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self.audit_log_repository.save(audit_log)
            
            logger.info(
                "使用者登入成功",
                extra={
                    "user_id": user.id,
                    "email": user.email,
                    "ip_address": ip_address,
                }
            )
            
            return token_info, user_info, user
        except ValueError as e:
            # 記錄登入失敗的稽核日誌（AC-022-4）
            audit_log = AuditLog.create(
                user_id=None,
                action="LOGIN",
                resource_type="Auth",
                resource_id=None,
                details={"status": "failed", "error": str(e), "ip_address": ip_address},
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self.audit_log_repository.save(audit_log)
            
            logger.warning(
                "使用者登入失敗",
                extra={
                    "error": str(e),
                    "ip_address": ip_address,
                }
            )
            
            raise ValueError(f"登入失敗: {str(e)}")
    
    async def validate_token(self, token: str) -> UserInfo:
        """
        驗證 Token 並取得使用者資訊
        
        Args:
            token: Access Token
        
        Returns:
            UserInfo: 使用者資訊
        
        Raises:
            ValueError: 當 Token 無效或過期時
        """
        token_data = await self.token_validator.validate_token(token)
        return self.token_validator.extract_user_info_from_token(token_data)
    
    async def get_user_by_subject_id(self, subject_id: str) -> Optional[User]:
        """
        依 Subject ID 取得使用者
        
        Args:
            subject_id: Subject ID
        
        Returns:
            Optional[User]: 使用者實體，如果不存在則返回 None
        """
        result = await self.db_session.execute(
            select(User).where(User.subject_id == subject_id)
        )
        return result.scalar_one_or_none()
    
    async def _get_or_create_user(self, user_info: UserInfo) -> User:
        """
        取得或建立使用者
        
        Args:
            user_info: 使用者資訊
        
        Returns:
            User: 使用者實體
        """
        # 查詢現有使用者
        user = await self.get_user_by_subject_id(user_info.sub)
        
        if user:
            # 更新使用者資訊
            user.email = user_info.email
            user.display_name = user_info.name or user_info.preferred_username or user_info.email
            user.updated_at = datetime.utcnow()
        else:
            # 建立新使用者
            user = User(
                id=str(uuid.uuid4()),
                subject_id=user_info.sub,
                email=user_info.email,
                display_name=user_info.name or user_info.preferred_username or user_info.email,
                is_active=True,
            )
            self.db_session.add(user)
        
        await self.db_session.commit()
        await self.db_session.refresh(user)
        
        return user
    
    async def logout(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        登出
        
        符合 AC-022-4：記錄登出操作
        
        Args:
            user_id: 使用者 ID
            ip_address: IP 位址（可選）
            user_agent: User Agent（可選）
        """
        # 記錄登出的稽核日誌（AC-022-4）
        audit_log = AuditLog.create(
            user_id=user_id,
            action="LOGOUT",
            resource_type="Auth",
            resource_id=None,
            details={"ip_address": ip_address},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        await self.audit_log_repository.save(audit_log)
        
        logger.info(
            "使用者登出",
            extra={
                "user_id": user_id,
                "ip_address": ip_address,
            }
        )

