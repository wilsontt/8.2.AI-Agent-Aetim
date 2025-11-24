"""
報告聚合根

報告聚合根包含所有業務邏輯方法，負責維護報告的一致性。
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from ..value_objects.report_type import ReportType
from ..value_objects.file_format import FileFormat
from ..domain_events.report_generated_event import ReportGeneratedEvent


@dataclass
class Report:
    """
    報告聚合根
    
    聚合根負責：
    1. 維護聚合的一致性邊界
    2. 實作業務邏輯
    3. 發布領域事件
    
    業務規則：
    - 報告類型必須為有效的 ReportType（AC-015-1, AC-017-5）
    - 檔案格式必須為有效的 FileFormat（AC-015-3, AC-017-3）
    - 檔案路徑不能為空（AC-015-5, AC-015-6）
    - 標題不能為空
    """
    
    id: str
    report_type: ReportType
    title: str
    file_path: str
    file_format: FileFormat
    generated_at: datetime
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    summary: Optional[str] = None  # AI 生成的摘要
    metadata: Optional[Dict[str, Any]] = None  # 報告元資料（JSON 格式）
    _domain_events: list = field(default_factory=list, repr=False)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """驗證聚合根的有效性"""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if not self.title or not self.title.strip():
            raise ValueError("報告標題不能為空")
        
        if not self.file_path or not self.file_path.strip():
            raise ValueError("檔案路徑不能為空")
        
        if not isinstance(self.report_type, ReportType):
            raise ValueError(f"無效的報告類型: {self.report_type}")
        
        if not isinstance(self.file_format, FileFormat):
            raise ValueError(f"無效的檔案格式: {self.file_format}")
    
    @classmethod
    def create(
        cls,
        report_type: ReportType,
        title: str,
        file_path: str,
        file_format: FileFormat,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        summary: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        generated_at: Optional[datetime] = None,
    ) -> "Report":
        """
        建立報告（工廠方法）
        
        Args:
            report_type: 報告類型
            title: 報告標題
            file_path: 檔案路徑
            file_format: 檔案格式
            period_start: 報告期間開始（可選）
            period_end: 報告期間結束（可選）
            summary: AI 生成的摘要（可選）
            metadata: 報告元資料（可選）
            generated_at: 生成時間（可選，預設為當前時間）
        
        Returns:
            Report: 新建立的報告聚合根
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        if generated_at is None:
            generated_at = datetime.utcnow()
        
        report = cls(
            id=str(uuid.uuid4()),
            report_type=report_type,
            title=title,
            file_path=file_path,
            file_format=file_format,
            generated_at=generated_at,
            period_start=period_start,
            period_end=period_end,
            summary=summary,
            metadata=metadata,
        )
        
        # 發布領域事件
        report._publish_domain_event(
            ReportGeneratedEvent(
                report_id=report.id,
                report_type=report.report_type,
                title=report.title,
                file_path=report.file_path,
                file_format=report.file_format,
                generated_at=report.generated_at,
                period_start=report.period_start,
                period_end=report.period_end,
            )
        )
        
        return report
    
    def set_summary(self, summary: str) -> None:
        """
        設定 AI 生成的摘要（AC-015-4）
        
        Args:
            summary: AI 生成的摘要文字
        
        Raises:
            ValueError: 當摘要為空時
        """
        if not summary or not summary.strip():
            raise ValueError("摘要不能為空")
        
        self.summary = summary
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        更新報告元資料
        
        Args:
            metadata: 報告元資料（字典格式）
        """
        if self.metadata is None:
            self.metadata = {}
        
        self.metadata.update(metadata)
    
    def _publish_domain_event(self, event: Any) -> None:
        """
        發布領域事件
        
        Args:
            event: 領域事件
        """
        if not hasattr(self, "_domain_events"):
            self._domain_events = []
        
        self._domain_events.append(event)
    
    def get_domain_events(self) -> list:
        """
        取得所有領域事件
        
        Returns:
            list: 領域事件清單
        """
        return getattr(self, "_domain_events", [])
    
    def clear_domain_events(self) -> None:
        """清除所有領域事件"""
        self._domain_events = []

