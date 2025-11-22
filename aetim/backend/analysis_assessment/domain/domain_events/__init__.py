"""
分析與評估領域事件

領域事件（Domain Events）用於表示領域中發生的重要事件。
"""

from .pir_created_event import PIRCreatedEvent
from .pir_updated_event import PIRUpdatedEvent
from .pir_toggled_event import PIRToggledEvent

__all__ = [
    "PIRCreatedEvent",
    "PIRUpdatedEvent",
    "PIRToggledEvent",
]

