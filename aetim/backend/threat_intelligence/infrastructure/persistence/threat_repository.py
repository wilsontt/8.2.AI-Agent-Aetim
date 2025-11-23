"""
威脅 Repository

實作威脅資料持久化邏輯。
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from ...domain.interfaces.threat_repository import IThreatRepository
from ...domain.aggregates.threat import Threat
from ..models import Threat as ThreatModel
from .threat_mapper import ThreatMapper
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class ThreatRepository(IThreatRepository):
    """
    威脅 Repository
    
    實作威脅資料持久化邏輯，使用 SQLAlchemy。
    """
    
    def __init__(self, session: AsyncSession):
        """
        初始化 Repository
        
        Args:
            session: 資料庫會話
        """
        self.session = session
    
    async def save(self, threat: Threat) -> None:
        """
        儲存威脅（新增或更新，AC-014-1）
        
        Args:
            threat: 威脅聚合根
        """
        try:
            # 檢查是否已存在
            existing_model = await self.session.get(ThreatModel, threat.id)
            
            if existing_model:
                # 更新現有記錄
                ThreatMapper.update_model(existing_model, threat)
                logger.debug(
                    f"更新威脅：{threat.id}",
                    extra={"threat_id": threat.id, "cve_id": threat.cve_id}
                )
            else:
                # 新增新記錄
                model = ThreatMapper.to_model(threat)
                self.session.add(model)
                logger.debug(
                    f"新增威脅：{threat.id}",
                    extra={"threat_id": threat.id, "cve_id": threat.cve_id}
                )
            
            await self.session.commit()
            
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"儲存威脅失敗：{str(e)}",
                extra={"threat_id": threat.id, "error": str(e)}
            )
            raise
    
    async def get_by_id(self, threat_id: str) -> Optional[Threat]:
        """
        根據 ID 取得威脅
        
        Args:
            threat_id: 威脅 ID
        
        Returns:
            Threat: 威脅聚合根，如果不存在則返回 None
        """
        try:
            model = await self.session.get(ThreatModel, threat_id)
            if not model:
                return None
            
            return ThreatMapper.to_domain(model)
            
        except Exception as e:
            logger.error(
                f"取得威脅失敗：{str(e)}",
                extra={"threat_id": threat_id, "error": str(e)}
            )
            raise
    
    async def get_by_cve(self, cve_id: str) -> Optional[Threat]:
        """
        根據 CVE 編號取得威脅
        
        Args:
            cve_id: CVE 編號
        
        Returns:
            Threat: 威脅聚合根，如果不存在則返回 None
        """
        try:
            stmt = select(ThreatModel).where(ThreatModel.cve == cve_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return None
            
            return ThreatMapper.to_domain(model)
            
        except Exception as e:
            logger.error(
                f"根據 CVE 取得威脅失敗：{str(e)}",
                extra={"cve_id": cve_id, "error": str(e)}
            )
            raise
    
    async def exists_by_cve(self, cve_id: str) -> bool:
        """
        檢查 CVE 是否存在
        
        Args:
            cve_id: CVE 編號
        
        Returns:
            bool: 如果存在則返回 True
        """
        try:
            stmt = select(func.count(ThreatModel.id)).where(ThreatModel.cve == cve_id)
            result = await self.session.execute(stmt)
            count = result.scalar()
            return count > 0
            
        except Exception as e:
            logger.error(
                f"檢查 CVE 是否存在失敗：{str(e)}",
                extra={"cve_id": cve_id, "error": str(e)}
            )
            raise
    
    async def delete(self, threat_id: str) -> None:
        """
        刪除威脅
        
        Args:
            threat_id: 威脅 ID
        """
        try:
            model = await self.session.get(ThreatModel, threat_id)
            if model:
                await self.session.delete(model)
                await self.session.commit()
                logger.debug(
                    f"刪除威脅：{threat_id}",
                    extra={"threat_id": threat_id}
                )
            
        except Exception as e:
            await self.session.rollback()
            logger.error(
                f"刪除威脅失敗：{str(e)}",
                extra={"threat_id": threat_id, "error": str(e)}
            )
            raise
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        threat_feed_id: Optional[str] = None,
        cve_id: Optional[str] = None,
        product_name: Optional[str] = None,
        min_cvss_score: Optional[float] = None,
        max_cvss_score: Optional[float] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> List[Threat]:
        """
        取得所有威脅（支援分頁、排序、篩選，AC-014-3）
        
        Args:
            skip: 跳過的記錄數
            limit: 返回的記錄數
            status: 狀態篩選（可選）
            threat_feed_id: 威脅情資來源 ID 篩選（可選）
            cve_id: CVE 編號篩選（可選）
            product_name: 產品名稱篩選（可選，在 affected_products JSON 中搜尋）
            min_cvss_score: 最小 CVSS 分數（可選）
            max_cvss_score: 最大 CVSS 分數（可選）
            sort_by: 排序欄位（可選：created_at, updated_at, cvss_base_score, published_date）
            sort_order: 排序順序（asc 或 desc，預設 desc）
        
        Returns:
            List[Threat]: 威脅列表
        """
        try:
            # 建立查詢
            stmt = select(ThreatModel)
            
            # 應用篩選條件
            conditions = []
            
            if status:
                conditions.append(ThreatModel.status == status)
            
            if threat_feed_id:
                conditions.append(ThreatModel.threat_feed_id == threat_feed_id)
            
            if cve_id:
                conditions.append(ThreatModel.cve == cve_id)
            
            if min_cvss_score is not None:
                conditions.append(ThreatModel.cvss_base_score >= min_cvss_score)
            
            if max_cvss_score is not None:
                conditions.append(ThreatModel.cvss_base_score <= max_cvss_score)
            
            # 產品名稱篩選（在 JSON 欄位中搜尋）
            if product_name:
                # SQLite 使用 LIKE 搜尋 JSON 欄位
                conditions.append(ThreatModel.affected_products.like(f'%"{product_name}"%'))
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            # 應用排序
            if sort_by:
                sort_column = None
                if sort_by == "created_at":
                    sort_column = ThreatModel.created_at
                elif sort_by == "updated_at":
                    sort_column = ThreatModel.updated_at
                elif sort_by == "cvss_base_score":
                    sort_column = ThreatModel.cvss_base_score
                elif sort_by == "published_date":
                    sort_column = ThreatModel.published_date
                
                if sort_column:
                    if sort_order.lower() == "asc":
                        stmt = stmt.order_by(sort_column.asc())
                    else:
                        stmt = stmt.order_by(sort_column.desc())
            else:
                # 預設按建立時間降序
                stmt = stmt.order_by(ThreatModel.created_at.desc())
            
            # 應用分頁
            stmt = stmt.offset(skip).limit(limit)
            
            # 執行查詢
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            # 轉換為領域模型
            threats = [ThreatMapper.to_domain(model) for model in models]
            
            return threats
            
        except Exception as e:
            logger.error(
                f"取得威脅列表失敗：{str(e)}",
                extra={
                    "skip": skip,
                    "limit": limit,
                    "status": status,
                    "error": str(e),
                }
            )
            raise
    
    async def search(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Threat]:
        """
        搜尋威脅（全文搜尋，標題、描述）
        
        Args:
            query: 搜尋關鍵字
            skip: 跳過的記錄數
            limit: 返回的記錄數
        
        Returns:
            List[Threat]: 威脅列表
        """
        try:
            # 建立查詢（在標題和描述中搜尋）
            stmt = select(ThreatModel).where(
                or_(
                    ThreatModel.title.like(f"%{query}%"),
                    ThreatModel.description.like(f"%{query}%"),
                )
            )
            
            # 按相關性排序（標題匹配優先於描述匹配）
            stmt = stmt.order_by(
                ThreatModel.title.like(f"%{query}%").desc(),
                ThreatModel.created_at.desc(),
            )
            
            # 應用分頁
            stmt = stmt.offset(skip).limit(limit)
            
            # 執行查詢
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            # 轉換為領域模型
            threats = [ThreatMapper.to_domain(model) for model in models]
            
            return threats
            
        except Exception as e:
            logger.error(
                f"搜尋威脅失敗：{str(e)}",
                extra={"query": query, "error": str(e)}
            )
            raise

