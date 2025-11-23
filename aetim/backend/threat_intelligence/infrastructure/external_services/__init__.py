"""
外部服務模組

提供與外部服務整合的功能。
"""

from .ai_service_client import AIServiceClient
from .collector_factory import CollectorFactory
from .collector_interface import ICollector
from .retry_handler import RetryHandler

__all__ = [
    "AIServiceClient",
    "CollectorFactory",
    "ICollector",
    "RetryHandler",
]

