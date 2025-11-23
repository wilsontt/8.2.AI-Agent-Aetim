"""
威脅服務

提供威脅管理的業務邏輯。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.interfaces.threat_repository import IThreatRepository
from ...domain.aggregates.threat import Threat
from ...domain.value_objects.threat_status import ThreatStatus
from ...infrastructure.persistence.threat_asset_association_repository import (
    ThreatAssetAssociationRepository,
)
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class ThreatService:
    """
    威脅服務
    
    提供威脅管理的業務邏輯，包括：
    - 查詢威脅
    - 更新威脅狀態
    - 管理威脅-資產關聯
    """
    
    def __init__(
        self,
        threat_repository: IThreatRepository,
        association_repository: ThreatAssetAssociationRepository,
    ):
        """
        初始化威脅服務
        
        Args:
            threat_repository: 威脅 Repository
            association_repository: 威脅資產關聯 Repository
        """
        self.threat_repository = threat_repository
        self.association_repository = association_repository
    
    async def get_threats(
        self,
        page: int = 1,
        page_size: int = 100,
        status: Optional[str] = None,
        threat_feed_id: Optional[str] = None,
        cve_id: Optional[str] = None,
        product_name: Optional[str] = None,
        min_cvss_score: Optional[float] = None,
        max_cvss_score: Optional[float] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """
        取得威脅清單
        
        Args:
            page: 頁碼
            page_size: 每頁筆數
            status: 狀態篩選
            threat_feed_id: 威脅情資來源 ID 篩選
            cve_id: CVE 編號篩選
            product_name: 產品名稱篩選
            min_cvss_score: 最小 CVSS 分數
            max_cvss_score: 最大 CVSS 分數
            sort_by: 排序欄位
            sort_order: 排序順序
        
        Returns:
            Dict: 包含 items, total, page, page_size, total_pages
        """
        skip = (page - 1) * page_size
        
        # 計算總數
        total = await self.threat_repository.count(
            status=status,
            threat_feed_id=threat_feed_id,
            cve_id=cve_id,
            product_name=product_name,
            min_cvss_score=min_cvss_score,
            max_cvss_score=max_cvss_score,
        )
        
        # 查詢威脅
        threats = await self.threat_repository.get_all(
            skip=skip,
            limit=page_size,
            status=status,
            threat_feed_id=threat_feed_id,
            cve_id=cve_id,
            product_name=product_name,
            min_cvss_score=min_cvss_score,
            max_cvss_score=max_cvss_score,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return {
            "items": threats,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    
    async def get_threat_by_id(self, threat_id: str) -> Optional[Threat]:
        """
        根據 ID 取得威脅
        
        Args:
            threat_id: 威脅 ID
        
        Returns:
            Threat: 威脅聚合根，如果不存在則返回 None
        """
        return await self.threat_repository.get_by_id(threat_id)
    
    async def search_threats(
        self,
        query: str,
        page: int = 1,
        page_size: int = 100,
    ) -> Dict[str, Any]:
        """
        搜尋威脅
        
        Args:
            query: 搜尋關鍵字
            page: 頁碼
            page_size: 每頁筆數
        
        Returns:
            Dict: 包含 items, total, page, page_size, total_pages
        """
        skip = (page - 1) * page_size
        
        # 搜尋威脅
        threats = await self.threat_repository.search(query, skip=skip, limit=page_size)
        
        # TODO: 計算總數（目前簡化處理）
        total = len(threats)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return {
            "items": threats,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    
    async def update_threat_status(
        self,
        threat_id: str,
        new_status: str,
    ) -> Threat:
        """
        更新威脅狀態（AC-014-3）
        
        Args:
            threat_id: 威脅 ID
            new_status: 新狀態
        
        Returns:
            Threat: 更新後的威脅聚合根
        
        Raises:
            ValueError: 如果威脅不存在或狀態轉換不合法
        """
        # 取得威脅
        threat = await self.threat_repository.get_by_id(threat_id)
        if not threat:
            raise ValueError(f"找不到威脅：{threat_id}")
        
        # 更新狀態
        threat.update_status(new_status)
        
        # 儲存
        await self.threat_repository.save(threat)
        
        logger.info(
            f"更新威脅狀態：{threat_id} -> {new_status}",
            extra={"threat_id": threat_id, "new_status": new_status}
        )
        
        return threat
    
    async def get_threat_with_associations(self, threat_id: str) -> Dict[str, Any]:
        """
        取得威脅及其關聯的資產
        
        Args:
            threat_id: 威脅 ID
        
        Returns:
            Dict: 包含 threat 和 associated_assets
        
        Raises:
            ValueError: 如果威脅不存在
        """
        # 取得威脅
        threat = await self.threat_repository.get_by_id(threat_id)
        if not threat:
            raise ValueError(f"找不到威脅：{threat_id}")
        
        # 取得關聯的資產
        associations = await self.association_repository.get_by_threat_id(threat_id)
        
        # 轉換關聯資料
        associated_assets = [
            {
                "asset_id": assoc.asset_id,
                "match_confidence": float(assoc.match_confidence),
                "match_type": assoc.match_type,
                "match_details": assoc.match_details,
                "created_at": assoc.created_at.isoformat() if assoc.created_at else None,
            }
            for assoc in associations
        ]
        
        return {
            "threat": threat,
            "associated_assets": associated_assets,
        }

