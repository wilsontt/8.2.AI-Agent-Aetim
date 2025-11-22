"""
威脅情資來源 Repository 介面

定義 ThreatFeed Repository 的抽象介面，實作將在 Infrastructure Layer。
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from ..aggregates.threat_feed import ThreatFeed


class IThreatFeedRepository(ABC):
    """
    威脅情資來源 Repository 介面
    
    定義 ThreatFeed 的持久化操作，實作將在 Infrastructure Layer。
    """
    
    @abstractmethod
    async def save(self, threat_feed: ThreatFeed) -> None:
        """
        儲存威脅情資來源（新增或更新）
        
        Args:
            threat_feed: 威脅情資來源聚合根
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, threat_feed_id: str) -> Optional[ThreatFeed]:
        """
        依 ID 查詢威脅情資來源
        
        Args:
            threat_feed_id: 威脅情資來源 ID
        
        Returns:
            ThreatFeed: 威脅情資來源聚合根，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[ThreatFeed]:
        """
        依名稱查詢威脅情資來源
        
        Args:
            name: 威脅情資來源名稱
        
        Returns:
            ThreatFeed: 威脅情資來源聚合根，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def delete(self, threat_feed_id: str) -> None:
        """
        刪除威脅情資來源
        
        Args:
            threat_feed_id: 威脅情資來源 ID
        
        Raises:
            ValueError: 當威脅情資來源不存在時
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> tuple[List[ThreatFeed], int]:
        """
        查詢所有威脅情資來源（支援分頁與排序）
        
        Args:
            page: 頁碼（從 1 開始）
            page_size: 每頁筆數（預設 20）
            sort_by: 排序欄位（name、priority、created_at 等）
            sort_order: 排序方向（asc、desc）
        
        Returns:
            tuple[List[ThreatFeed], int]: (威脅情資來源清單, 總筆數)
        """
        pass
    
    @abstractmethod
    async def get_enabled_feeds(self) -> List[ThreatFeed]:
        """
        查詢啟用的威脅情資來源
        
        Returns:
            List[ThreatFeed]: 啟用的威脅情資來源清單（依優先級排序）
        """
        pass
    
    @abstractmethod
    async def get_feeds_by_priority(self, priority: str) -> List[ThreatFeed]:
        """
        查詢指定優先級的威脅情資來源
        
        Args:
            priority: 優先級（P0/P1/P2/P3）
        
        Returns:
            List[ThreatFeed]: 威脅情資來源清單
        """
        pass

