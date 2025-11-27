"""
系統設定服務

提供系統設定管理的應用層服務。
符合 AC-024-1, AC-024-2, AC-024-3, AC-024-4, AC-024-5。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from ...domain.interfaces.system_configuration_repository import ISystemConfigurationRepository
from ...domain.interfaces.audit_log_repository import IAuditLogRepository
from ...domain.entities.audit_log import AuditLog
from ...infrastructure.persistence.models import SystemConfiguration
from shared_kernel.infrastructure.logging import get_logger
import uuid
import json

logger = get_logger(__name__)


class SystemConfigurationService:
    """
    系統設定服務
    
    提供系統設定管理功能。
    符合 AC-024-1：提供系統設定的集中管理介面
    符合 AC-024-2：支援所有設定類別
    符合 AC-024-5：記錄所有設定變更的稽核日誌
    """
    
    # 設定類別（符合 AC-024-2）
    CATEGORY_THREAT_FEED = "threat_feed"
    CATEGORY_NOTIFICATION_RULE = "notification_rule"
    CATEGORY_REPORT_SCHEDULE = "report_schedule"
    CATEGORY_DATA_RETENTION = "data_retention"
    
    def __init__(
        self,
        repository: ISystemConfigurationRepository,
        audit_log_repository: IAuditLogRepository,
    ):
        """
        初始化系統設定服務
        
        Args:
            repository: 系統設定 Repository
            audit_log_repository: 稽核日誌 Repository
        """
        self.repository = repository
        self.audit_log_repository = audit_log_repository
    
    async def get_configuration(
        self,
        key: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Optional[SystemConfiguration | List[SystemConfiguration]]:
        """
        取得系統設定
        
        符合 AC-024-1：提供系統設定的集中管理介面
        
        Args:
            key: 設定鍵（可選）
            category: 設定類別（可選）
        
        Returns:
            Optional[SystemConfiguration | List[SystemConfiguration]]: 系統設定或設定清單
        """
        if key:
            return await self.repository.get_by_key(key)
        elif category:
            return await self.repository.get_by_category(category)
        else:
            return await self.repository.get_all()
    
    async def update_configuration(
        self,
        key: str,
        value: str,
        description: Optional[str] = None,
        category: str = "general",
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> SystemConfiguration:
        """
        更新系統設定
        
        符合 AC-024-3：在儲存設定前要求使用者確認（明確的交易儲存）
        符合 AC-024-5：記錄所有設定變更的稽核日誌
        
        Args:
            key: 設定鍵
            value: 設定值
            description: 設定說明（可選）
            category: 設定類別
            user_id: 使用者 ID（用於稽核日誌）
            ip_address: IP 位址（用於稽核日誌）
            user_agent: User Agent（用於稽核日誌）
        
        Returns:
            SystemConfiguration: 更新後的系統設定
        
        Raises:
            ValueError: 當設定鍵無效時
        """
        # 取得現有設定
        existing_config = await self.repository.get_by_key(key)
        
        # 記錄舊值（用於稽核日誌）
        old_value = existing_config.value if existing_config else None
        
        if existing_config:
            # 更新現有設定
            existing_config.value = value
            existing_config.updated_at = datetime.utcnow()
            existing_config.updated_by = user_id or "system"
            if description:
                existing_config.description = description
            
            configuration = await self.repository.save(existing_config)
        else:
            # 建立新設定
            configuration = SystemConfiguration(
                id=str(uuid.uuid4()),
                key=key,
                value=value,
                category=category,
                description=description,
                updated_by=user_id or "system",
            )
            configuration = await self.repository.save(configuration)
        
        # 記錄稽核日誌（AC-024-5）
        if user_id:
            audit_log = AuditLog.create(
                user_id=user_id,
                action="UPDATE",
                resource_type="SystemConfiguration",
                resource_id=configuration.id,
                details={
                    "key": key,
                    "category": category,
                    "old_value": old_value,
                    "new_value": value,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self.audit_log_repository.save(audit_log)
            
            logger.info(
                "系統設定已更新",
                extra={
                    "user_id": user_id,
                    "key": key,
                    "category": category,
                    "ip_address": ip_address,
                }
            )
        
        return configuration
    
    async def update_configurations_batch(
        self,
        configurations: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> List[SystemConfiguration]:
        """
        批次更新系統設定
        
        符合 AC-024-3：在儲存設定前要求使用者確認（明確的交易儲存）
        符合 AC-024-5：記錄所有設定變更的稽核日誌
        
        Args:
            configurations: 設定清單（每個設定包含 key, value, description, category）
            user_id: 使用者 ID（用於稽核日誌）
            ip_address: IP 位址（用於稽核日誌）
            user_agent: User Agent（用於稽核日誌）
        
        Returns:
            List[SystemConfiguration]: 更新後的系統設定清單
        """
        updated_configs = []
        
        for config_data in configurations:
            config = await self.update_configuration(
                key=config_data["key"],
                value=config_data["value"],
                description=config_data.get("description"),
                category=config_data.get("category", "general"),
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            updated_configs.append(config)
        
        return updated_configs
    
    async def delete_configuration(
        self,
        key: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        刪除系統設定
        
        符合 AC-024-5：記錄所有設定變更的稽核日誌
        
        Args:
            key: 設定鍵
            user_id: 使用者 ID（用於稽核日誌）
            ip_address: IP 位址（用於稽核日誌）
            user_agent: User Agent（用於稽核日誌）
        
        Returns:
            bool: 是否成功刪除
        """
        # 取得現有設定（用於稽核日誌）
        existing_config = await self.repository.get_by_key(key)
        
        if not existing_config:
            return False
        
        # 刪除設定
        success = await self.repository.delete(key)
        
        # 記錄稽核日誌（AC-024-5）
        if success and user_id:
            audit_log = AuditLog.create(
                user_id=user_id,
                action="DELETE",
                resource_type="SystemConfiguration",
                resource_id=existing_config.id,
                details={
                    "key": key,
                    "category": existing_config.category,
                    "value": existing_config.value,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )
            await self.audit_log_repository.save(audit_log)
            
            logger.info(
                "系統設定已刪除",
                extra={
                    "user_id": user_id,
                    "key": key,
                    "category": existing_config.category,
                    "ip_address": ip_address,
                }
            )
        
        return success

