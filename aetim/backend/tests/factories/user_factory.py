"""
使用者與角色測試資料工廠
"""

import uuid
from datetime import datetime
from typing import Optional

from system_management.infrastructure.persistence.models import (
    User,
    Role,
    Permission,
    UserRole,
    RolePermission,
)


class UserFactory:
    """使用者測試資料工廠"""

    @staticmethod
    def create(
        subject_id: Optional[str] = None,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
        is_active: Optional[bool] = None,
        **kwargs
    ) -> User:
        """建立測試用使用者"""
        item = kwargs.get("item", 1)
        return User(
            id=str(uuid.uuid4()),
            subject_id=subject_id or f"sub-{item:03d}",
            email=email or f"user{item}@example.com",
            display_name=display_name or f"Test User {item}",
            is_active=is_active if is_active is not None else True,
            last_login_at=kwargs.get("last_login_at"),
            created_at=kwargs.get("created_at", datetime.utcnow()),
            updated_at=kwargs.get("updated_at", datetime.utcnow()),
        )

    @staticmethod
    def create_ciso(**kwargs) -> User:
        """建立 CISO 使用者"""
        return UserFactory.create(
            subject_id=kwargs.get("subject_id", "sub-ciso"),
            email=kwargs.get("email", "ciso@example.com"),
            display_name=kwargs.get("display_name", "CISO"),
            **kwargs
        )

    @staticmethod
    def create_it_admin(**kwargs) -> User:
        """建立 IT 管理員使用者"""
        return UserFactory.create(
            subject_id=kwargs.get("subject_id", "sub-itadmin"),
            email=kwargs.get("email", "itadmin@example.com"),
            display_name=kwargs.get("display_name", "IT Administrator"),
            **kwargs
        )

    @staticmethod
    def create_analyst(**kwargs) -> User:
        """建立分析師使用者"""
        return UserFactory.create(
            subject_id=kwargs.get("subject_id", "sub-analyst"),
            email=kwargs.get("email", "analyst@example.com"),
            display_name=kwargs.get("display_name", "Security Analyst"),
            **kwargs
        )


class RoleFactory:
    """角色測試資料工廠"""

    @staticmethod
    def create(
        name: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> Role:
        """建立測試用角色"""
        return Role(
            id=str(uuid.uuid4()),
            name=name or "Test Role",
            description=description or "Test role description",
            created_at=kwargs.get("created_at", datetime.utcnow()),
            updated_at=kwargs.get("updated_at", datetime.utcnow()),
        )

    @staticmethod
    def create_ciso(**kwargs) -> Role:
        """建立 CISO 角色"""
        return RoleFactory.create(
            name="CISO",
            description="Chief Information Security Officer",
            **kwargs
        )

    @staticmethod
    def create_it_admin(**kwargs) -> Role:
        """建立 IT 管理員角色"""
        return RoleFactory.create(
            name="IT_Admin",
            description="IT Administrator",
            **kwargs
        )

    @staticmethod
    def create_analyst(**kwargs) -> Role:
        """建立分析師角色"""
        return RoleFactory.create(
            name="Analyst",
            description="Security Analyst",
            **kwargs
        )

    @staticmethod
    def create_viewer(**kwargs) -> Role:
        """建立檢視者角色"""
        return RoleFactory.create(
            name="Viewer",
            description="Viewer (Read-only)",
            **kwargs
        )


class PermissionFactory:
    """權限測試資料工廠"""

    @staticmethod
    def create(
        name: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        **kwargs
    ) -> Permission:
        """建立測試用權限"""
        return Permission(
            id=str(uuid.uuid4()),
            name=name or f"{resource or 'asset'}:{action or 'read'}",
            resource=resource or "asset",
            action=action or "read",
            created_at=kwargs.get("created_at", datetime.utcnow()),
        )

    @staticmethod
    def create_read(**kwargs) -> Permission:
        """建立讀取權限"""
        return PermissionFactory.create(
            action="read",
            **kwargs
        )

    @staticmethod
    def create_write(**kwargs) -> Permission:
        """建立寫入權限"""
        return PermissionFactory.create(
            action="write",
            **kwargs
        )

    @staticmethod
    def create_delete(**kwargs) -> Permission:
        """建立刪除權限"""
        return PermissionFactory.create(
            action="delete",
            **kwargs
        )

