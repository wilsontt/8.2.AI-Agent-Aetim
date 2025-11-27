"""
資產統計服務

提供資產統計功能。
"""

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from asset_management.infrastructure.persistence.models import Asset, AssetProduct
from analysis_assessment.infrastructure.persistence.models import ThreatAssetAssociation
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class AssetStatisticsService:
    """
    資產統計服務
    
    提供資產統計功能。
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        初始化統計服務
        
        Args:
            db_session: 資料庫 Session
        """
        self.db_session = db_session
    
    async def get_asset_statistics(self) -> Dict[str, Any]:
        """
        取得資產統計
        
        Returns:
            Dict[str, Any]: 資產統計資料
        """
        # 資產總數統計
        total_count_result = await self.db_session.execute(
            select(func.count(Asset.id))
        )
        total_count = total_count_result.scalar() or 0
        
        # 依資產類型統計（使用 AssetProduct 的 product_type）
        by_type_result = await self.db_session.execute(
            select(
                AssetProduct.product_type,
                func.count(distinct(AssetProduct.asset_id)).label("count"),
            )
            .group_by(AssetProduct.product_type)
        )
        by_type = {
            row.product_type or "Unknown": row.count
            for row in by_type_result.all()
        }
        
        # 依資料敏感度統計
        by_sensitivity_result = await self.db_session.execute(
            select(
                Asset.data_sensitivity,
                func.count(Asset.id).label("count"),
            )
            .group_by(Asset.data_sensitivity)
        )
        by_sensitivity = {
            row.data_sensitivity: row.count
            for row in by_sensitivity_result.all()
        }
        
        # 依業務關鍵性統計
        by_criticality_result = await self.db_session.execute(
            select(
                Asset.business_criticality,
                func.count(Asset.id).label("count"),
            )
            .group_by(Asset.business_criticality)
        )
        by_criticality = {
            row.business_criticality: row.count
            for row in by_criticality_result.all()
        }
        
        # 受威脅影響的資產統計
        affected_assets_result = await self.db_session.execute(
            select(func.count(distinct(ThreatAssetAssociation.asset_id)))
        )
        affected_assets_count = affected_assets_result.scalar() or 0
        
        # 計算受威脅影響的資產百分比
        affected_percentage = (
            (affected_assets_count / total_count * 100) if total_count > 0 else 0
        )
        
        # 對外暴露資產統計
        public_facing_result = await self.db_session.execute(
            select(func.count(Asset.id)).where(Asset.is_public_facing == True)
        )
        public_facing_count = public_facing_result.scalar() or 0
        
        return {
            "total_count": total_count,
            "by_type": by_type,
            "by_sensitivity": by_sensitivity,
            "by_criticality": by_criticality,
            "affected_assets": {
                "count": affected_assets_count,
                "percentage": round(affected_percentage, 2),
            },
            "public_facing_count": public_facing_count,
        }

