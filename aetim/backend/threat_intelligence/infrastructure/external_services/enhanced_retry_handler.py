"""
增強的重試處理器

提供增強的錯誤重試機制，包含 HTTP 429 處理和錯誤分類。
"""

import asyncio
import httpx
from typing import Callable, TypeVar, Optional, Dict, Any
from datetime import datetime, timedelta
from shared_kernel.infrastructure.logging import get_logger
from .error_handler import ErrorHandler, ErrorType

logger = get_logger(__name__)

T = TypeVar("T")


class EnhancedRetryHandler:
    """
    增強的重試處理器
    
    提供增強的錯誤重試機制，包含：
    - HTTP 429 速率限制處理
    - 錯誤分類和記錄
    - 指數退避重試
    - 重試次數和時間記錄
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        """
        初始化增強的重試處理器
        
        Args:
            max_retries: 最大重試次數
            initial_delay: 初始延遲時間（秒）
            max_delay: 最大延遲時間（秒）
            exponential_base: 指數退避的基底
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.error_handler = ErrorHandler()
    
    async def execute_with_retry(
        self,
        func: Callable[[], T],
        *,
        retryable_exceptions: tuple = (Exception,),
        on_retry: Optional[Callable[[int, Exception, Dict[str, Any]], None]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> T:
        """
        執行函數並在失敗時重試（AC-008-3）
        
        Args:
            func: 要執行的異步函數
            retryable_exceptions: 可重試的異常類型
            on_retry: 重試時的回調函數（接收重試次數、異常和錯誤詳情）
            context: 錯誤上下文資訊
        
        Returns:
            T: 函數的返回值
        
        Raises:
            Exception: 如果所有重試都失敗，拋出最後的異常
        """
        last_exception = None
        retry_history = []
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func()
            except retryable_exceptions as e:
                last_exception = e
                
                # 分類錯誤
                error_type = self.error_handler.classify_error(e)
                
                # 判斷是否可重試
                if not self.error_handler.is_retryable(e) and attempt < self.max_retries:
                    # 不可重試的錯誤，直接拋出
                    logger.error(
                        f"發生不可重試的錯誤：{error_type.value}",
                        extra={"error": str(e), "context": context}
                    )
                    raise e
                
                # 記錄錯誤
                error_details = self.error_handler.log_error(e, context=context, error_type=error_type)
                
                if attempt < self.max_retries:
                    # 計算延遲時間
                    delay = self._calculate_delay(attempt, e, error_details)
                    
                    # 記錄重試資訊
                    retry_info = {
                        "attempt": attempt + 1,
                        "max_retries": self.max_retries,
                        "delay": delay,
                        "error_type": error_type.value,
                        "retry_at": (datetime.utcnow() + timedelta(seconds=delay)).isoformat(),
                    }
                    retry_history.append(retry_info)
                    
                    logger.warning(
                        f"執行失敗，{delay:.2f} 秒後重試（第 {attempt + 1}/{self.max_retries} 次）",
                        extra={
                            **retry_info,
                            "error": str(e),
                            "context": context,
                        }
                    )
                    
                    if on_retry:
                        on_retry(attempt + 1, e, error_details)
                    
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"執行失敗，已達最大重試次數",
                        extra={
                            "max_retries": self.max_retries,
                            "retry_history": retry_history,
                            "error": str(e),
                            "error_type": error_type.value,
                            "context": context,
                        }
                    )
        
        # 所有重試都失敗，拋出最後的異常
        raise last_exception
    
    def _calculate_delay(
        self,
        attempt: int,
        error: Exception,
        error_details: Dict[str, Any],
    ) -> float:
        """
        計算重試延遲時間
        
        對於 HTTP 429 錯誤，使用 Retry-After header 的值。
        對於其他錯誤，使用指數退避。
        
        Args:
            attempt: 重試次數（從 0 開始）
            error: 異常物件
            error_details: 錯誤詳情
        
        Returns:
            float: 延遲時間（秒）
        """
        # 如果是 HTTP 429 錯誤，使用 Retry-After header
        if isinstance(error, httpx.HTTPStatusError):
            if hasattr(error, "response") and error.response.status_code == 429:
                rate_limit_info = error_details.get("rate_limit_info", {})
                retry_after = rate_limit_info.get("retry_after")
                if retry_after:
                    # 使用 Retry-After header 的值，但不超過 max_delay
                    return min(float(retry_after), self.max_delay)
        
        # 使用指數退避
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay,
        )
        
        return delay

