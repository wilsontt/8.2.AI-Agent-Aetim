"""
威脅-資產關聯服務

實作威脅與資產關聯的建立和管理（Application Layer）。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from threat_intelligence.domain.aggregates.threat import Threat
from threat_intelligence.domain.value_objects.threat_status import ThreatStatus
from threat_intelligence.domain.interfaces.threat_repository import IThreatRepository
from threat_intelligence.infrastructure.persistence.threat_asset_association_repository import (
    ThreatAssetAssociationRepository,
)
from analysis_assessment.domain.domain_services.association_analysis_service import (
    AssociationAnalysisService,
    AssociationResult,
)
from asset_management.domain.interfaces.asset_repository import IAssetRepository
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class ThreatAssetAssociationService:
    """
    威脅-資產關聯服務（Application Service）
    
    負責建立和管理威脅與資產的關聯（AC-010-3, AC-010-4）。
    """
    
    def __init__(
        self,
        threat_repository: IThreatRepository,
        asset_repository: IAssetRepository,
        association_repository: ThreatAssetAssociationRepository,
        association_analysis_service: AssociationAnalysisService,
    ):
        """
        初始化威脅-資產關聯服務
        
        Args:
            threat_repository: 威脅 Repository
            asset_repository: 資產 Repository
            association_repository: 威脅-資產關聯 Repository
            association_analysis_service: 關聯分析服務
        """
        self.threat_repository = threat_repository
        self.asset_repository = asset_repository
        self.association_repository = association_repository
        self.association_analysis_service = association_analysis_service
    
    async def create_associations(
        self,
        threat_id: str,
        association_results: List[AssociationResult],
    ) -> Dict[str, Any]:
        """
        建立威脅-資產關聯（AC-010-3）
        
        對每個匹配的資產建立關聯記錄，並更新威脅記錄的關聯狀態。
        
        Args:
            threat_id: 威脅 ID
            association_results: 關聯分析結果列表
        
        Returns:
            Dict: 建立結果，包含：
                - success: bool - 是否成功
                - threat_id: str - 威脅 ID
                - associations_created: int - 建立的關聯數量
                - errors: List[str] - 錯誤訊息列表
        """
        try:
            # 1. 取得威脅
            threat = await self.threat_repository.get_by_id(threat_id)
            if not threat:
                return {
                    "success": False,
                    "threat_id": threat_id,
                    "associations_created": 0,
                    "errors": [f"找不到威脅：{threat_id}"],
                }
            
            # 2. 更新威脅狀態為「分析中」（AC-010-4）
            if threat.status.value != "Analyzing":
                threat.update_status("Analyzing")
                await self.threat_repository.save(threat)
            
            logger.info(
                f"開始建立威脅-資產關聯：{threat_id}",
                extra={
                    "threat_id": threat_id,
                    "threat_title": threat.title,
                    "associations_count": len(association_results),
                }
            )
            
            # 3. 建立關聯記錄
            associations_created = 0
            errors: List[str] = []
            
            for result in association_results:
                try:
                    # 建立匹配詳情（JSON 格式）
                    match_details = {
                        "matched_products": result.matched_products,
                        "os_match": result.os_match,
                        "match_type": result.match_type.value,
                    }
                    
                    # 儲存關聯記錄（AC-010-3）
                    await self.association_repository.save_association(
                        threat_id=result.threat_id,
                        asset_id=result.asset_id,
                        match_confidence=float(result.confidence),
                        match_type=result.match_type.value,
                        match_details=json.dumps(match_details, ensure_ascii=False),
                    )
                    
                    associations_created += 1
                    
                    logger.debug(
                        f"建立威脅-資產關聯：{result.threat_id} - {result.asset_id}",
                        extra={
                            "threat_id": result.threat_id,
                            "asset_id": result.asset_id,
                            "confidence": result.confidence,
                            "match_type": result.match_type.value,
                        }
                    )
                    
                except Exception as e:
                    error_msg = f"建立關聯記錄失敗：{result.asset_id} - {str(e)}"
                    logger.error(
                        error_msg,
                        extra={
                            "threat_id": result.threat_id,
                            "asset_id": result.asset_id,
                            "error": str(e),
                        }
                    )
                    errors.append(error_msg)
            
            # 4. 更新威脅狀態為「已處理」（AC-010-4）
            threat.update_status("Processed")
            await self.threat_repository.save(threat)
            
            logger.info(
                f"威脅-資產關聯建立完成：{threat_id}",
                extra={
                    "threat_id": threat_id,
                    "associations_created": associations_created,
                    "errors_count": len(errors),
                }
            )
            
            return {
                "success": True,
                "threat_id": threat_id,
                "associations_created": associations_created,
                "errors": errors,
            }
        
        except Exception as e:
            error_msg = f"建立威脅-資產關聯時發生未預期錯誤：{str(e)}"
            logger.error(error_msg, exc_info=True, extra={"threat_id": threat_id})
            
            return {
                "success": False,
                "threat_id": threat_id,
                "associations_created": 0,
                "errors": [error_msg],
            }
    
    async def analyze_and_create_associations(
        self,
        threat_id: str,
    ) -> Dict[str, Any]:
        """
        執行關聯分析並建立關聯（AC-010-3, AC-010-4）
        
        這是一個便利方法，整合了關聯分析和關聯建立。
        
        Args:
            threat_id: 威脅 ID
        
        Returns:
            Dict: 建立結果
        """
        try:
            # 1. 取得威脅
            threat = await self.threat_repository.get_by_id(threat_id)
            if not threat:
                return {
                    "success": False,
                    "threat_id": threat_id,
                    "associations_created": 0,
                    "errors": [f"找不到威脅：{threat_id}"],
                }
            
            # 2. 取得所有資產（不分頁，取得全部）
            assets, _ = await self.asset_repository.get_all(
                page=1,
                page_size=10000,  # 設定一個很大的值以取得所有資產
            )
            
            # 3. 執行關聯分析
            association_results = self.association_analysis_service.analyze(
                threat,
                assets,
            )
            
            # 4. 建立關聯記錄
            return await self.create_associations(threat_id, association_results)
        
        except Exception as e:
            error_msg = f"執行關聯分析並建立關聯時發生錯誤：{str(e)}"
            logger.error(error_msg, exc_info=True, extra={"threat_id": threat_id})
            
            return {
                "success": False,
                "threat_id": threat_id,
                "associations_created": 0,
                "errors": [error_msg],
            }
    
    async def update_associations(
        self,
        threat_id: str,
        association_results: List[AssociationResult],
    ) -> Dict[str, Any]:
        """
        更新威脅-資產關聯（AC-010-3）
        
        當資產變更時重新分析，更新或刪除關聯記錄。
        
        Args:
            threat_id: 威脅 ID
            association_results: 新的關聯分析結果列表
        
        Returns:
            Dict: 更新結果
        """
        try:
            # 1. 取得現有關聯
            existing_associations = await self.association_repository.get_by_threat_id(threat_id)
            existing_asset_ids = {assoc.asset_id for assoc in existing_associations}
            
            # 2. 取得新的關聯資產 ID
            new_asset_ids = {result.asset_id for result in association_results}
            
            # 3. 刪除不再匹配的關聯
            deleted_count = 0
            for asset_id in existing_asset_ids - new_asset_ids:
                try:
                    await self.association_repository.delete_association(threat_id, asset_id)
                    deleted_count += 1
                except Exception as e:
                    logger.error(
                        f"刪除關聯記錄失敗：{threat_id} - {asset_id}",
                        extra={
                            "threat_id": threat_id,
                            "asset_id": asset_id,
                            "error": str(e),
                        }
                    )
            
            # 4. 建立或更新關聯記錄
            result = await self.create_associations(threat_id, association_results)
            
            logger.info(
                f"威脅-資產關聯更新完成：{threat_id}",
                extra={
                    "threat_id": threat_id,
                    "associations_created": result["associations_created"],
                    "associations_deleted": deleted_count,
                }
            )
            
            return {
                **result,
                "associations_deleted": deleted_count,
            }
        
        except Exception as e:
            error_msg = f"更新威脅-資產關聯時發生錯誤：{str(e)}"
            logger.error(error_msg, exc_info=True, extra={"threat_id": threat_id})
            
            return {
                "success": False,
                "threat_id": threat_id,
                "associations_created": 0,
                "associations_deleted": 0,
                "errors": [error_msg],
            }
    
    async def get_associations_by_threat_id(
        self,
        threat_id: str,
    ) -> List[Dict[str, Any]]:
        """
        查詢威脅的所有關聯（AC-010-3）
        
        Args:
            threat_id: 威脅 ID
        
        Returns:
            List[Dict]: 關聯列表
        """
        try:
            associations = await self.association_repository.get_by_threat_id(threat_id)
            
            return [
                {
                    "id": assoc.id,
                    "threat_id": assoc.threat_id,
                    "asset_id": assoc.asset_id,
                    "match_confidence": float(assoc.match_confidence),
                    "match_type": assoc.match_type,
                    "match_details": json.loads(assoc.match_details) if assoc.match_details else None,
                    "created_at": assoc.created_at.isoformat() if assoc.created_at else None,
                }
                for assoc in associations
            ]
        
        except Exception as e:
            logger.error(
                f"查詢威脅關聯失敗：{str(e)}",
                extra={"threat_id": threat_id, "error": str(e)}
            )
            raise
    
    async def get_associations_by_asset_id(
        self,
        asset_id: str,
    ) -> List[Dict[str, Any]]:
        """
        查詢資產的所有關聯（AC-010-3）
        
        Args:
            asset_id: 資產 ID
        
        Returns:
            List[Dict]: 關聯列表
        """
        try:
            associations = await self.association_repository.get_by_asset_id(asset_id)
            
            return [
                {
                    "id": assoc.id,
                    "threat_id": assoc.threat_id,
                    "asset_id": assoc.asset_id,
                    "match_confidence": float(assoc.match_confidence),
                    "match_type": assoc.match_type,
                    "match_details": json.loads(assoc.match_details) if assoc.match_details else None,
                    "created_at": assoc.created_at.isoformat() if assoc.created_at else None,
                }
                for assoc in associations
            ]
        
        except Exception as e:
            logger.error(
                f"查詢資產關聯失敗：{str(e)}",
                extra={"asset_id": asset_id, "error": str(e)}
            )
            raise

