"""
報告排程 Repository 介面

定義報告排程的資料存取介面。
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from ..aggregates.report_schedule import ReportSchedule
from ..value_objects.report_type import ReportType


class IReportScheduleRepository(ABC):
    """
    報告排程 Repository 介面
    
    定義報告排程的資料存取方法。
    """
    
    @abstractmethod
    async def save(self, schedule: ReportSchedule) -> None:
        """
        儲存報告排程（新增或更新）
        
        Args:
            schedule: 報告排程聚合根
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, schedule_id: str) -> Optional[ReportSchedule]:
        """
        依 ID 查詢報告排程
        
        Args:
            schedule_id: 排程 ID
        
        Returns:
            Optional[ReportSchedule]: 報告排程聚合根，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def get_by_report_type(
        self, report_type: ReportType
    ) -> Optional[ReportSchedule]:
        """
        依報告類型查詢報告排程
        
        Args:
            report_type: 報告類型
        
        Returns:
            Optional[ReportSchedule]: 報告排程聚合根，如果不存在則返回 None
        """
        pass
    
    @abstractmethod
    async def get_all_enabled(self) -> List[ReportSchedule]:
        """
        查詢所有啟用的報告排程
        
        Returns:
            List[ReportSchedule]: 報告排程聚合根清單
        """
        pass
    
    @abstractmethod
    async def delete(self, schedule_id: str) -> None:
        """
        刪除報告排程
        
        Args:
            schedule_id: 排程 ID
        """
        pass

