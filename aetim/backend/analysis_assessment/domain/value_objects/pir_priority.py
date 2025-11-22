"""
PIR 優先級值物件

PIR 優先級等級。
"""

from typing import Literal
from dataclasses import dataclass


@dataclass(frozen=True)
class PIRPriority:
    """
    PIR 優先級值物件
    
    值物件是不可變的，透過值相等性比較。
    """
    
    value: Literal["高", "中", "低"]
    
    def __post_init__(self):
        """驗證值物件的有效性"""
        if self.value not in ["高", "中", "低"]:
            raise ValueError(f"PIR 優先級必須為「高」、「中」或「低」，收到：{self.value}")
    
    def __eq__(self, other):
        """值物件透過值相等性比較"""
        if not isinstance(other, PIRPriority):
            return False
        return self.value == other.value
    
    def __hash__(self):
        """值物件必須可雜湊"""
        return hash(self.value)
    
    def __repr__(self):
        return f"PIRPriority(value='{self.value}')"

