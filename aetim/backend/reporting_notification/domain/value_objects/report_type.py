"""
報告類型值物件

定義報告類型的枚舉值。
"""

from enum import Enum


class ReportType(str, Enum):
    """報告類型枚舉"""
    
    CISO_WEEKLY = "CISO_Weekly"  # CISO 週報
    IT_TICKET = "IT_Ticket"  # IT 工單
    
    def __str__(self) -> str:
        return self.value
    
    @classmethod
    def from_string(cls, value: str) -> "ReportType":
        """從字串建立報告類型"""
        try:
            return cls(value)
        except ValueError:
            raise ValueError(f"無效的報告類型: {value}")

