"""
收集頻率值物件

威脅情資來源的收集頻率（每小時、每日、每週等）。
"""

from typing import Literal
from dataclasses import dataclass


@dataclass(frozen=True)
class CollectionFrequency:
    """
    收集頻率值物件
    
    值物件是不可變的，透過值相等性比較。
    """
    
    value: Literal["每小時", "每日", "每週", "每月"]
    
    def __post_init__(self):
        """驗證值物件的有效性"""
        valid_frequencies = ["每小時", "每日", "每週", "每月"]
        if self.value not in valid_frequencies:
            raise ValueError(f"收集頻率必須為以下之一：{', '.join(valid_frequencies)}，收到：{self.value}")
    
    def __eq__(self, other):
        """值物件透過值相等性比較"""
        if not isinstance(other, CollectionFrequency):
            return False
        return self.value == other.value
    
    def __hash__(self):
        """值物件必須可雜湊"""
        return hash(self.value)
    
    def __repr__(self):
        return f"CollectionFrequency(value='{self.value}')"
    
    @property
    def hours(self) -> int:
        """取得小時數（用於排程）"""
        mapping = {
            "每小時": 1,
            "每日": 24,
            "每週": 168,  # 7 * 24
            "每月": 720,  # 30 * 24（近似值）
        }
        return mapping[self.value]

