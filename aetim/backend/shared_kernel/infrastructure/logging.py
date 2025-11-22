"""
結構化日誌設定

實作結構化日誌（JSON 格式），符合 plan.md 第 9.3.1 節的要求。
"""

import structlog
import logging
import sys
from typing import Any


def setup_logging(log_level: str = "INFO") -> None:
    """
    設定結構化日誌
    
    Args:
        log_level: 日誌級別（DEBUG、INFO、WARN、ERROR、FATAL）
    """
    # 設定標準日誌
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
    
    # 設定 structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """
    取得結構化日誌記錄器
    
    Args:
        name: 記錄器名稱（通常是模組名稱）
    
    Returns:
        結構化日誌記錄器
    """
    return structlog.get_logger(name)

