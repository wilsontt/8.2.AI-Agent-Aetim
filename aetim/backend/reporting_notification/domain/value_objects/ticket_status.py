"""
工單狀態值物件

定義 IT 工單狀態的枚舉值。
"""

from enum import Enum


class TicketStatus(str, Enum):
    """工單狀態枚舉（AC-017-5）"""
    
    PENDING = "待處理"  # 待處理
    IN_PROGRESS = "處理中"  # 處理中
    COMPLETED = "已完成"  # 已完成
    CLOSED = "已關閉"  # 已關閉
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def from_string(cls, value: str) -> "TicketStatus":
        """從字串建立工單狀態"""
        # 支援中英文
        mapping = {
            "待處理": cls.PENDING,
            "處理中": cls.IN_PROGRESS,
            "已完成": cls.COMPLETED,
            "已關閉": cls.CLOSED,
            "pending": cls.PENDING,
            "in_progress": cls.IN_PROGRESS,
            "completed": cls.COMPLETED,
            "closed": cls.CLOSED,
        }
        
        if value in mapping:
            return mapping[value]
        
        raise ValueError(f"無效的工單狀態: {value}")
    
    def can_transition_to(self, target_status: "TicketStatus") -> bool:
        """
        檢查是否可以轉換到目標狀態
        
        狀態轉換規則：
        - 待處理 → 處理中、已關閉
        - 處理中 → 已完成、已關閉
        - 已完成 → 已關閉
        - 已關閉 → 不可變更
        """
        if self == TicketStatus.CLOSED:
            return False
        
        valid_transitions = {
            TicketStatus.PENDING: [TicketStatus.IN_PROGRESS, TicketStatus.CLOSED],
            TicketStatus.IN_PROGRESS: [TicketStatus.COMPLETED, TicketStatus.CLOSED],
            TicketStatus.COMPLETED: [TicketStatus.CLOSED],
        }
        
        return target_status in valid_transitions.get(self, [])

