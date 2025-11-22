"""
PIR Repository 介面

定義 PIR Repository 的抽象介面，實作將在 Infrastructure Layer。
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from ..aggregates.pir import PIR


class IPIRRepository(ABC):
    """
    PIR Repository 介面
    
    定義 PIR 的持久化操作，實作將在 Infrastructure Layer。
    """
    
    @abstractmethod
    async def save(self, pir: PIR) -> None:
        """
        儲存 PIR（新增或更新）
        
        Args:
            pir: PIR 聚合根
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, pir_id: str) -> Optional[PIR]:
        """
        依 ID 查詢 PIR
        
        Args:
            pir_id: PIR ID
        
        Returns:
            PIR: PIR 聚合根，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def delete(self, pir_id: str) -> None:
        """
        刪除 PIR
        
        Args:
            pir_id: PIR ID
        
        Raises:
            ValueError: 當 PIR 不存在時
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> tuple[List[PIR], int]:
        """
        查詢所有 PIR（支援分頁與排序）
        
        Args:
            page: 頁碼（從 1 開始）
            page_size: 每頁筆數（預設 20）
            sort_by: 排序欄位（name、priority、created_at 等）
            sort_order: 排序方向（asc、desc）
        
        Returns:
            tuple[List[PIR], int]: (PIR 清單, 總筆數)
        """
        pass
    
    @abstractmethod
    async def get_enabled_pirs(self) -> List[PIR]:
        """
        查詢啟用的 PIR
        
        Returns:
            List[PIR]: 啟用的 PIR 清單
        """
        pass
    
    @abstractmethod
    async def find_matching_pirs(self, threat_data: dict) -> List[PIR]:
        """
        查詢符合威脅資料的 PIR
        
        Args:
            threat_data: 威脅資料字典（包含 cve、product_name、threat_type 等）
        
        Returns:
            List[PIR]: 符合條件的 PIR 清單（僅包含啟用的 PIR）
        """
        pass

