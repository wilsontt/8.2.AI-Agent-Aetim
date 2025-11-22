"""
收集器工廠

根據威脅情資來源類型建立對應的收集器。
"""

from typing import Dict, Optional
from ...domain.aggregates.threat_feed import ThreatFeed
from .collector_interface import ICollector
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class CollectorFactory:
    """
    收集器工廠
    
    根據威脅情資來源類型建立對應的收集器。
    """
    
    def __init__(self):
        """初始化工廠"""
        self._collectors: Dict[str, ICollector] = {}
    
    def register_collector(self, collector_type: str, collector: ICollector) -> None:
        """
        註冊收集器
        
        Args:
            collector_type: 收集器類型
            collector: 收集器實例
        """
        self._collectors[collector_type] = collector
        logger.info(
            f"已註冊收集器：{collector_type}",
            extra={"collector_type": collector_type}
        )
    
    def get_collector(self, feed: ThreatFeed) -> Optional[ICollector]:
        """
        取得對應的收集器
        
        Args:
            feed: 威脅情資來源聚合根
        
        Returns:
            ICollector: 收集器實例，如果找不到則返回 None
        """
        # 根據 feed.name 判斷收集器類型
        collector_type = self._get_collector_type_from_feed_name(feed.name)
        
        collector = self._collectors.get(collector_type)
        
        if not collector:
            logger.warning(
                f"找不到對應的收集器：{collector_type}",
                extra={
                    "feed_name": feed.name,
                    "collector_type": collector_type,
                }
            )
        
        return collector
    
    def _get_collector_type_from_feed_name(self, feed_name: str) -> str:
        """
        根據來源名稱判斷收集器類型
        
        Args:
            feed_name: 來源名稱
        
        Returns:
            str: 收集器類型
        """
        feed_name_lower = feed_name.lower()
        
        if "cisa" in feed_name_lower or "kev" in feed_name_lower:
            return "CISA_KEV"
        elif "nvd" in feed_name_lower:
            return "NVD"
        elif "vmware" in feed_name_lower or "vmsa" in feed_name_lower:
            return "VMWARE_VMSA"
        elif "msrc" in feed_name_lower or "microsoft" in feed_name_lower:
            return "MSRC"
        elif "twcert" in feed_name_lower or "tw-cert" in feed_name_lower:
            return "TWCERT"
        else:
            return feed_name.upper().replace(" ", "_")

