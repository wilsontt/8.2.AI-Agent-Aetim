"""
結構化日誌設定

實作結構化日誌（JSON 格式），符合 plan.md 第 9.3.1 節的要求。
"""

import structlog
import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from typing import Any
from pathlib import Path


def setup_logging(log_level: str = "INFO", enable_file_logging: bool = True) -> None:
    """
    設定結構化日誌
    
    Args:
        log_level: 日誌級別（DEBUG、INFO、WARN、ERROR、FATAL）
        enable_file_logging: 是否啟用檔案日誌
    """
    # 建立日誌目錄
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 設定標準日誌
    handlers = []
    
    # Console 輸出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    handlers.append(console_handler)
    
    # 檔案輸出（日誌輪轉）
    if enable_file_logging:
        file_handler = RotatingFileHandler(
            log_dir / "aetim.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        handlers.append(file_handler)
    
    # 設定根記錄器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.handlers = handlers
    
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

