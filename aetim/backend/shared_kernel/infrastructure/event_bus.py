"""
事件總線（Event Bus）

提供簡單的事件發布與訂閱機制。
"""

from typing import Dict, List, Callable, Any, Optional
import asyncio
import structlog

logger = structlog.get_logger(__name__)


class EventBus:
    """
    事件總線
    
    提供簡單的事件發布與訂閱機制。
    """
    
    def __init__(self):
        """初始化事件總線"""
        self._subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """
        訂閱事件
        
        Args:
            event_type: 事件類型（通常是事件類別的名稱）
            handler: 事件處理器（必須是 async 函數）
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
        
        logger.debug(
            "事件處理器已訂閱",
            event_type=event_type,
            handler=handler.__name__,
        )
    
    async def publish(self, event: Any) -> None:
        """
        發布事件
        
        Args:
            event: 事件物件
        """
        event_type = type(event).__name__
        
        if event_type not in self._subscribers:
            logger.debug(
                "沒有訂閱者處理此事件",
                event_type=event_type,
            )
            return
        
        handlers = self._subscribers[event_type]
        
        logger.debug(
            "發布事件",
            event_type=event_type,
            handler_count=len(handlers),
        )
        
        # 並行執行所有處理器
        tasks = []
        for handler in handlers:
            try:
                task = asyncio.create_task(handler(event))
                tasks.append(task)
            except Exception as e:
                logger.error(
                    "建立事件處理任務失敗",
                    event_type=event_type,
                    handler=handler.__name__,
                    error=str(e),
                    exc_info=True,
                )
        
        # 等待所有處理器完成（不等待錯誤）
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 記錄錯誤
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    "事件處理器執行失敗",
                    event_type=event_type,
                    handler=handlers[i].__name__,
                    error=str(result),
                    exc_info=True,
                )


# 全域事件總線實例
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    取得事件總線實例（單例模式）
    
    Returns:
        EventBus: 事件總線實例
    """
    global _event_bus
    
    if _event_bus is None:
        _event_bus = EventBus()
    
    return _event_bus


def reset_event_bus() -> None:
    """重置事件總線（主要用於測試）"""
    global _event_bus
    _event_bus = None

