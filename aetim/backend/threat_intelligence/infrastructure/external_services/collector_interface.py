"""
收集器介面

定義所有威脅情資收集器必須實作的介面。
"""

from abc import ABC, abstractmethod
from typing import List
from ...domain.aggregates.threat import Threat
from ...domain.aggregates.threat_feed import ThreatFeed


class ICollector(ABC):
    """
    收集器介面
    
    所有威脅情資收集器都必須實作此介面。
    """
    
    @abstractmethod
    async def collect(self, feed: ThreatFeed) -> List[Threat]:
        """
        收集威脅情資
        
        Args:
            feed: 威脅情資來源聚合根
        
        Returns:
            List[Threat]: 收集到的威脅列表
        
        Raises:
            CollectorError: 收集失敗時拋出
        """
        pass
    
    @abstractmethod
    def get_collector_type(self) -> str:
        """
        取得收集器類型
        
        Returns:
            str: 收集器類型（例如：CISA_KEV, NVD, VMWARE_VMSA, MSRC, TWCERT）
        """
        pass

