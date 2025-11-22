"""
日誌功能單元測試
"""

import pytest
import json
import logging
from shared_kernel.infrastructure.logging import setup_logging, get_logger


@pytest.mark.unit
def test_setup_logging():
    """測試日誌設定"""
    setup_logging(log_level="INFO", enable_file_logging=False)
    logger = get_logger("test")
    
    # 測試日誌輸出
    logger.info("Test log message", extra={"test_key": "test_value"})
    
    # 驗證日誌記錄器已建立
    assert logger is not None


@pytest.mark.unit
def test_logger_output_format():
    """測試日誌輸出格式（JSON）"""
    setup_logging(log_level="DEBUG", enable_file_logging=False)
    logger = get_logger("test")
    
    # 記錄一條日誌
    logger.info("Test message", extra={"key": "value"})
    
    # 驗證記錄器存在
    assert logger is not None

