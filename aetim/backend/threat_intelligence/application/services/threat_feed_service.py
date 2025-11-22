"""
威脅情資來源服務

提供威脅情資來源的 CRUD 操作和查詢功能。
"""

from typing import Optional, List
from ...domain.interfaces.threat_feed_repository import IThreatFeedRepository
from ...domain.aggregates.threat_feed import ThreatFeed
from ..dtos.threat_feed_dto import (
    CreateThreatFeedRequest,
    UpdateThreatFeedRequest,
    ThreatFeedResponse,
    ThreatFeedListResponse,
    CollectionStatusResponse,
)
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class ThreatFeedService:
    """
    威脅情資來源服務
    
    提供威脅情資來源的 CRUD 操作和查詢功能。
    """
    
    def __init__(self, repository: IThreatFeedRepository):
        """
        初始化服務
        
        Args:
            repository: 威脅情資來源 Repository
        """
        self.repository = repository
    
    async def create_threat_feed(
        self,
        request: CreateThreatFeedRequest,
        user_id: str = "system",
    ) -> str:
        """
        建立威脅情資來源
        
        Args:
            request: 建立威脅情資來源請求
            user_id: 使用者 ID（預設 "system"）
        
        Returns:
            str: 威脅情資來源 ID
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        logger.info("建立威脅情資來源", extra={"name": request.name, "user_id": user_id})
        
        # 1. 建立威脅情資來源聚合
        threat_feed = ThreatFeed.create(
            name=request.name,
            priority=request.priority,
            collection_frequency=request.collection_frequency,
            description=request.description,
            collection_strategy=request.collection_strategy,
            api_key=request.api_key,
            is_enabled=request.is_enabled,
            created_by=user_id,
        )
        
        # 2. 儲存
        await self.repository.save(threat_feed)
        
        # 3. 發布領域事件（如果需要）
        events = threat_feed.get_domain_events()
        if events:
            logger.info("威脅情資來源建立事件", extra={"threat_feed_id": threat_feed.id, "event_count": len(events)})
        
        logger.info("威脅情資來源建立成功", extra={"threat_feed_id": threat_feed.id})
        
        return threat_feed.id
    
    async def update_threat_feed(
        self,
        threat_feed_id: str,
        request: UpdateThreatFeedRequest,
        user_id: str = "system",
    ) -> None:
        """
        更新威脅情資來源
        
        Args:
            threat_feed_id: 威脅情資來源 ID
            request: 更新威脅情資來源請求
            user_id: 使用者 ID（預設 "system"）
        
        Raises:
            ValueError: 當威脅情資來源不存在或輸入參數無效時
        """
        logger.info("更新威脅情資來源", extra={"threat_feed_id": threat_feed_id, "user_id": user_id})
        
        # 1. 取得威脅情資來源
        threat_feed = await self.repository.get_by_id(threat_feed_id)
        if not threat_feed:
            raise ValueError(f"威脅情資來源 ID {threat_feed_id} 不存在")
        
        # 2. 更新威脅情資來源
        update_kwargs = {}
        if request.name is not None:
            update_kwargs["name"] = request.name
        if request.description is not None:
            update_kwargs["description"] = request.description
        if request.priority is not None:
            update_kwargs["priority"] = request.priority
        if request.collection_frequency is not None:
            update_kwargs["collection_frequency"] = request.collection_frequency
        if request.collection_strategy is not None:
            update_kwargs["collection_strategy"] = request.collection_strategy
        if request.api_key is not None:
            update_kwargs["api_key"] = request.api_key
        
        threat_feed.update(updated_by=user_id, **update_kwargs)
        
        # 3. 儲存
        await self.repository.save(threat_feed)
        
        # 4. 發布領域事件（如果需要）
        events = threat_feed.get_domain_events()
        if events:
            logger.info("威脅情資來源更新事件", extra={"threat_feed_id": threat_feed.id, "event_count": len(events)})
        
        logger.info("威脅情資來源更新成功", extra={"threat_feed_id": threat_feed.id})
    
    async def delete_threat_feed(
        self,
        threat_feed_id: str,
        user_id: str = "system",
    ) -> None:
        """
        刪除威脅情資來源
        
        Args:
            threat_feed_id: 威脅情資來源 ID
            user_id: 使用者 ID（預設 "system"）
        
        Raises:
            ValueError: 當威脅情資來源不存在時
        """
        logger.info("刪除威脅情資來源", extra={"threat_feed_id": threat_feed_id, "user_id": user_id})
        
        # 檢查威脅情資來源是否存在
        threat_feed = await self.repository.get_by_id(threat_feed_id)
        if not threat_feed:
            raise ValueError(f"威脅情資來源 ID {threat_feed_id} 不存在")
        
        # 刪除威脅情資來源
        await self.repository.delete(threat_feed_id)
        
        logger.info("威脅情資來源刪除成功", extra={"threat_feed_id": threat_feed_id})
    
    async def toggle_threat_feed(
        self,
        threat_feed_id: str,
        user_id: str = "system",
    ) -> None:
        """
        切換威脅情資來源啟用狀態
        
        Args:
            threat_feed_id: 威脅情資來源 ID
            user_id: 使用者 ID（預設 "system"）
        
        Raises:
            ValueError: 當威脅情資來源不存在時
        """
        logger.info("切換威脅情資來源啟用狀態", extra={"threat_feed_id": threat_feed_id, "user_id": user_id})
        
        # 1. 取得威脅情資來源
        threat_feed = await self.repository.get_by_id(threat_feed_id)
        if not threat_feed:
            raise ValueError(f"威脅情資來源 ID {threat_feed_id} 不存在")
        
        # 2. 切換啟用狀態
        threat_feed.toggle(updated_by=user_id)
        
        # 3. 儲存
        await self.repository.save(threat_feed)
        
        # 4. 發布領域事件（如果需要）
        events = threat_feed.get_domain_events()
        if events:
            logger.info("威脅情資來源切換事件", extra={"threat_feed_id": threat_feed.id, "is_enabled": threat_feed.is_enabled})
        
        logger.info("威脅情資來源切換成功", extra={"threat_feed_id": threat_feed.id, "is_enabled": threat_feed.is_enabled})
    
    async def set_collection_frequency(
        self,
        threat_feed_id: str,
        collection_frequency: str,
        user_id: str = "system",
    ) -> None:
        """
        設定收集頻率
        
        Args:
            threat_feed_id: 威脅情資來源 ID
            collection_frequency: 收集頻率（每小時/每日/每週/每月）
            user_id: 使用者 ID（預設 "system"）
        
        Raises:
            ValueError: 當威脅情資來源不存在或輸入參數無效時
        """
        logger.info("設定收集頻率", extra={"threat_feed_id": threat_feed_id, "collection_frequency": collection_frequency, "user_id": user_id})
        
        # 1. 取得威脅情資來源
        threat_feed = await self.repository.get_by_id(threat_feed_id)
        if not threat_feed:
            raise ValueError(f"威脅情資來源 ID {threat_feed_id} 不存在")
        
        # 2. 更新收集頻率
        threat_feed.update(collection_frequency=collection_frequency, updated_by=user_id)
        
        # 3. 儲存
        await self.repository.save(threat_feed)
        
        logger.info("收集頻率設定成功", extra={"threat_feed_id": threat_feed.id, "collection_frequency": collection_frequency})
    
    async def get_threat_feeds(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> ThreatFeedListResponse:
        """
        查詢威脅情資來源清單（支援分頁、排序）
        
        Args:
            page: 頁碼（從 1 開始）
            page_size: 每頁筆數（預設 20）
            sort_by: 排序欄位
            sort_order: 排序方向（asc/desc）
        
        Returns:
            ThreatFeedListResponse: 威脅情資來源清單回應
        """
        threat_feeds, total_count = await self.repository.get_all(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        
        # 計算總頁數
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
        
        # 轉換為回應格式
        threat_feed_responses = [self._to_response(threat_feed) for threat_feed in threat_feeds]
        
        return ThreatFeedListResponse(
            data=threat_feed_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    async def get_threat_feed_by_id(self, threat_feed_id: str) -> Optional[ThreatFeedResponse]:
        """
        查詢威脅情資來源詳情
        
        Args:
            threat_feed_id: 威脅情資來源 ID
        
        Returns:
            ThreatFeedResponse: 威脅情資來源回應，如果不存在則返回 None
        """
        threat_feed = await self.repository.get_by_id(threat_feed_id)
        
        if not threat_feed:
            return None
        
        return self._to_response(threat_feed)
    
    async def get_enabled_feeds(self) -> List[ThreatFeedResponse]:
        """
        查詢啟用的威脅情資來源
        
        Returns:
            List[ThreatFeedResponse]: 啟用的威脅情資來源清單
        """
        threat_feeds = await self.repository.get_enabled_feeds()
        
        return [self._to_response(threat_feed) for threat_feed in threat_feeds]
    
    async def get_collection_status(self, threat_feed_id: Optional[str] = None) -> List[CollectionStatusResponse]:
        """
        查詢收集狀態
        
        Args:
            threat_feed_id: 威脅情資來源 ID（可選，如果提供則只查詢該來源）
        
        Returns:
            List[CollectionStatusResponse]: 收集狀態清單
        """
        if threat_feed_id:
            threat_feed = await self.repository.get_by_id(threat_feed_id)
            if not threat_feed:
                return []
            threat_feeds = [threat_feed]
        else:
            threat_feeds = await self.repository.get_enabled_feeds()
        
        return [
            CollectionStatusResponse(
                threat_feed_id=threat_feed.id,
                name=threat_feed.name,
                last_collection_time=threat_feed.last_collection_time,
                last_collection_status=threat_feed.last_collection_status.value if threat_feed.last_collection_status else None,
                last_collection_error=threat_feed.last_collection_error,
                is_enabled=threat_feed.is_enabled,
                collection_frequency=threat_feed.collection_frequency.value if threat_feed.collection_frequency else None,
            )
            for threat_feed in threat_feeds
        ]
    
    async def update_collection_status(
        self,
        threat_feed_id: str,
        status: str,
        record_count: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        """
        更新收集狀態與日誌
        
        Args:
            threat_feed_id: 威脅情資來源 ID
            status: 收集狀態（success/failed/in_progress）
            record_count: 收集的記錄數（預設 0）
            error_message: 錯誤訊息（可選）
        
        Raises:
            ValueError: 當威脅情資來源不存在或輸入參數無效時
        """
        logger.info(
            "更新收集狀態",
            extra={
                "threat_feed_id": threat_feed_id,
                "status": status,
                "record_count": record_count,
            }
        )
        
        # 1. 取得威脅情資來源
        threat_feed = await self.repository.get_by_id(threat_feed_id)
        if not threat_feed:
            raise ValueError(f"威脅情資來源 ID {threat_feed_id} 不存在")
        
        # 2. 更新收集狀態
        threat_feed.update_collection_status(status, record_count, error_message)
        
        # 3. 儲存
        await self.repository.save(threat_feed)
        
        # 4. 發布領域事件（如果需要）
        events = threat_feed.get_domain_events()
        if events:
            logger.info("收集狀態更新事件", extra={"threat_feed_id": threat_feed.id, "event_count": len(events)})
        
        logger.info(
            "收集狀態更新成功",
            extra={
                "threat_feed_id": threat_feed.id,
                "status": status,
                "record_count": record_count,
            }
        )
    
    def _to_response(self, threat_feed: ThreatFeed) -> ThreatFeedResponse:
        """
        將領域模型轉換為回應格式
        
        Args:
            threat_feed: 威脅情資來源聚合根
        
        Returns:
            ThreatFeedResponse: 威脅情資來源回應
        """
        return ThreatFeedResponse(
            id=threat_feed.id,
            name=threat_feed.name,
            description=threat_feed.description,
            priority=threat_feed.priority.value,
            is_enabled=threat_feed.is_enabled,
            collection_frequency=threat_feed.collection_frequency.value if threat_feed.collection_frequency else None,
            collection_strategy=threat_feed.collection_strategy,
            last_collection_time=threat_feed.last_collection_time,
            last_collection_status=threat_feed.last_collection_status.value if threat_feed.last_collection_status else None,
            last_collection_error=threat_feed.last_collection_error,
            created_at=threat_feed.created_at,
            updated_at=threat_feed.updated_at,
            created_by=threat_feed.created_by,
            updated_by=threat_feed.updated_by,
        )

