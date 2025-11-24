"""
報告生成領域事件

當報告生成完成時發布此事件。
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..value_objects.report_type import ReportType
from ..value_objects.file_format import FileFormat


@dataclass
class ReportGeneratedEvent:
    """
    報告生成領域事件
    
    當報告生成完成時發布此事件，通知其他模組（如通知模組）進行後續處理。
    """
    
    report_id: str
    report_type: ReportType
    title: str
    file_path: str
    file_format: FileFormat
    generated_at: datetime
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    
    def __str__(self) -> str:
        return (
            f"ReportGeneratedEvent(report_id='{self.report_id}', "
            f"report_type='{self.report_type.value}', "
            f"title='{self.title}', "
            f"file_path='{self.file_path}', "
            f"generated_at='{self.generated_at.isoformat()}')"
        )

