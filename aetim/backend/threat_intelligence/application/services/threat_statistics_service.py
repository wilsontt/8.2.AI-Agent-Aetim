"""
威脅統計服務

提供威脅情資的統計功能。
符合 AC-028-1, AC-028-2。
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case, distinct
from sqlalchemy.orm import selectinload
from threat_intelligence.infrastructure.persistence.models import Threat, ThreatFeed
from analysis_assessment.infrastructure.persistence.models import RiskAssessment, ThreatAssetAssociation
from asset_management.infrastructure.persistence.models import Asset
from shared_kernel.infrastructure.logging import get_logger
from shared_kernel.infrastructure.decorators.cache import cache_result

logger = get_logger(__name__)


class ThreatStatisticsService:
    """
    威脅統計服務
    
    提供威脅情資的統計功能。
    符合 AC-028-1：提供威脅情資的統計圖表
    符合 AC-028-2：支援時間範圍篩選
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        初始化統計服務
        
        Args:
            db_session: 資料庫 Session
        """
        self.db_session = db_session
    
    @cache_result(ttl=300, key_prefix="cache:threat_statistics:trend")
    async def get_threat_trend(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        interval: str = "day",
    ) -> List[Dict[str, Any]]:
        """
        取得威脅數量趨勢
        
        符合 AC-028-1：威脅數量趨勢（依時間）
        符合 AC-028-2：支援時間範圍篩選
        
        Args:
            start_date: 開始日期（可選，預設為最近 30 天）
            end_date: 結束日期（可選，預設為現在）
            interval: 時間間隔（day/week/month）
        
        Returns:
            List[Dict[str, Any]]: 威脅數量趨勢資料
        """
        # 設定預設時間範圍
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            # 根據 interval 設定預設開始日期
            if interval == "day":
                start_date = end_date - timedelta(days=30)
            elif interval == "week":
                start_date = end_date - timedelta(weeks=12)
            elif interval == "month":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
        
        # 建立查詢
        query = select(
            func.date(Threat.created_at).label("date"),
            func.count(Threat.id).label("count"),
        ).where(
            and_(
                Threat.created_at >= start_date,
                Threat.created_at <= end_date,
            )
        )
        
        # 根據 interval 分組
        if interval == "day":
            query = query.group_by(func.date(Threat.created_at))
        elif interval == "week":
            # 使用 SQLite 的 strftime 來取得週
            query = select(
                func.strftime("%Y-W%W", Threat.created_at).label("date"),
                func.count(Threat.id).label("count"),
            ).where(
                and_(
                    Threat.created_at >= start_date,
                    Threat.created_at <= end_date,
                )
            ).group_by(func.strftime("%Y-W%W", Threat.created_at))
        elif interval == "month":
            query = select(
                func.strftime("%Y-%m", Threat.created_at).label("date"),
                func.count(Threat.id).label("count"),
            ).where(
                and_(
                    Threat.created_at >= start_date,
                    Threat.created_at <= end_date,
                )
            ).group_by(func.strftime("%Y-%m", Threat.created_at))
        
        query = query.order_by("date")
        
        # 執行查詢
        result = await self.db_session.execute(query)
        rows = result.all()
        
        # 轉換為字典格式
        trend_data = [
            {
                "date": str(row.date),
                "count": row.count,
            }
            for row in rows
        ]
        
        return trend_data
    
    async def get_risk_distribution(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> Dict[str, Any]:
        """
        取得風險分數分布
        
        符合 AC-028-1：風險分數分布（嚴重/高/中/低）
        
        Args:
            start_date: 開始日期（可選）
            end_date: 結束日期（可選）
        
        Returns:
            Dict[str, Any]: 風險分數分布資料
        """
        # 建立查詢條件
        conditions = []
        if start_date:
            conditions.append(RiskAssessment.created_at >= start_date)
        if end_date:
            conditions.append(RiskAssessment.created_at <= end_date)
        
        # 統計各風險等級的威脅數量
        query = select(
            RiskAssessment.risk_level,
            func.count(RiskAssessment.id).label("count"),
        )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.group_by(RiskAssessment.risk_level)
        
        # 執行查詢
        result = await self.db_session.execute(query)
        rows = result.all()
        
        # 初始化統計資料
        distribution = {
            "Critical": 0,
            "High": 0,
            "Medium": 0,
            "Low": 0,
        }
        
        # 填入統計資料
        for row in rows:
            risk_level = row.risk_level
            if risk_level in distribution:
                distribution[risk_level] = row.count
        
        # 計算總數
        total = sum(distribution.values())
        
        return {
            "distribution": distribution,
            "total": total,
        }
    
    async def get_affected_asset_statistics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> Dict[str, Any]:
        """
        取得受影響資產統計
        
        符合 AC-028-1：受影響資產統計（依資產類型、依資產重要性）
        
        Args:
            start_date: 開始日期（可選）
            end_date: 結束日期（可選）
        
        Returns:
            Dict[str, Any]: 受影響資產統計資料
        """
        # 建立查詢條件
        conditions = []
        if start_date:
            conditions.append(ThreatAssetAssociation.created_at >= start_date)
        if end_date:
            conditions.append(ThreatAssetAssociation.created_at <= end_date)
        
        # 依資產類型統計
        # 使用子查詢來避免重複計算
        query_by_type = select(
            AssetProduct.product_type,
            func.count(distinct(ThreatAssetAssociation.id)).label("count"),
        ).select_from(
            ThreatAssetAssociation
        ).join(
            Asset, ThreatAssetAssociation.asset_id == Asset.id
        ).join(
            AssetProduct, Asset.id == AssetProduct.asset_id
        )
        
        if conditions:
            query_by_type = query_by_type.where(and_(*conditions))
        
        query_by_type = query_by_type.group_by(AssetProduct.product_type)
        
        result_by_type = await self.db_session.execute(query_by_type)
        rows_by_type = result_by_type.all()
        
        by_type = {
            (row.product_type or "Unknown"): row.count
            for row in rows_by_type
        }
        
        # 依資產重要性統計
        query_by_importance = select(
            Asset.business_criticality,
            func.count(distinct(ThreatAssetAssociation.id)).label("count"),
        ).select_from(
            ThreatAssetAssociation
        ).join(
            Asset, ThreatAssetAssociation.asset_id == Asset.id
        )
        
        if conditions:
            query_by_importance = query_by_importance.where(and_(*conditions))
        
        query_by_importance = query_by_importance.group_by(Asset.business_criticality)
        
        result_by_importance = await self.db_session.execute(query_by_importance)
        rows_by_importance = result_by_importance.all()
        
        by_importance = {
            row.business_criticality: row.count
            for row in rows_by_importance
        }
        
        return {
            "by_type": by_type,
            "by_importance": by_importance,
        }
    
    async def get_threat_source_statistics(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> List[Dict[str, Any]]:
        """
        取得威脅來源統計
        
        符合 AC-028-1：威脅來源統計（各來源的威脅數量）
        
        Args:
            start_date: 開始日期（可選）
            end_date: 結束日期（可選）
        
        Returns:
            List[Dict[str, Any]]: 威脅來源統計資料
        """
        # 建立查詢條件
        conditions = []
        if start_date:
            conditions.append(Threat.created_at >= start_date)
        if end_date:
            conditions.append(Threat.created_at <= end_date)
        
        # 統計各來源的威脅數量
        query = select(
            ThreatFeed.name.label("source_name"),
            ThreatFeed.priority.label("priority"),
            func.count(Threat.id).label("count"),
        ).join(
            ThreatFeed, Threat.threat_feed_id == ThreatFeed.id
        )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.group_by(ThreatFeed.id, ThreatFeed.name, ThreatFeed.priority).order_by(
            func.count(Threat.id).desc()
        )
        
        # 執行查詢
        result = await self.db_session.execute(query)
        rows = result.all()
        
        # 轉換為字典格式
        source_statistics = [
            {
                "source_name": row.source_name,
                "priority": row.priority,
                "count": row.count,
            }
            for row in rows
        ]
        
        return source_statistics

