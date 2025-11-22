"""
系統管理領域實體

實體（Entities）具有唯一識別碼，透過 ID 相等性比較。
"""

from .audit_log import AuditLog

__all__ = [
    "AuditLog",
]

