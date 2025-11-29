"""
報告排程聚合根

定義報告排程的領域模型。
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Optional
import uuid

from ..value_objects.report_type import ReportType


@dataclass
class ReportSchedule:
    """
    報告排程聚合根
    
    負責管理報告生成的排程設定。
    """
    
    id: str
    report_type: ReportType
    cron_expression: str  # Cron 表達式，例如："0 9 * * 1" 表示每週一上午 9:00
    is_enabled: bool
    recipients: List[str]  # Email 收件人清單
    file_format: str = "HTML"  # 檔案格式（HTML/PDF）
    timezone: str = "Asia/Taipei"  # 時區設定
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    
    def __post_init__(self):
        """驗證聚合根的有效性"""
        if not self.cron_expression or not self.cron_expression.strip():
            raise ValueError("Cron 表達式不能為空")
        if not self.recipients:
            raise ValueError("收件人清單不能為空")
        if not isinstance(self.report_type, ReportType):
            raise ValueError("報告類型必須是 ReportType 枚舉")
    
    @classmethod
    def create(
        cls,
        report_type: ReportType,
        cron_expression: str,
        recipients: List[str],
        file_format: str = "HTML",
        timezone: str = "Asia/Taipei",
        is_enabled: bool = True,
        schedule_id: Optional[str] = None,
    ) -> "ReportSchedule":
        """
        建立報告排程（工廠方法）
        
        Args:
            report_type: 報告類型
            cron_expression: Cron 表達式
            recipients: 收件人清單
            file_format: 檔案格式（預設：HTML）
            timezone: 時區設定（預設：Asia/Taipei）
            is_enabled: 是否啟用（預設：True）
            schedule_id: 排程 ID（可選，預設自動生成）
        
        Returns:
            ReportSchedule: 報告排程聚合根
        """
        return cls(
            id=schedule_id if schedule_id else str(uuid.uuid4()),
            report_type=report_type,
            cron_expression=cron_expression,
            is_enabled=is_enabled,
            recipients=recipients,
            file_format=file_format,
            timezone=timezone,
        )
    
    def update_schedule(
        self,
        cron_expression: Optional[str] = None,
        recipients: Optional[List[str]] = None,
        file_format: Optional[str] = None,
        timezone: Optional[str] = None,
        is_enabled: Optional[bool] = None,
    ) -> None:
        """
        更新排程設定
        
        Args:
            cron_expression: 新的 Cron 表達式（可選）
            recipients: 新的收件人清單（可選）
            file_format: 新的檔案格式（可選）
            timezone: 新的時區設定（可選）
            is_enabled: 是否啟用（可選）
        """
        if cron_expression is not None:
            if not cron_expression.strip():
                raise ValueError("Cron 表達式不能為空")
            self.cron_expression = cron_expression
        
        if recipients is not None:
            if not recipients:
                raise ValueError("收件人清單不能為空")
            self.recipients = recipients
        
        if file_format is not None:
            self.file_format = file_format
        
        if timezone is not None:
            if not timezone.strip():
                raise ValueError("時區設定不能為空")
            self.timezone = timezone
        
        if is_enabled is not None:
            self.is_enabled = is_enabled
        
        self.updated_at = datetime.utcnow()
    
    def update_run_times(
        self,
        last_run_at: Optional[datetime] = None,
        next_run_at: Optional[datetime] = None,
    ) -> None:
        """
        更新執行時間
        
        Args:
            last_run_at: 最後執行時間（可選）
            next_run_at: 下次執行時間（可選）
        """
        if last_run_at is not None:
            self.last_run_at = last_run_at
        if next_run_at is not None:
            self.next_run_at = next_run_at
    
    def enable(self) -> None:
        """啟用排程"""
        self.is_enabled = True
        self.updated_at = datetime.utcnow()
    
    def disable(self) -> None:
        """停用排程"""
        self.is_enabled = False
        self.updated_at = datetime.utcnow()

