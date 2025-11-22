"""
日誌工具

提供結構化日誌記錄功能。
"""

import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime


def setup_logging(log_level: str = "INFO"):
    """
    設定日誌配置
    
    Args:
        log_level: 日誌級別（DEBUG/INFO/WARN/ERROR）
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def get_logger(name: str) -> logging.Logger:
    """
    取得日誌記錄器
    
    Args:
        name: 日誌記錄器名稱
    
    Returns:
        logging.Logger: 日誌記錄器
    """
    return logging.getLogger(name)


def log_ai_processing(
    logger: logging.Logger,
    input_text: str,
    result: Dict[str, Any],
    confidence: float,
    processing_time: Optional[float] = None,
):
    """
    記錄 AI 處理日誌（符合 AC-009-6）
    
    記錄輸入內容、提取結果、信心分數。
    
    Args:
        logger: 日誌記錄器
        input_text: 輸入文字內容
        result: 提取結果
        confidence: 信心分數
        processing_time: 處理時間（秒，可選）
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "input_text_length": len(input_text),
        "input_text_preview": input_text[:200] if len(input_text) > 200 else input_text,
        "result": {
            "cve_count": len(result.get("cve", [])),
            "products_count": len(result.get("products", [])),
            "ttps_count": len(result.get("ttps", [])),
            "iocs_count": sum(len(v) for v in result.get("iocs", {}).values()),
        },
        "confidence": confidence,
    }
    
    if processing_time is not None:
        log_data["processing_time_seconds"] = processing_time
    
    logger.info(
        "AI 處理完成",
        extra=log_data,
    )

