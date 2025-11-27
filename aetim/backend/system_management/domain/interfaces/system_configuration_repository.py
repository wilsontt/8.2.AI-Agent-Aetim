"""
系統設定 Repository 介面

定義系統設定資料存取的抽象介面。
"""

from typing import List, Optional
from abc import ABC, abstractmethod
from ...infrastructure.persistence.models import SystemConfiguration


class ISystemConfigurationRepository(ABC):
    """
    系統設定 Repository 介面
    
    定義系統設定資料存取的抽象方法。
    """
    
    @abstractmethod
    async def save(self, configuration: SystemConfiguration) -> SystemConfiguration:
        """
        儲存系統設定
        
        Args:
            configuration: 系統設定實體
        
        Returns:
            SystemConfiguration: 儲存後的系統設定實體
        """
        pass
    
    @abstractmethod
    async def get_by_key(self, key: str) -> Optional[SystemConfiguration]:
        """
        依鍵值取得系統設定
        
        Args:
            key: 設定鍵
        
        Returns:
            Optional[SystemConfiguration]: 系統設定實體，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def get_by_category(self, category: str) -> List[SystemConfiguration]:
        """
        依類別取得系統設定清單
        
        Args:
            category: 設定類別
        
        Returns:
            List[SystemConfiguration]: 系統設定清單
        """
        pass
    
    @abstractmethod
    async def get_all(self) -> List[SystemConfiguration]:
        """
        取得所有系統設定
        
        Returns:
            List[SystemConfiguration]: 系統設定清單
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        刪除系統設定
        
        Args:
            key: 設定鍵
        
        Returns:
            bool: 是否成功刪除
        """
        pass

