"""
分析與評估領域值物件

值物件（Value Objects）是不可變的，沒有唯一識別碼，透過值相等性比較。
"""

from .pir_priority import PIRPriority

__all__ = [
    "PIRPriority",
]

