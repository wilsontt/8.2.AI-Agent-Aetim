"""
共享核心中介軟體

提供跨模組使用的中介軟體。
"""

from .audit_log_middleware import AuditLogMiddleware

__all__ = [
    "AuditLogMiddleware",
]

