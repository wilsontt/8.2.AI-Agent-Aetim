"""
報告與通知模組介面
"""

from .report_repository import IReportRepository
from .report_schedule_repository import IReportScheduleRepository

__all__ = ["IReportRepository", "IReportScheduleRepository"]

