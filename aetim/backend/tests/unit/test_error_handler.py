"""
錯誤處理器單元測試

測試錯誤分類、記錄和處理功能。
"""

import pytest
import httpx
from threat_intelligence.infrastructure.external_services.error_handler import (
    ErrorHandler,
    ErrorType,
)


class TestErrorHandler:
    """錯誤處理器測試"""
    
    def test_classify_timeout_error(self):
        """測試超時錯誤分類"""
        error = httpx.TimeoutException("Request timeout")
        error_type = ErrorHandler.classify_error(error)
        assert error_type == ErrorType.TIMEOUT_ERROR
    
    def test_classify_rate_limit_error(self):
        """測試速率限制錯誤分類"""
        response = httpx.Response(429, headers={"Retry-After": "60"})
        error = httpx.HTTPStatusError("Rate limit exceeded", request=None, response=response)
        error_type = ErrorHandler.classify_error(error)
        assert error_type == ErrorType.RATE_LIMIT_ERROR
    
    def test_classify_authentication_error(self):
        """測試認證錯誤分類"""
        response = httpx.Response(401, headers={})
        error = httpx.HTTPStatusError("Unauthorized", request=None, response=response)
        error_type = ErrorHandler.classify_error(error)
        assert error_type == ErrorType.AUTHENTICATION_ERROR
    
    def test_classify_network_error(self):
        """測試網路錯誤分類"""
        error = httpx.NetworkError("Connection failed")
        error_type = ErrorHandler.classify_error(error)
        assert error_type == ErrorType.NETWORK_ERROR
    
    def test_classify_data_format_error(self):
        """測試資料格式錯誤分類"""
        error = ValueError("Invalid data format")
        error_type = ErrorHandler.classify_error(error)
        assert error_type == ErrorType.DATA_FORMAT_ERROR
    
    def test_classify_unknown_error(self):
        """測試未知錯誤分類"""
        error = Exception("Unknown error")
        error_type = ErrorHandler.classify_error(error)
        assert error_type == ErrorType.UNKNOWN_ERROR
    
    def test_is_retryable_network_error(self):
        """測試網路錯誤是否可重試"""
        error = httpx.NetworkError("Connection failed")
        assert ErrorHandler.is_retryable(error) is True
    
    def test_is_retryable_rate_limit_error(self):
        """測試速率限制錯誤是否可重試"""
        response = httpx.Response(429, headers={"Retry-After": "60"})
        error = httpx.HTTPStatusError("Rate limit exceeded", request=None, response=response)
        assert ErrorHandler.is_retryable(error) is True
    
    def test_is_retryable_authentication_error(self):
        """測試認證錯誤是否不可重試"""
        response = httpx.Response(401, headers={})
        error = httpx.HTTPStatusError("Unauthorized", request=None, response=response)
        assert ErrorHandler.is_retryable(error) is False
    
    def test_is_retryable_data_format_error(self):
        """測試資料格式錯誤是否不可重試"""
        error = ValueError("Invalid data format")
        assert ErrorHandler.is_retryable(error) is False
    
    def test_extract_rate_limit_info(self):
        """測試提取速率限制資訊"""
        response = httpx.Response(
            429,
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": "1234567890",
            }
        )
        error = httpx.HTTPStatusError("Rate limit exceeded", request=None, response=response)
        info = ErrorHandler.extract_rate_limit_info(error)
        
        assert info is not None
        assert info["retry_after"] == 60
        assert info["rate_limit_limit"] == 100
        assert info["rate_limit_remaining"] == 0
        assert info["rate_limit_reset"] == 1234567890
    
    def test_extract_rate_limit_info_non_429(self):
        """測試非 429 錯誤不提取速率限制資訊"""
        response = httpx.Response(500, headers={})
        error = httpx.HTTPStatusError("Internal server error", request=None, response=response)
        info = ErrorHandler.extract_rate_limit_info(error)
        assert info is None
    
    def test_log_error(self):
        """測試記錄錯誤"""
        error = httpx.NetworkError("Connection failed")
        context = {"feed_id": "feed-123", "feed_name": "Test Feed"}
        
        error_details = ErrorHandler.log_error(error, context=context)
        
        assert error_details["error_type"] == ErrorType.NETWORK_ERROR.value
        assert error_details["error_message"] == "Connection failed"
        assert error_details["error_class"] == "NetworkError"
        assert error_details["context"] == context
        assert "timestamp" in error_details

