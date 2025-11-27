"""
授權服務

提供角色基礎存取控制 (RBAC) 功能。
符合 AC-023-1, AC-023-2, AC-023-4, AC-023-5。
"""

from typing import List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...infrastructure.persistence.models import User, Role, Permission, UserRole, RolePermission
from ...domain.value_objects.role_name import RoleName
from ...domain.value_objects.permission_name import PermissionName
from ...domain.interfaces.audit_log_repository import IAuditLogRepository
from ...domain.entities.audit_log import AuditLog
from shared_kernel.infrastructure.logging import get_logger
import uuid

logger = get_logger(__name__)


class AuthorizationService:
    """
    授權服務
    
    提供角色基礎存取控制 (RBAC) 功能。
    符合 AC-023-1：實作角色基礎存取控制 (RBAC)
    符合 AC-023-2：定義所有角色（CISO、IT Admin、Analyst、Viewer）
    符合 AC-023-4：在 API 層級驗證權限，防止未授權存取
    符合 AC-023-5：記錄所有權限驗證失敗的稽核日誌
    """
    
    def __init__(
        self,
        db_session: AsyncSession,
        audit_log_repository: IAuditLogRepository,
    ):
        """
        初始化授權服務
        
        Args:
            db_session: 資料庫 Session
            audit_log_repository: 稽核日誌 Repository
        """
        self.db_session = db_session
        self.audit_log_repository = audit_log_repository
    
    async def get_user_roles(self, user_id: str) -> List[str]:
        """
        取得使用者角色
        
        Args:
            user_id: 使用者 ID
        
        Returns:
            List[str]: 角色名稱清單
        """
        result = await self.db_session.execute(
            select(Role.name)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        return [row[0] for row in result.fetchall()]
    
    async def get_role_permissions(self, role_name: str) -> Set[str]:
        """
        取得角色權限
        
        Args:
            role_name: 角色名稱
        
        Returns:
            Set[str]: 權限名稱集合
        """
        result = await self.db_session.execute(
            select(Permission.name)
            .join(RolePermission, Permission.id == RolePermission.permission_id)
            .join(Role, Role.id == RolePermission.role_id)
            .where(Role.name == role_name)
        )
        return {row[0] for row in result.fetchall()}
    
    async def get_user_permissions(self, user_id: str) -> Set[str]:
        """
        取得使用者權限（所有角色的權限聯集）
        
        Args:
            user_id: 使用者 ID
        
        Returns:
            Set[str]: 權限名稱集合
        """
        # 取得使用者角色
        roles = await self.get_user_roles(user_id)
        
        # 取得所有角色的權限
        all_permissions: Set[str] = set()
        for role_name in roles:
            permissions = await self.get_role_permissions(role_name)
            all_permissions.update(permissions)
        
        return all_permissions
    
    async def check_permission(
        self,
        user_id: str,
        permission: str,
        resource_type: str = "Auth",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        檢查使用者是否有特定權限
        
        符合 AC-023-4：在 API 層級驗證權限，防止未授權存取
        符合 AC-023-5：記錄所有權限驗證失敗的稽核日誌
        
        Args:
            user_id: 使用者 ID
            permission: 權限名稱
            resource_type: 資源類型（用於稽核日誌）
            ip_address: IP 位址（可選）
            user_agent: User Agent（可選）
        
        Returns:
            bool: 是否有權限
        """
        # 取得使用者權限
        user_permissions = await self.get_user_permissions(user_id)
        
        # 檢查權限
        has_permission = permission in user_permissions
        
        # 如果沒有權限，記錄稽核日誌（AC-023-5）
        if not has_permission:
            audit_log = AuditLog.create(
                user_id=user_id,
                action="VIEW",
                resource_type=resource_type,
                resource_id=None,
                details={
                    "permission": permission,
                    "status": "denied",
                    "ip_address": ip_address,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self.audit_log_repository.save(audit_log)
            
            logger.warning(
                "權限驗證失敗",
                extra={
                    "user_id": user_id,
                    "permission": permission,
                    "resource_type": resource_type,
                    "ip_address": ip_address,
                }
            )
        
        return has_permission
    
    async def check_role(
        self,
        user_id: str,
        role_name: str,
        resource_type: str = "Auth",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        檢查使用者是否有特定角色
        
        符合 AC-023-4：在 API 層級驗證權限，防止未授權存取
        符合 AC-023-5：記錄所有權限驗證失敗的稽核日誌
        
        Args:
            user_id: 使用者 ID
            role_name: 角色名稱
            resource_type: 資源類型（用於稽核日誌）
            ip_address: IP 位址（可選）
            user_agent: User Agent（可選）
        
        Returns:
            bool: 是否有角色
        """
        # 取得使用者角色
        user_roles = await self.get_user_roles(user_id)
        
        # 檢查角色
        has_role = role_name in user_roles
        
        # 如果沒有角色，記錄稽核日誌（AC-023-5）
        if not has_role:
            audit_log = AuditLog.create(
                user_id=user_id,
                action="VIEW",
                resource_type=resource_type,
                resource_id=None,
                details={
                    "role": role_name,
                    "status": "denied",
                    "ip_address": ip_address,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self.audit_log_repository.save(audit_log)
            
            logger.warning(
                "角色驗證失敗",
                extra={
                    "user_id": user_id,
                    "role": role_name,
                    "resource_type": resource_type,
                    "ip_address": ip_address,
                }
            )
        
        return has_role

