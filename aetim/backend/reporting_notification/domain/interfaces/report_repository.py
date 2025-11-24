"""
報告 Repository 介面

定義報告資料存取的抽象介面。
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..aggregates.report import Report
from ..value_objects.report_type import ReportType


class IReportRepository(ABC):
    """
    報告 Repository 介面
    
    定義報告資料存取的抽象方法。
    """
    
    @abstractmethod
    async def save(self, report: Report, file_content: bytes) -> None:
        """
        儲存報告記錄和檔案
        
        Args:
            report: 報告聚合根
            file_content: 報告檔案內容（位元組）
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, report_id: str) -> Optional[Report]:
        """
        依 ID 查詢報告
        
        Args:
            report_id: 報告 ID
        
        Returns:
            Optional[Report]: 報告聚合根，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def get_all(
        self,
        report_type: Optional[ReportType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "generated_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """
        查詢所有報告（支援分頁、排序、篩選）
        
        Args:
            report_type: 報告類型篩選（可選）
            start_date: 開始日期篩選（可選）
            end_date: 結束日期篩選（可選）
            page: 頁碼（從 1 開始）
            page_size: 每頁數量
            sort_by: 排序欄位（預設：generated_at）
            sort_order: 排序順序（asc/desc，預設：desc）
        
        Returns:
            Dict[str, Any]: 包含 items（報告清單）、total（總數）、page、page_size、total_pages
        """
        pass
    
    @abstractmethod
    async def get_file_path(self, report_id: str) -> Optional[str]:
        """
        取得報告檔案路徑
        
        Args:
            report_id: 報告 ID
        
        Returns:
            Optional[str]: 檔案路徑，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def get_file_content(self, report_id: str) -> Optional[bytes]:
        """
        取得報告檔案內容
        
        Args:
            report_id: 報告 ID
        
        Returns:
            Optional[bytes]: 檔案內容（位元組），如果不存在則返回 None
        """
        pass

