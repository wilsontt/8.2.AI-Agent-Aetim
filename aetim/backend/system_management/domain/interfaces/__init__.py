"""
系統管理領域介面

定義領域層需要的介面（Repository、外部服務等）。
"""

from .audit_log_repository import IAuditLogRepository

__all__ = [
    "IAuditLogRepository",
]

