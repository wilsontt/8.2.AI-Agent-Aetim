"""
系統設定 Repository 實作

實作系統設定資料存取。
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ...domain.interfaces.system_configuration_repository import ISystemConfigurationRepository
from ...infrastructure.persistence.models import SystemConfiguration


class SystemConfigurationRepository(ISystemConfigurationRepository):
    """
    系統設定 Repository 實作
    
    實作系統設定資料存取功能。
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        初始化系統設定 Repository
        
        Args:
            db_session: 資料庫 Session
        """
        self.db_session = db_session
    
    async def save(self, configuration: SystemConfiguration) -> SystemConfiguration:
        """
        儲存系統設定
        
        Args:
            configuration: 系統設定實體
        
        Returns:
            SystemConfiguration: 儲存後的系統設定實體
        """
        self.db_session.add(configuration)
        await self.db_session.commit()
        await self.db_session.refresh(configuration)
        return configuration
    
    async def get_by_key(self, key: str) -> Optional[SystemConfiguration]:
        """
        依鍵值取得系統設定
        
        Args:
            key: 設定鍵
        
        Returns:
            Optional[SystemConfiguration]: 系統設定實體，如果不存在則返回 None
        """
        result = await self.db_session.execute(
            select(SystemConfiguration).where(SystemConfiguration.key == key)
        )
        return result.scalar_one_or_none()
    
    async def get_by_category(self, category: str) -> List[SystemConfiguration]:
        """
        依類別取得系統設定清單
        
        Args:
            category: 設定類別
        
        Returns:
            List[SystemConfiguration]: 系統設定清單
        """
        result = await self.db_session.execute(
            select(SystemConfiguration)
            .where(SystemConfiguration.category == category)
            .order_by(SystemConfiguration.key)
        )
        return list(result.scalars().all())
    
    async def get_all(self) -> List[SystemConfiguration]:
        """
        取得所有系統設定
        
        Returns:
            List[SystemConfiguration]: 系統設定清單
        """
        result = await self.db_session.execute(
            select(SystemConfiguration)
            .order_by(SystemConfiguration.category, SystemConfiguration.key)
        )
        return list(result.scalars().all())
    
    async def delete(self, key: str) -> bool:
        """
        刪除系統設定
        
        Args:
            key: 設定鍵
        
        Returns:
            bool: 是否成功刪除
        """
        result = await self.db_session.execute(
            delete(SystemConfiguration).where(SystemConfiguration.key == key)
        )
        await self.db_session.commit()
        return result.rowcount > 0

