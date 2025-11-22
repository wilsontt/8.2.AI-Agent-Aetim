"""
威脅情資來源優先級值物件

威脅情資來源的優先級等級（P0/P1/P2/P3）。
"""

from typing import Literal
from dataclasses import dataclass


@dataclass(frozen=True)
class ThreatFeedPriority:
    """
    威脅情資來源優先級值物件
    
    值物件是不可變的，透過值相等性比較。
    
    優先級說明：
    - P0：緊急（CISA KEV 等）
    - P1：高（NVD、VMware VMSA、MSRC 等）
    - P2：中（TWCERT/CC、TW-CERT 等）
    - P3：低（OSINT 等）
    """
    
    value: Literal["P0", "P1", "P2", "P3"]
    
    def __post_init__(self):
        """驗證值物件的有效性"""
        if self.value not in ["P0", "P1", "P2", "P3"]:
            raise ValueError(f"威脅情資來源優先級必須為 P0、P1、P2 或 P3，收到：{self.value}")
    
    def __eq__(self, other):
        """值物件透過值相等性比較"""
        if not isinstance(other, ThreatFeedPriority):
            return False
        return self.value == other.value
    
    def __hash__(self):
        """值物件必須可雜湊"""
        return hash(self.value)
    
    def __repr__(self):
        return f"ThreatFeedPriority(value='{self.value}')"
    
    @property
    def numeric_value(self) -> int:
        """取得數值優先級（用於排序）"""
        mapping = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        return mapping[self.value]

