"""
系統管理模組資料模型

實作系統管理相關的資料庫模型，符合 plan.md 第 4.2.5 節的設計。
"""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Index,
    UniqueConstraint,
    Table,
)
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from shared_kernel.infrastructure.database import Base


class User(Base):
    """使用者表"""

    __tablename__ = "users"

    # 主鍵
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 身份資訊
    subject_id = Column(String(200), nullable=False, unique=True, comment="IdP 提供的 Subject ID")
    email = Column(String(200), nullable=False, unique=True, comment="Email 地址")
    display_name = Column(String(200), nullable=False, comment="顯示名稱")

    # 狀態
    is_active = Column(Boolean, nullable=False, default=True, comment="是否啟用")
    last_login_at = Column(DateTime, nullable=True, comment="最後登入時間")

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

    # 索引
    __table_args__ = (
        Index("IX_Users_SubjectId", "subject_id"),
        Index("IX_Users_Email", "email"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Role(Base):
    """角色表"""

    __tablename__ = "roles"

    # 主鍵
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 角色資訊
    name = Column(
        String(100),
        nullable=False,
        unique=True,
        comment="角色名稱（CISO/IT_Admin/Analyst/Viewer）",
    )
    description = Column(String(500), nullable=True, comment="角色描述")

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    role_permissions = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class UserRole(Base):
    """使用者角色關聯表"""

    __tablename__ = "user_roles"

    # 複合主鍵
    user_id = Column(
        CHAR(36),
        ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        comment="使用者 ID",
    )
    role_id = Column(
        CHAR(36),
        ForeignKey("roles.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        comment="角色 ID",
    )

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 關聯
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")

    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


class Permission(Base):
    """權限表"""

    __tablename__ = "permissions"

    # 主鍵
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 權限資訊
    name = Column(String(100), nullable=False, unique=True, comment="權限名稱")
    resource = Column(String(200), nullable=False, comment="資源名稱")
    action = Column(String(50), nullable=False, comment="動作（Read/Write/Delete）")

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 關聯
    role_permissions = relationship(
        "RolePermission", back_populates="permission", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Permission(id={self.id}, name={self.name})>"


class RolePermission(Base):
    """角色權限關聯表"""

    __tablename__ = "role_permissions"

    # 複合主鍵
    role_id = Column(
        CHAR(36),
        ForeignKey("roles.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        comment="角色 ID",
    )
    permission_id = Column(
        CHAR(36),
        ForeignKey("permissions.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
        comment="權限 ID",
    )

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 關聯
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")

    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"


class SystemConfiguration(Base):
    """系統設定表"""

    __tablename__ = "system_configurations"

    # 主鍵
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 設定資訊
    key = Column(String(200), nullable=False, unique=True, comment="設定鍵")
    value = Column(Text, nullable=True, comment="設定值")
    category = Column(String(100), nullable=False, comment="設定類別")
    description = Column(String(500), nullable=True, comment="設定說明")

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), nullable=False, default="system")

    # 索引
    __table_args__ = (
        Index("IX_SystemConfigurations_Key", "key"),
        Index("IX_SystemConfigurations_Category", "category"),
    )

    def __repr__(self):
        return f"<SystemConfiguration(id={self.id}, key={self.key})>"


class Schedule(Base):
    """排程表"""

    __tablename__ = "schedules"

    # 主鍵
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 排程資訊
    name = Column(String(200), nullable=False, comment="排程名稱")
    schedule_type = Column(
        String(50), nullable=False, comment="排程類型（ThreatCollection/ReportGeneration）"
    )
    cron_expression = Column(String(100), nullable=False, comment="Cron 表達式")
    is_enabled = Column(Boolean, nullable=False, default=True, comment="是否啟用")

    # 執行狀態
    last_run_time = Column(DateTime, nullable=True, comment="最後執行時間")
    next_run_time = Column(DateTime, nullable=True, comment="下次執行時間")
    last_run_status = Column(String(20), nullable=True, comment="最後執行狀態")

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=False, default="system")
    updated_by = Column(String(100), nullable=False, default="system")

    # 索引
    __table_args__ = (
        Index("IX_Schedules_ScheduleType", "schedule_type"),
        Index("IX_Schedules_IsEnabled", "is_enabled"),
        Index("IX_Schedules_NextRunTime", "next_run_time"),
    )

    def __repr__(self):
        return f"<Schedule(id={self.id}, name={self.name}, schedule_type={self.schedule_type})>"


class AuditLog(Base):
    """稽核日誌表"""

    __tablename__ = "audit_logs"

    # 主鍵
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 外鍵
    user_id = Column(
        CHAR(36),
        ForeignKey("users.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        comment="使用者 ID",
    )

    # 操作資訊
    action = Column(String(50), nullable=False, comment="操作類型（Create/Update/Delete/View）")
    resource_type = Column(String(100), nullable=False, comment="資源類型（Asset/Threat/Report 等）")
    resource_id = Column(CHAR(36), nullable=True, comment="資源 ID")
    details = Column(Text, nullable=True, comment="操作詳情（JSON 格式）")

    # 請求資訊
    ip_address = Column(String(50), nullable=True, comment="IP 位址")
    user_agent = Column(String(500), nullable=True, comment="User Agent")

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 關聯
    user = relationship("User", back_populates="audit_logs")

    # 索引
    __table_args__ = (
        Index("IX_AuditLogs_UserId", "user_id"),
        Index("IX_AuditLogs_ResourceType", "resource_type"),
        Index("IX_AuditLogs_CreatedAt", "created_at"),
        Index("IX_AuditLogs_UserId_CreatedAt", "user_id", "created_at"),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, resource_type={self.resource_type})>"

