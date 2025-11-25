"""
工單狀態更新事件

當工單狀態變更時發布此事件。
"""

from dataclasses import dataclass
from datetime import datetime
from ..value_objects.ticket_status import TicketStatus


@dataclass(frozen=True)
class TicketStatusUpdatedEvent:
    """工單狀態更新事件"""
    
    ticket_id: str
    old_status: TicketStatus
    new_status: TicketStatus
    updated_at: datetime
    updated_by: str | None = None  # 更新者（可選）
    
    def __str__(self) -> str:
        return (
            f"TicketStatusUpdatedEvent(ticket_id='{self.ticket_id}', "
            f"old_status='{self.old_status.value}', "
            f"new_status='{self.new_status.value}', "
            f"updated_at='{self.updated_at.isoformat()}')"
        )

