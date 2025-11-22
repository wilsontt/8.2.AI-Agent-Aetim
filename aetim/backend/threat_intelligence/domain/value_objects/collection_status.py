"""
收集狀態值物件

威脅情資來源的收集狀態（success/failed/in_progress）。
"""

from typing import Literal
from dataclasses import dataclass


@dataclass(frozen=True)
class CollectionStatus:
    """
    收集狀態值物件
    
    值物件是不可變的，透過值相等性比較。
    """
    
    value: Literal["success", "failed", "in_progress"]
    
    def __post_init__(self):
        """驗證值物件的有效性"""
        valid_statuses = ["success", "failed", "in_progress"]
        if self.value not in valid_statuses:
            raise ValueError(f"收集狀態必須為以下之一：{', '.join(valid_statuses)}，收到：{self.value}")
    
    def __eq__(self, other):
        """值物件透過值相等性比較"""
        if not isinstance(other, CollectionStatus):
            return False
        return self.value == other.value
    
    def __hash__(self):
        """值物件必須可雜湊"""
        return hash(self.value)
    
    def __repr__(self):
        return f"CollectionStatus(value='{self.value}')"
    
    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.value == "success"
    
    @property
    def is_failed(self) -> bool:
        """是否失敗"""
        return self.value == "failed"
    
    @property
    def is_in_progress(self) -> bool:
        """是否進行中"""
        return self.value == "in_progress"

