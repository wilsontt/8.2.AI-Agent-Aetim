"""
資產管理領域值物件

值物件（Value Objects）是不可變的，沒有唯一識別碼，透過值相等性比較。
"""

from .data_sensitivity import DataSensitivity
from .business_criticality import BusinessCriticality

__all__ = [
    "DataSensitivity",
    "BusinessCriticality",
]

