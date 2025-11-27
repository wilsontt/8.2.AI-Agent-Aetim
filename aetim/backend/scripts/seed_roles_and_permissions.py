"""
角色與權限種子資料腳本

初始化系統的角色和權限資料。
符合 AC-023-2：定義所有角色（CISO、IT Admin、Analyst、Viewer）
"""

import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from system_management.infrastructure.persistence.models import Role, Permission, RolePermission
from system_management.domain.value_objects.role_name import RoleName
from system_management.domain.value_objects.permission_name import PermissionName
from shared_kernel.infrastructure.database import get_database_url
import uuid


# 角色定義（符合 AC-023-2）
ROLES = [
    {
        "name": RoleName.CISO.value,
        "description": "資安官：完整存取權限（檢視、設定、管理）",
    },
    {
        "name": RoleName.IT_ADMIN.value,
        "description": "IT 管理員：資產管理、排程設定、工單檢視",
    },
    {
        "name": RoleName.ANALYST.value,
        "description": "資安分析師：檢視威脅情資、分析結果、報告",
    },
    {
        "name": RoleName.VIEWER.value,
        "description": "唯讀使用者：僅能檢視報告與威脅情資",
    },
]

# 權限定義
PERMISSIONS = [
    # 資產管理
    {"name": PermissionName.ASSET_VIEW.value, "resource": "Asset", "action": "Read"},
    {"name": PermissionName.ASSET_CREATE.value, "resource": "Asset", "action": "Write"},
    {"name": PermissionName.ASSET_UPDATE.value, "resource": "Asset", "action": "Write"},
    {"name": PermissionName.ASSET_DELETE.value, "resource": "Asset", "action": "Delete"},
    {"name": PermissionName.ASSET_IMPORT.value, "resource": "Asset", "action": "Write"},
    # PIR 管理
    {"name": PermissionName.PIR_VIEW.value, "resource": "PIR", "action": "Read"},
    {"name": PermissionName.PIR_CREATE.value, "resource": "PIR", "action": "Write"},
    {"name": PermissionName.PIR_UPDATE.value, "resource": "PIR", "action": "Write"},
    {"name": PermissionName.PIR_DELETE.value, "resource": "PIR", "action": "Delete"},
    {"name": PermissionName.PIR_TOGGLE.value, "resource": "PIR", "action": "Write"},
    # 威脅情資來源管理
    {"name": PermissionName.THREAT_FEED_VIEW.value, "resource": "ThreatFeed", "action": "Read"},
    {"name": PermissionName.THREAT_FEED_CREATE.value, "resource": "ThreatFeed", "action": "Write"},
    {"name": PermissionName.THREAT_FEED_UPDATE.value, "resource": "ThreatFeed", "action": "Write"},
    {"name": PermissionName.THREAT_FEED_DELETE.value, "resource": "ThreatFeed", "action": "Delete"},
    {"name": PermissionName.THREAT_FEED_TOGGLE.value, "resource": "ThreatFeed", "action": "Write"},
    # 威脅情資
    {"name": PermissionName.THREAT_VIEW.value, "resource": "Threat", "action": "Read"},
    # 關聯分析
    {"name": PermissionName.ASSOCIATION_VIEW.value, "resource": "Association", "action": "Read"},
    # 風險評估
    {"name": PermissionName.RISK_ASSESSMENT_VIEW.value, "resource": "RiskAssessment", "action": "Read"},
    # 報告
    {"name": PermissionName.REPORT_VIEW.value, "resource": "Report", "action": "Read"},
    {"name": PermissionName.REPORT_CREATE.value, "resource": "Report", "action": "Write"},
    {"name": PermissionName.REPORT_DOWNLOAD.value, "resource": "Report", "action": "Read"},
    # IT 工單
    {"name": PermissionName.TICKET_VIEW.value, "resource": "Ticket", "action": "Read"},
    {"name": PermissionName.TICKET_EXPORT.value, "resource": "Ticket", "action": "Read"},
    {"name": PermissionName.TICKET_UPDATE_STATUS.value, "resource": "Ticket", "action": "Write"},
    # 通知規則
    {"name": PermissionName.NOTIFICATION_RULE_VIEW.value, "resource": "NotificationRule", "action": "Read"},
    {"name": PermissionName.NOTIFICATION_RULE_CREATE.value, "resource": "NotificationRule", "action": "Write"},
    {"name": PermissionName.NOTIFICATION_RULE_UPDATE.value, "resource": "NotificationRule", "action": "Write"},
    {"name": PermissionName.NOTIFICATION_RULE_DELETE.value, "resource": "NotificationRule", "action": "Delete"},
    # 系統設定
    {"name": PermissionName.SYSTEM_CONFIG_VIEW.value, "resource": "SystemConfig", "action": "Read"},
    {"name": PermissionName.SYSTEM_CONFIG_UPDATE.value, "resource": "SystemConfig", "action": "Write"},
    # 排程管理
    {"name": PermissionName.SCHEDULE_VIEW.value, "resource": "Schedule", "action": "Read"},
    {"name": PermissionName.SCHEDULE_CREATE.value, "resource": "Schedule", "action": "Write"},
    {"name": PermissionName.SCHEDULE_UPDATE.value, "resource": "Schedule", "action": "Write"},
    {"name": PermissionName.SCHEDULE_DELETE.value, "resource": "Schedule", "action": "Delete"},
    {"name": PermissionName.SCHEDULE_TRIGGER.value, "resource": "Schedule", "action": "Write"},
    # 稽核日誌
    {"name": PermissionName.AUDIT_LOG_VIEW.value, "resource": "AuditLog", "action": "Read"},
]

# 角色與權限對應關係
ROLE_PERMISSIONS = {
    RoleName.CISO.value: [
        # 所有權限
        PermissionName.ASSET_VIEW.value,
        PermissionName.ASSET_CREATE.value,
        PermissionName.ASSET_UPDATE.value,
        PermissionName.ASSET_DELETE.value,
        PermissionName.ASSET_IMPORT.value,
        PermissionName.PIR_VIEW.value,
        PermissionName.PIR_CREATE.value,
        PermissionName.PIR_UPDATE.value,
        PermissionName.PIR_DELETE.value,
        PermissionName.PIR_TOGGLE.value,
        PermissionName.THREAT_FEED_VIEW.value,
        PermissionName.THREAT_FEED_CREATE.value,
        PermissionName.THREAT_FEED_UPDATE.value,
        PermissionName.THREAT_FEED_DELETE.value,
        PermissionName.THREAT_FEED_TOGGLE.value,
        PermissionName.THREAT_VIEW.value,
        PermissionName.ASSOCIATION_VIEW.value,
        PermissionName.RISK_ASSESSMENT_VIEW.value,
        PermissionName.REPORT_VIEW.value,
        PermissionName.REPORT_CREATE.value,
        PermissionName.REPORT_DOWNLOAD.value,
        PermissionName.TICKET_VIEW.value,
        PermissionName.TICKET_EXPORT.value,
        PermissionName.TICKET_UPDATE_STATUS.value,
        PermissionName.NOTIFICATION_RULE_VIEW.value,
        PermissionName.NOTIFICATION_RULE_CREATE.value,
        PermissionName.NOTIFICATION_RULE_UPDATE.value,
        PermissionName.NOTIFICATION_RULE_DELETE.value,
        PermissionName.SYSTEM_CONFIG_VIEW.value,
        PermissionName.SYSTEM_CONFIG_UPDATE.value,
        PermissionName.SCHEDULE_VIEW.value,
        PermissionName.SCHEDULE_CREATE.value,
        PermissionName.SCHEDULE_UPDATE.value,
        PermissionName.SCHEDULE_DELETE.value,
        PermissionName.SCHEDULE_TRIGGER.value,
        PermissionName.AUDIT_LOG_VIEW.value,
    ],
    RoleName.IT_ADMIN.value: [
        # 資產管理、排程設定、工單檢視
        PermissionName.ASSET_VIEW.value,
        PermissionName.ASSET_CREATE.value,
        PermissionName.ASSET_UPDATE.value,
        PermissionName.ASSET_DELETE.value,
        PermissionName.ASSET_IMPORT.value,
        PermissionName.THREAT_VIEW.value,
        PermissionName.REPORT_VIEW.value,
        PermissionName.TICKET_VIEW.value,
        PermissionName.TICKET_EXPORT.value,
        PermissionName.TICKET_UPDATE_STATUS.value,
        PermissionName.SCHEDULE_VIEW.value,
        PermissionName.SCHEDULE_CREATE.value,
        PermissionName.SCHEDULE_UPDATE.value,
        PermissionName.SCHEDULE_DELETE.value,
        PermissionName.SCHEDULE_TRIGGER.value,
    ],
    RoleName.ANALYST.value: [
        # 檢視威脅情資、分析結果、報告
        PermissionName.THREAT_VIEW.value,
        PermissionName.ASSOCIATION_VIEW.value,
        PermissionName.RISK_ASSESSMENT_VIEW.value,
        PermissionName.REPORT_VIEW.value,
        PermissionName.REPORT_DOWNLOAD.value,
    ],
    RoleName.VIEWER.value: [
        # 僅能檢視報告與威脅情資
        PermissionName.REPORT_VIEW.value,
        PermissionName.REPORT_DOWNLOAD.value,
        PermissionName.THREAT_VIEW.value,
    ],
}


async def seed_roles_and_permissions():
    """初始化角色和權限"""
    database_url = get_database_url()
    engine = create_async_engine(database_url)
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session_maker() as session:
        # 建立角色
        role_map = {}
        for role_data in ROLES:
            # 檢查角色是否已存在
            from sqlalchemy import select
            result = await session.execute(
                select(Role).where(Role.name == role_data["name"])
            )
            existing_role = result.scalar_one_or_none()
            
            if existing_role:
                role_map[role_data["name"]] = existing_role
                print(f"角色已存在：{role_data['name']}")
            else:
                role = Role(
                    id=str(uuid.uuid4()),
                    name=role_data["name"],
                    description=role_data["description"],
                )
                session.add(role)
                role_map[role_data["name"]] = role
                print(f"建立角色：{role_data['name']}")
        
        await session.commit()
        
        # 建立權限
        permission_map = {}
        for permission_data in PERMISSIONS:
            # 檢查權限是否已存在
            from sqlalchemy import select
            result = await session.execute(
                select(Permission).where(Permission.name == permission_data["name"])
            )
            existing_permission = result.scalar_one_or_none()
            
            if existing_permission:
                permission_map[permission_data["name"]] = existing_permission
                print(f"權限已存在：{permission_data['name']}")
            else:
                permission = Permission(
                    id=str(uuid.uuid4()),
                    name=permission_data["name"],
                    resource=permission_data["resource"],
                    action=permission_data["action"],
                )
                session.add(permission)
                permission_map[permission_data["name"]] = permission
                print(f"建立權限：{permission_data['name']}")
        
        await session.commit()
        
        # 建立角色與權限關聯
        for role_name, permission_names in ROLE_PERMISSIONS.items():
            role = role_map[role_name]
            
            for permission_name in permission_names:
                permission = permission_map[permission_name]
                
                # 檢查關聯是否已存在
                from sqlalchemy import select
                result = await session.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == permission.id,
                    )
                )
                existing_relation = result.scalar_one_or_none()
                
                if not existing_relation:
                    role_permission = RolePermission(
                        role_id=role.id,
                        permission_id=permission.id,
                    )
                    session.add(role_permission)
                    print(f"建立角色權限關聯：{role_name} -> {permission_name}")
        
        await session.commit()
        print("角色與權限初始化完成！")


if __name__ == "__main__":
    asyncio.run(seed_roles_and_permissions())

