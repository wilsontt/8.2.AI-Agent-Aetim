"""
威脅情資來源 Repository 實作

使用 SQLAlchemy 實作 ThreatFeed 的持久化操作。
"""

from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.interfaces.threat_feed_repository import IThreatFeedRepository
from ...domain.aggregates.threat_feed import ThreatFeed
from .models import ThreatFeed as ThreatFeedModel
from .threat_feed_mapper import ThreatFeedMapper


class ThreatFeedRepository(IThreatFeedRepository):
    """威脅情資來源 Repository 實作"""
    
    def __init__(self, session: AsyncSession):
        """
        初始化 Repository
        
        Args:
            session: 資料庫 Session
        """
        self.session = session
    
    async def save(self, threat_feed: ThreatFeed) -> None:
        """
        儲存威脅情資來源（新增或更新）
        
        Args:
            threat_feed: 威脅情資來源聚合根
        """
        # 檢查威脅情資來源是否存在
        result = await self.session.execute(
            select(ThreatFeedModel).where(ThreatFeedModel.id == threat_feed.id)
        )
        existing_feed = result.scalar_one_or_none()
        
        if existing_feed:
            # 更新現有威脅情資來源
            ThreatFeedMapper.update_model(existing_feed, threat_feed)
            self.session.add(existing_feed)
        else:
            # 新增威脅情資來源
            threat_feed_model = ThreatFeedMapper.to_model(threat_feed)
            self.session.add(threat_feed_model)
        
        await self.session.commit()
    
    async def get_by_id(self, threat_feed_id: str) -> Optional[ThreatFeed]:
        """
        依 ID 查詢威脅情資來源
        
        Args:
            threat_feed_id: 威脅情資來源 ID
        
        Returns:
            ThreatFeed: 威脅情資來源聚合根，如果不存在則返回 None
        """
        result = await self.session.execute(
            select(ThreatFeedModel).where(ThreatFeedModel.id == threat_feed_id)
        )
        threat_feed_model = result.scalar_one_or_none()
        
        if not threat_feed_model:
            return None
        
        return ThreatFeedMapper.to_domain(threat_feed_model)
    
    async def get_by_name(self, name: str) -> Optional[ThreatFeed]:
        """
        依名稱查詢威脅情資來源
        
        Args:
            name: 威脅情資來源名稱
        
        Returns:
            ThreatFeed: 威脅情資來源聚合根，如果不存在則返回 None
        """
        result = await self.session.execute(
            select(ThreatFeedModel).where(ThreatFeedModel.name == name)
        )
        threat_feed_model = result.scalar_one_or_none()
        
        if not threat_feed_model:
            return None
        
        return ThreatFeedMapper.to_domain(threat_feed_model)
    
    async def delete(self, threat_feed_id: str) -> None:
        """
        刪除威脅情資來源
        
        Args:
            threat_feed_id: 威脅情資來源 ID
        
        Raises:
            ValueError: 當威脅情資來源不存在時
        """
        result = await self.session.execute(
            select(ThreatFeedModel).where(ThreatFeedModel.id == threat_feed_id)
        )
        threat_feed_model = result.scalar_one_or_none()
        
        if not threat_feed_model:
            raise ValueError(f"威脅情資來源 ID {threat_feed_id} 不存在")
        
        await self.session.delete(threat_feed_model)
        await self.session.commit()
    
    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> Tuple[List[ThreatFeed], int]:
        """
        查詢所有威脅情資來源（支援分頁與排序）
        
        Args:
            page: 頁碼（從 1 開始）
            page_size: 每頁筆數（預設 20）
            sort_by: 排序欄位（name、priority、created_at 等）
            sort_order: 排序方向（asc、desc）
        
        Returns:
            Tuple[List[ThreatFeed], int]: (威脅情資來源清單, 總筆數)
        """
        # 建立查詢
        query = select(ThreatFeedModel)
        
        # 排序
        if sort_by:
            sort_column = self._get_sort_column(sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            # 預設排序：依優先級升序，然後依建立時間降序
            query = query.order_by(ThreatFeedModel.priority.asc(), ThreatFeedModel.created_at.desc())
        
        # 計算總筆數
        count_query = select(func.count(ThreatFeedModel.id))
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar()
        
        # 分頁
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # 執行查詢
        result = await self.session.execute(query)
        threat_feed_models = result.scalars().all()
        
        # 轉換為領域模型
        threat_feeds = [ThreatFeedMapper.to_domain(model) for model in threat_feed_models]
        
        return threat_feeds, total_count
    
    async def get_enabled_feeds(self) -> List[ThreatFeed]:
        """
        查詢啟用的威脅情資來源
        
        Returns:
            List[ThreatFeed]: 啟用的威脅情資來源清單（依優先級排序）
        """
        result = await self.session.execute(
            select(ThreatFeedModel)
            .where(ThreatFeedModel.is_enabled == True)
            .order_by(ThreatFeedModel.priority.asc())
        )
        threat_feed_models = result.scalars().all()
        
        # 轉換為領域模型
        threat_feeds = [ThreatFeedMapper.to_domain(model) for model in threat_feed_models]
        
        return threat_feeds
    
    async def get_feeds_by_priority(self, priority: str) -> List[ThreatFeed]:
        """
        查詢指定優先級的威脅情資來源
        
        Args:
            priority: 優先級（P0/P1/P2/P3）
        
        Returns:
            List[ThreatFeed]: 威脅情資來源清單
        """
        result = await self.session.execute(
            select(ThreatFeedModel)
            .where(ThreatFeedModel.priority == priority)
            .where(ThreatFeedModel.is_enabled == True)
            .order_by(ThreatFeedModel.created_at.desc())
        )
        threat_feed_models = result.scalars().all()
        
        # 轉換為領域模型
        threat_feeds = [ThreatFeedMapper.to_domain(model) for model in threat_feed_models]
        
        return threat_feeds
    
    def _get_sort_column(self, sort_by: str):
        """
        取得排序欄位
        
        Args:
            sort_by: 排序欄位名稱
        
        Returns:
            排序欄位
        
        Raises:
            ValueError: 當排序欄位無效時
        """
        sort_mapping = {
            "name": ThreatFeedModel.name,
            "priority": ThreatFeedModel.priority,
            "created_at": ThreatFeedModel.created_at,
            "updated_at": ThreatFeedModel.updated_at,
            "is_enabled": ThreatFeedModel.is_enabled,
            "last_collection_time": ThreatFeedModel.last_collection_time,
        }
        
        if sort_by not in sort_mapping:
            raise ValueError(f"無效的排序欄位：{sort_by}")
        
        return sort_mapping[sort_by]

