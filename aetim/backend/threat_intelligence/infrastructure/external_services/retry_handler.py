"""
重試處理器

提供指數退避重試機制。
"""

import asyncio
from typing import Callable, TypeVar, Optional
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class RetryHandler:
    """
    重試處理器
    
    提供指數退避重試機制。
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
    ):
        """
        初始化重試處理器
        
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
    
    async def execute_with_retry(
        self,
        func: Callable[[], T],
        *,
        retryable_exceptions: tuple = (Exception,),
        on_retry: Optional[Callable[[int, Exception], None]] = None,
    ) -> T:
        """
        執行函數並在失敗時重試
        
        Args:
            func: 要執行的異步函數
            retryable_exceptions: 可重試的異常類型
            on_retry: 重試時的回調函數（接收重試次數和異常）
        
        Returns:
            T: 函數的返回值
        
        Raises:
            Exception: 如果所有重試都失敗，拋出最後的異常
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func()
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = min(
                        self.initial_delay * (self.exponential_base ** attempt),
                        self.max_delay,
                    )
                    
                    logger.warning(
                        f"執行失敗，{delay:.2f} 秒後重試（第 {attempt + 1}/{self.max_retries} 次）",
                        extra={
                            "attempt": attempt + 1,
                            "max_retries": self.max_retries,
                            "delay": delay,
                            "error": str(e),
                        }
                    )
                    
                    if on_retry:
                        on_retry(attempt + 1, e)
                    
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"執行失敗，已達最大重試次數",
                        extra={
                            "max_retries": self.max_retries,
                            "error": str(e),
                        }
                    )
        
        # 所有重試都失敗，拋出最後的異常
        raise last_exception

