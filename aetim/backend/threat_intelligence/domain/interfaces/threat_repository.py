"""
威脅 Repository 介面

定義威脅資料持久化的抽象介面。
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from ..aggregates.threat import Threat


class IThreatRepository(ABC):
    """
    威脅 Repository 介面
    
    定義威脅資料持久化的抽象方法。
    """
    
    @abstractmethod
    async def save(self, threat: Threat) -> None:
        """
        儲存威脅（新增或更新）
        
        Args:
            threat: 威脅聚合根
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, threat_id: str) -> Optional[Threat]:
        """
        根據 ID 取得威脅
        
        Args:
            threat_id: 威脅 ID
        
        Returns:
            Threat: 威脅聚合根，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def get_by_cve(self, cve_id: str) -> Optional[Threat]:
        """
        根據 CVE 編號取得威脅
        
        Args:
            cve_id: CVE 編號
        
        Returns:
            Threat: 威脅聚合根，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def delete(self, threat_id: str) -> None:
        """
        刪除威脅
        
        Args:
            threat_id: 威脅 ID
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        threat_feed_id: Optional[str] = None,
    ) -> List[Threat]:
        """
        取得所有威脅（支援分頁和篩選）
        
        Args:
            skip: 跳過的記錄數
            limit: 返回的記錄數
            status: 狀態篩選（可選）
            threat_feed_id: 威脅情資來源 ID 篩選（可選）
        
        Returns:
            List[Threat]: 威脅列表
        """
        pass

