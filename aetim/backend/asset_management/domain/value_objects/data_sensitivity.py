"""
資料敏感度值物件

資料敏感度等級及其權重計算。
"""

from typing import Literal
from dataclasses import dataclass


@dataclass(frozen=True)
class DataSensitivity:
    """
    資料敏感度值物件
    
    值物件是不可變的，透過值相等性比較。
    權重用於風險分數計算。
    """
    
    value: Literal["高", "中", "低"]
    
    def __post_init__(self):
        """驗證值物件的有效性"""
        if self.value not in DataSensitivity.WEIGHTS:
            raise ValueError(
                f"資料敏感度必須為「高」、「中」或「低」，收到：{self.value}"
            )
    
    @property
    def weight(self) -> float:
        """取得權重值"""
        return DataSensitivity.WEIGHTS.get(self.value, 1.0)
    
    def __eq__(self, other):
        """值物件透過值相等性比較"""
        if not isinstance(other, DataSensitivity):
            return False
        return self.value == other.value
    
    def __hash__(self):
        """值物件必須可雜湊"""
        return hash(self.value)
    
    def __repr__(self):
        return f"DataSensitivity(value='{self.value}', weight={self.weight})"


# 權重對照表（類別變數，在類別定義後設定以避免 dataclass 欄位問題）
DataSensitivity.WEIGHTS = {
    "高": 1.5,
    "中": 1.0,
    "低": 0.5,
}
