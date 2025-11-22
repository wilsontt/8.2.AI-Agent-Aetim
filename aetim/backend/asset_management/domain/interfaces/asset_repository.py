"""
資產 Repository 介面

定義資產 Repository 的抽象介面，實作將在 Infrastructure Layer。
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from ..aggregates.asset import Asset


class IAssetRepository(ABC):
    """
    資產 Repository 介面
    
    定義資產的持久化操作，實作將在 Infrastructure Layer。
    """
    
    @abstractmethod
    async def save(self, asset: Asset) -> None:
        """
        儲存資產（新增或更新）
        
        Args:
            asset: 資產聚合根
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, asset_id: str) -> Optional[Asset]:
        """
        依 ID 查詢資產
        
        Args:
            asset_id: 資產 ID
        
        Returns:
            Asset: 資產聚合根，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def delete(self, asset_id: str) -> None:
        """
        刪除資產
        
        Args:
            asset_id: 資產 ID
        
        Raises:
            ValueError: 當資產不存在時
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> tuple[List[Asset], int]:
        """
        查詢所有資產（支援分頁與排序）
        
        Args:
            page: 頁碼（從 1 開始）
            page_size: 每頁筆數（預設 20，至少 20）
            sort_by: 排序欄位（host_name、owner、created_at 等）
            sort_order: 排序方向（asc、desc）
        
        Returns:
            tuple[List[Asset], int]: (資產清單, 總筆數)
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        product_name: Optional[str] = None,
        product_version: Optional[str] = None,
        product_type: Optional[str] = None,
        is_public_facing: Optional[bool] = None,
        data_sensitivity: Optional[str] = None,
        business_criticality: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> tuple[List[Asset], int]:
        """
        搜尋資產（支援多條件篩選）
        
        Args:
            product_name: 產品名稱（模糊搜尋）
            product_version: 產品版本（模糊搜尋）
            product_type: 產品類型（OS/Application）
            is_public_facing: 是否對外暴露
            data_sensitivity: 資料敏感度（高/中/低）
            business_criticality: 業務關鍵性（高/中/低）
            page: 頁碼（從 1 開始）
            page_size: 每頁筆數（預設 20）
            sort_by: 排序欄位
            sort_order: 排序方向（asc、desc）
        
        Returns:
            tuple[List[Asset], int]: (資產清單, 總筆數)
        """
        pass

