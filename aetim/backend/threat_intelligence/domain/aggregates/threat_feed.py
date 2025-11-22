"""
威脅情資來源聚合根

ThreatFeed（威脅情資來源）聚合根包含所有業務邏輯方法，負責維護 ThreatFeed 的一致性。
"""

from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from ..value_objects.threat_feed_priority import ThreatFeedPriority
from ..value_objects.collection_frequency import CollectionFrequency
from ..value_objects.collection_status import CollectionStatus
from ..domain_events.threat_feed_created_event import ThreatFeedCreatedEvent
from ..domain_events.threat_feed_updated_event import ThreatFeedUpdatedEvent
from ..domain_events.collection_status_updated_event import CollectionStatusUpdatedEvent


@dataclass
class ThreatFeed:
    """
    威脅情資來源聚合根
    
    聚合根負責：
    1. 維護聚合的一致性邊界
    2. 實作業務邏輯
    3. 發布領域事件
    """
    
    id: str
    name: str
    description: Optional[str]
    priority: ThreatFeedPriority
    is_enabled: bool = True
    collection_frequency: CollectionFrequency = None
    collection_strategy: Optional[str] = None
    api_key: Optional[str] = None
    last_collection_time: Optional[datetime] = None
    last_collection_status: Optional[CollectionStatus] = None
    last_collection_error: Optional[str] = None
    _domain_events: List = field(default_factory=list, repr=False)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    updated_by: str = "system"
    
    def __post_init__(self):
        """驗證聚合根的有效性"""
        if not self.name or not self.name.strip():
            raise ValueError("威脅情資來源名稱不能為空")
        
        if not isinstance(self.priority, ThreatFeedPriority):
            raise ValueError("priority 必須是 ThreatFeedPriority 值物件")
        
        if self.collection_frequency and not isinstance(self.collection_frequency, CollectionFrequency):
            raise ValueError("collection_frequency 必須是 CollectionFrequency 值物件")
        
        if self.last_collection_status and not isinstance(self.last_collection_status, CollectionStatus):
            raise ValueError("last_collection_status 必須是 CollectionStatus 值物件")
    
    @classmethod
    def create(
        cls,
        name: str,
        priority: str,
        collection_frequency: str,
        description: Optional[str] = None,
        collection_strategy: Optional[str] = None,
        api_key: Optional[str] = None,
        is_enabled: bool = True,
        created_by: str = "system",
    ) -> "ThreatFeed":
        """
        建立威脅情資來源（工廠方法）
        
        Args:
            name: 來源名稱（CISA KEV、NVD 等）
            priority: 優先級（P0/P1/P2/P3）
            collection_frequency: 收集頻率（每小時/每日/每週/每月）
            description: 來源描述（可選）
            collection_strategy: 收集策略說明（可選）
            api_key: API 金鑰（可選）
            is_enabled: 是否啟用（預設 True）
            created_by: 建立者（預設 "system"）
        
        Returns:
            ThreatFeed: 新建立的威脅情資來源聚合根
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        threat_feed = cls(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            priority=ThreatFeedPriority(priority),
            collection_frequency=CollectionFrequency(collection_frequency),
            collection_strategy=collection_strategy,
            api_key=api_key,
            is_enabled=is_enabled,
            created_by=created_by,
            updated_by=created_by,
        )
        
        # 發布領域事件
        threat_feed._domain_events.append(
            ThreatFeedCreatedEvent(
                threat_feed_id=threat_feed.id,
                name=threat_feed.name,
                priority=threat_feed.priority.value,
                collection_frequency=threat_feed.collection_frequency.value,
            )
        )
        
        return threat_feed
    
    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        collection_frequency: Optional[str] = None,
        collection_strategy: Optional[str] = None,
        api_key: Optional[str] = None,
        updated_by: str = "system",
    ) -> None:
        """
        更新威脅情資來源資訊
        
        Args:
            name: 來源名稱（可選）
            description: 來源描述（可選）
            priority: 優先級（可選）
            collection_frequency: 收集頻率（可選）
            collection_strategy: 收集策略說明（可選）
            api_key: API 金鑰（可選）
            updated_by: 更新者（預設 "system"）
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        updated_fields = []
        
        if name is not None:
            if not name.strip():
                raise ValueError("威脅情資來源名稱不能為空")
            self.name = name
            updated_fields.append("name")
        
        if description is not None:
            self.description = description
            updated_fields.append("description")
        
        if priority is not None:
            self.priority = ThreatFeedPriority(priority)
            updated_fields.append("priority")
        
        if collection_frequency is not None:
            self.collection_frequency = CollectionFrequency(collection_frequency)
            updated_fields.append("collection_frequency")
        
        if collection_strategy is not None:
            self.collection_strategy = collection_strategy
            updated_fields.append("collection_strategy")
        
        if api_key is not None:
            self.api_key = api_key
            updated_fields.append("api_key")
        
        if updated_fields:
            self.updated_at = datetime.utcnow()
            self.updated_by = updated_by
            
            # 發布領域事件
            self._domain_events.append(
                ThreatFeedUpdatedEvent(
                    threat_feed_id=self.id,
                    name=self.name,
                    updated_fields=updated_fields,
                )
            )
    
    def toggle(self, updated_by: str = "system") -> None:
        """
        切換威脅情資來源啟用狀態
        
        Args:
            updated_by: 更新者（預設 "system"）
        """
        self.is_enabled = not self.is_enabled
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
        
        # 發布領域事件
        self._domain_events.append(
            ThreatFeedUpdatedEvent(
                threat_feed_id=self.id,
                name=self.name,
                updated_fields=["is_enabled"],
            )
        )
    
    def enable(self, updated_by: str = "system") -> None:
        """
        啟用威脅情資來源
        
        Args:
            updated_by: 更新者（預設 "system"）
        """
        if not self.is_enabled:
            self.toggle(updated_by)
    
    def disable(self, updated_by: str = "system") -> None:
        """
        停用威脅情資來源
        
        Args:
            updated_by: 更新者（預設 "system"）
        """
        if self.is_enabled:
            self.toggle(updated_by)
    
    def update_collection_status(
        self,
        status: str,
        record_count: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        """
        更新收集狀態
        
        Args:
            status: 收集狀態（success/failed/in_progress）
            record_count: 收集的記錄數（預設 0）
            error_message: 錯誤訊息（可選）
        """
        self.last_collection_status = CollectionStatus(status)
        self.last_collection_time = datetime.utcnow()
        self.last_collection_error = error_message
        self.updated_at = datetime.utcnow()
        
        # 發布領域事件
        self._domain_events.append(
            CollectionStatusUpdatedEvent(
                threat_feed_id=self.id,
                name=self.name,
                status=status,
                record_count=record_count,
                error_message=error_message,
            )
        )
    
    def get_domain_events(self) -> List:
        """
        取得領域事件清單
        
        Returns:
            List: 領域事件清單
        """
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """清除領域事件清單"""
        self._domain_events.clear()
    
    def __repr__(self):
        return (
            f"ThreatFeed(id='{self.id}', "
            f"name='{self.name}', "
            f"priority='{self.priority.value}', "
            f"is_enabled={self.is_enabled})"
        )

