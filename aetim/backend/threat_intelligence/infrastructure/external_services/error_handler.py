"""
錯誤處理器

提供錯誤分類、記錄和處理功能。
"""

import httpx
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class ErrorType(Enum):
    """錯誤類型"""
    
    NETWORK_ERROR = "network_error"  # 網路錯誤
    API_ERROR = "api_error"  # API 錯誤
    RATE_LIMIT_ERROR = "rate_limit_error"  # 速率限制錯誤
    DATA_FORMAT_ERROR = "data_format_error"  # 資料格式錯誤
    AUTHENTICATION_ERROR = "authentication_error"  # 認證錯誤
    TIMEOUT_ERROR = "timeout_error"  # 超時錯誤
    UNKNOWN_ERROR = "unknown_error"  # 未知錯誤


class ErrorHandler:
    """
    錯誤處理器
    
    提供錯誤分類、記錄和處理功能。
    """
    
    @staticmethod
    def classify_error(error: Exception) -> ErrorType:
        """
        分類錯誤類型
        
        Args:
            error: 異常物件
        
        Returns:
            ErrorType: 錯誤類型
        """
        if isinstance(error, httpx.TimeoutException):
            return ErrorType.TIMEOUT_ERROR
        elif isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code if hasattr(error, "response") else None
            if status_code == 429:
                return ErrorType.RATE_LIMIT_ERROR
            elif status_code in [401, 403]:
                return ErrorType.AUTHENTICATION_ERROR
            elif status_code >= 500:
                return ErrorType.API_ERROR
            else:
                return ErrorType.API_ERROR
        elif isinstance(error, httpx.NetworkError):
            return ErrorType.NETWORK_ERROR
        elif isinstance(error, (ValueError, KeyError, TypeError)):
            return ErrorType.DATA_FORMAT_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    @staticmethod
    def is_retryable(error: Exception) -> bool:
        """
        判斷錯誤是否可重試
        
        Args:
            error: 異常物件
        
        Returns:
            bool: 是否可重試
        """
        error_type = ErrorHandler.classify_error(error)
        
        # 可重試的錯誤類型
        retryable_types = {
            ErrorType.NETWORK_ERROR,
            ErrorType.API_ERROR,  # 5xx 錯誤
            ErrorType.RATE_LIMIT_ERROR,
            ErrorType.TIMEOUT_ERROR,
        }
        
        return error_type in retryable_types
    
    @staticmethod
    def extract_rate_limit_info(error: Exception) -> Optional[Dict[str, Any]]:
        """
        從 HTTP 429 錯誤中提取速率限制資訊
        
        Args:
            error: 異常物件
        
        Returns:
            Optional[Dict]: 速率限制資訊，包含 retry_after 等
        """
        if not isinstance(error, httpx.HTTPStatusError):
            return None
        
        if not hasattr(error, "response"):
            return None
        
        response = error.response
        if response.status_code != 429:
            return None
        
        # 從 Response Headers 提取速率限制資訊
        retry_after = response.headers.get("Retry-After")
        rate_limit_limit = response.headers.get("X-RateLimit-Limit")
        rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")
        rate_limit_reset = response.headers.get("X-RateLimit-Reset")
        
        info = {}
        if retry_after:
            try:
                info["retry_after"] = int(retry_after)
            except ValueError:
                pass
        if rate_limit_limit:
            try:
                info["rate_limit_limit"] = int(rate_limit_limit)
            except ValueError:
                pass
        if rate_limit_remaining:
            try:
                info["rate_limit_remaining"] = int(rate_limit_remaining)
            except ValueError:
                pass
        if rate_limit_reset:
            try:
                info["rate_limit_reset"] = int(rate_limit_reset)
            except ValueError:
                pass
        
        return info if info else None
    
    @staticmethod
    def log_error(
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        error_type: Optional[ErrorType] = None,
    ) -> Dict[str, Any]:
        """
        記錄錯誤
        
        Args:
            error: 異常物件
            context: 錯誤上下文資訊
            error_type: 錯誤類型（如果未提供則自動分類）
        
        Returns:
            Dict: 錯誤詳情
        """
        if error_type is None:
            error_type = ErrorHandler.classify_error(error)
        
        error_details = {
            "error_type": error_type.value,
            "error_message": str(error),
            "error_class": error.__class__.__name__,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # 如果是 HTTP 錯誤，提取狀態碼和回應內容
        if isinstance(error, httpx.HTTPStatusError):
            if hasattr(error, "response"):
                response = error.response
                error_details["status_code"] = response.status_code
                error_details["response_headers"] = dict(response.headers)
                
                # 如果是速率限制錯誤，提取速率限制資訊
                if response.status_code == 429:
                    rate_limit_info = ErrorHandler.extract_rate_limit_info(error)
                    if rate_limit_info:
                        error_details["rate_limit_info"] = rate_limit_info
        
        # 合併上下文資訊
        if context:
            error_details["context"] = context
        
        # 記錄錯誤日誌
        log_level = "error" if error_type in [
            ErrorType.AUTHENTICATION_ERROR,
            ErrorType.DATA_FORMAT_ERROR,
        ] else "warning"
        
        logger.log(
            getattr(logger, log_level.upper()),
            f"錯誤發生：{error_type.value}",
            extra=error_details,
        )
        
        return error_details

