"""
威脅資產關聯 Repository

實作威脅與資產關聯的資料持久化邏輯。
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import ThreatAssetAssociation as ThreatAssetAssociationModel
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class ThreatAssetAssociationRepository:
    """
    威脅資產關聯 Repository
    
    實作威脅與資產關聯的資料持久化邏輯，使用 SQLAlchemy。
    """
    
    def __init__(self, session: AsyncSession):
        """
        初始化 Repository
        
        Args:
            session: 資料庫會話
        """
        self.session = session
    
    async def save_association(
        self,
        threat_id: str,
        asset_id: str,
        match_confidence: float,
        match_type: str,
        match_details: Optional[str] = None,
    ) -> None:
        """
        儲存威脅-資產關聯（AC-014-4）
        
        Args:
            threat_id: 威脅 ID
            asset_id: 資產 ID
            match_confidence: 匹配信心分數（0.0-1.0）
            match_type: 匹配類型（Exact/Fuzzy/VersionRange）
            match_details: 匹配詳情（JSON 格式，可選）
        """
        try:
            # 檢查是否已存在
            stmt = select(ThreatAssetAssociationModel).where(
                ThreatAssetAssociationModel.threat_id == threat_id,
                ThreatAssetAssociationModel.asset_id == asset_id,
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # 更新現有關聯
                existing.match_confidence = match_confidence
                existing.match_type = match_type
                existing.match_details = match_details
                logger.debug(
                    f"更新威脅資產關聯：{threat_id} - {asset_id}",
                    extra={"threat_id": threat_id, "asset_id": asset_id}
                )
            else:
                # 新增新關聯
                association = ThreatAssetAssociationModel(
                    threat_id=threat_id,
                    asset_id=asset_id,
                    match_confidence=match_confidence,
                    match_type=match_type,
                    match_details=match_details,
                )
                self.session.add(association)
                logger.debug(
                    f"新增威脅資產關聯：{threat_id} - {asset_id}",
                    extra={"threat_id": threat_id, "asset_id": asset_id}
                )
            
            await self.session.commit()
            
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"儲存威脅資產關聯失敗：{str(e)}",
                extra={
                    "threat_id": threat_id,
                    "asset_id": asset_id,
                    "error": str(e),
                }
            )
            raise
    
    async def get_by_threat_id(self, threat_id: str) -> List[ThreatAssetAssociationModel]:
        """
        查詢威脅的所有關聯
        
        Args:
            threat_id: 威脅 ID
        
        Returns:
            List[ThreatAssetAssociationModel]: 關聯列表
        """
        try:
            stmt = select(ThreatAssetAssociationModel).where(
                ThreatAssetAssociationModel.threat_id == threat_id
            )
            result = await self.session.execute(stmt)
            associations = result.scalars().all()
            
            return list(associations)
            
        except Exception as e:
            logger.error(
                f"查詢威脅關聯失敗：{str(e)}",
                extra={"threat_id": threat_id, "error": str(e)}
            )
            raise
    
    async def get_by_asset_id(self, asset_id: str) -> List[ThreatAssetAssociationModel]:
        """
        查詢資產的所有關聯
        
        Args:
            asset_id: 資產 ID
        
        Returns:
            List[ThreatAssetAssociationModel]: 關聯列表
        """
        try:
            stmt = select(ThreatAssetAssociationModel).where(
                ThreatAssetAssociationModel.asset_id == asset_id
            )
            result = await self.session.execute(stmt)
            associations = result.scalars().all()
            
            return list(associations)
            
        except Exception as e:
            logger.error(
                f"查詢資產關聯失敗：{str(e)}",
                extra={"asset_id": asset_id, "error": str(e)}
            )
            raise
    
    async def delete_association(self, threat_id: str, asset_id: str) -> None:
        """
        刪除威脅-資產關聯
        
        Args:
            threat_id: 威脅 ID
            asset_id: 資產 ID
        """
        try:
            stmt = select(ThreatAssetAssociationModel).where(
                ThreatAssetAssociationModel.threat_id == threat_id,
                ThreatAssetAssociationModel.asset_id == asset_id,
            )
            result = await self.session.execute(stmt)
            association = result.scalar_one_or_none()
            
            if association:
                await self.session.delete(association)
                await self.session.commit()
                logger.debug(
                    f"刪除威脅資產關聯：{threat_id} - {asset_id}",
                    extra={"threat_id": threat_id, "asset_id": asset_id}
                )
            
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"刪除威脅資產關聯失敗：{str(e)}",
                extra={
                    "threat_id": threat_id,
                    "asset_id": asset_id,
                    "error": str(e),
                }
            )
            raise

