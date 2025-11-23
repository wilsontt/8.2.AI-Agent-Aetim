"""
關聯分析服務

實作威脅與資產的關聯分析邏輯（Domain Service）。
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import re

from threat_intelligence.domain.aggregates.threat import Threat
from threat_intelligence.domain.entities.threat_product import ThreatProduct
from asset_management.domain.aggregates.asset import Asset
from asset_management.domain.entities.asset_product import AssetProduct
from .product_name_matcher import ProductNameMatcher
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class MatchType(Enum):
    """比對類型"""
    
    EXACT_PRODUCT_EXACT_VERSION = "exact_product_exact_version"  # 精確產品名稱 + 精確版本
    EXACT_PRODUCT_VERSION_RANGE = "exact_product_version_range"  # 精確產品名稱 + 版本範圍
    EXACT_PRODUCT_MAJOR_VERSION = "exact_product_major_version"  # 精確產品名稱 + 主版本
    EXACT_PRODUCT_NO_VERSION = "exact_product_no_version"  # 精確產品名稱 + 無版本
    FUZZY_PRODUCT_EXACT_VERSION = "fuzzy_product_exact_version"  # 模糊產品名稱 + 精確版本
    FUZZY_PRODUCT_VERSION_RANGE = "fuzzy_product_version_range"  # 模糊產品名稱 + 版本範圍
    FUZZY_PRODUCT_MAJOR_VERSION = "fuzzy_product_major_version"  # 模糊產品名稱 + 主版本
    FUZZY_PRODUCT_NO_VERSION = "fuzzy_product_no_version"  # 模糊產品名稱 + 無版本
    OS_MATCH = "os_match"  # 作業系統匹配


@dataclass
class AssociationResult:
    """
    關聯分析結果
    
    表示威脅與資產的關聯分析結果。
    """
    
    threat_id: str
    asset_id: str
    confidence: float  # 信心分數（0.0 - 1.0）
    match_type: MatchType
    matched_products: List[Dict[str, str]]  # 匹配的產品資訊
    os_match: bool = False  # 是否匹配作業系統
    
    def __str__(self) -> str:
        return (
            f"AssociationResult(threat_id={self.threat_id}, "
            f"asset_id={self.asset_id}, "
            f"confidence={self.confidence:.2f}, "
            f"match_type={self.match_type.value})"
        )


class AssociationAnalysisService:
    """
    關聯分析服務（Domain Service）
    
    負責分析威脅與資產的關聯，實作模糊比對邏輯（AC-010-1, AC-010-2）。
    """
    
    def __init__(self, product_name_matcher: Optional[ProductNameMatcher] = None):
        """
        初始化關聯分析服務
        
        Args:
            product_name_matcher: 產品名稱比對器（可選，預設建立新實例）
        """
        self.product_name_matcher = product_name_matcher or ProductNameMatcher()
    
    def analyze(
        self,
        threat: Threat,
        assets: List[Asset],
    ) -> List[AssociationResult]:
        """
        分析威脅與資產的關聯（AC-010-1, AC-010-3）
        
        Args:
            threat: 威脅聚合根
            assets: 資產清單
        
        Returns:
            List[AssociationResult]: 關聯分析結果清單
        """
        results: List[AssociationResult] = []
        
        logger.info(
            f"開始關聯分析：威脅 {threat.id}，資產數量 {len(assets)}",
            extra={
                "threat_id": threat.id,
                "threat_title": threat.title,
                "assets_count": len(assets),
            }
        )
        
        for asset in assets:
            match_result = self._match_threat_to_asset(threat, asset)
            if match_result and match_result.confidence > 0:
                results.append(match_result)
                logger.debug(
                    f"發現關聯：威脅 {threat.id} <-> 資產 {asset.id}",
                    extra={
                        "threat_id": threat.id,
                        "asset_id": asset.id,
                        "confidence": match_result.confidence,
                        "match_type": match_result.match_type.value,
                    }
                )
        
        logger.info(
            f"關聯分析完成：威脅 {threat.id}，找到 {len(results)} 個受影響資產",
            extra={
                "threat_id": threat.id,
                "affected_assets_count": len(results),
            }
        )
        
        return results
    
    def _match_threat_to_asset(
        self,
        threat: Threat,
        asset: Asset,
    ) -> Optional[AssociationResult]:
        """
        模糊比對威脅與資產（AC-010-2）
        
        Args:
            threat: 威脅聚合根
            asset: 資產聚合根
        
        Returns:
            Optional[AssociationResult]: 比對結果，如果不匹配則返回 None
        """
        best_match: Optional[AssociationResult] = None
        best_confidence = 0.0
        
        # 1. 產品名稱比對（精確與模糊比對）
        for threat_product in threat.products:
            for asset_product in asset.products:
                match_result = self._match_products(
                    threat_product,
                    asset_product,
                    threat.id,
                    asset.id,
                )
                
                if match_result and match_result.confidence > best_confidence:
                    best_match = match_result
                    best_confidence = match_result.confidence
        
        # 2. 作業系統比對（如果威脅影響作業系統）
        os_match_result = self._match_operating_system(threat, asset)
        if os_match_result and os_match_result.confidence > best_confidence:
            best_match = os_match_result
            best_confidence = os_match_result.confidence
        
        return best_match
    
    def _match_products(
        self,
        threat_product: ThreatProduct,
        asset_product: AssetProduct,
        threat_id: str,
        asset_id: str,
    ) -> Optional[AssociationResult]:
        """
        比對威脅產品與資產產品（AC-010-1, AC-010-2）
        
        Args:
            threat_product: 威脅產品
            asset_product: 資產產品
            threat_id: 威脅 ID
            asset_id: 資產 ID
        
        Returns:
            Optional[AssociationResult]: 比對結果
        """
        # 使用產品名稱比對器進行比對
        match_result = self.product_name_matcher.match(
            threat_product.product_name,
            asset_product.product_name,
            allow_fuzzy=True,
        )
        
        # 1. 精確匹配
        if match_result.is_exact and match_result.is_match:
            # 精確產品名稱匹配，檢查版本
            version_match = self._match_version(
                threat_product.product_version,
                asset_product.product_version,
            )
            
            if version_match["is_match"]:
                # 確定最終的 match_type（精確產品名稱 + 版本匹配類型）
                match_type = version_match["match_type"]
                
                confidence = self._calculate_confidence(
                    is_exact_product=True,
                    version_match_type=match_type,
                )
                
                return AssociationResult(
                    threat_id=threat_id,
                    asset_id=asset_id,
                    confidence=confidence,
                    match_type=match_type,
                    matched_products=[
                        {
                            "threat_product": threat_product.product_name,
                            "threat_version": threat_product.product_version or "N/A",
                            "asset_product": asset_product.product_name,
                            "asset_version": asset_product.product_version or "N/A",
                        }
                    ],
                )
        
        # 2. 模糊匹配
        if match_result.is_match and not match_result.is_exact:
            # 模糊產品名稱匹配，檢查版本
            version_match = self._match_version(
                threat_product.product_version,
                asset_product.product_version,
            )
            
            if version_match["is_match"]:
                # 確定最終的 match_type（模糊產品名稱 + 版本匹配類型）
                base_match_type = version_match["match_type"]
                # 將精確產品名稱的 match_type 轉換為模糊產品名稱的 match_type
                match_type_mapping = {
                    MatchType.EXACT_PRODUCT_EXACT_VERSION: MatchType.FUZZY_PRODUCT_EXACT_VERSION,
                    MatchType.EXACT_PRODUCT_VERSION_RANGE: MatchType.FUZZY_PRODUCT_VERSION_RANGE,
                    MatchType.EXACT_PRODUCT_MAJOR_VERSION: MatchType.FUZZY_PRODUCT_MAJOR_VERSION,
                    MatchType.EXACT_PRODUCT_NO_VERSION: MatchType.FUZZY_PRODUCT_NO_VERSION,
                }
                match_type = match_type_mapping.get(base_match_type, base_match_type)
                
                confidence = self._calculate_confidence(
                    is_exact_product=False,
                    version_match_type=match_type,
                    product_similarity=match_result.similarity,
                )
                
                return AssociationResult(
                    threat_id=threat_id,
                    asset_id=asset_id,
                    confidence=confidence,
                    match_type=match_type,
                    matched_products=[
                        {
                            "threat_product": threat_product.product_name,
                            "threat_version": threat_product.product_version or "N/A",
                            "asset_product": asset_product.product_name,
                            "asset_version": asset_product.product_version or "N/A",
                        }
                    ],
                )
        
        return None
    
    def _match_version(
        self,
        threat_version: Optional[str],
        asset_version: Optional[str],
    ) -> Dict[str, any]:
        """
        比對版本（AC-010-2）
        
        支援：
        - 精確版本匹配
        - 版本範圍匹配（如 "7.0.x" 匹配 "7.0.1", "7.0.2" 等）
        - 主版本匹配（如 "7" 匹配 "7.0", "7.1", "7.2" 等）
        
        Args:
            threat_version: 威脅產品版本
            asset_version: 資產產品版本
        
        Returns:
            Dict: 包含 is_match, match_type 的字典
        """
        # 如果兩個版本都為空，視為匹配（無版本資訊）
        if not threat_version and not asset_version:
            return {
                "is_match": True,
                "match_type": MatchType.EXACT_PRODUCT_NO_VERSION,
            }
        
        # 如果威脅版本為空，視為匹配（威脅影響所有版本）
        if not threat_version:
            return {
                "is_match": True,
                "match_type": MatchType.EXACT_PRODUCT_NO_VERSION,
            }
        
        # 如果資產版本為空，無法比對
        if not asset_version:
            return {
                "is_match": False,
                "match_type": None,
            }
        
        # 標準化版本字串
        threat_version_clean = self._normalize_version(threat_version)
        asset_version_clean = self._normalize_version(asset_version)
        
        # 1. 精確版本匹配
        if threat_version_clean == asset_version_clean:
            return {
                "is_match": True,
                "match_type": MatchType.EXACT_PRODUCT_EXACT_VERSION,
            }
        
        # 2. 版本範圍匹配（如 "7.0.x" 匹配 "7.0.1", "7.0.2" 等）
        if threat_version_clean.endswith(".x"):
            base_version = threat_version_clean[:-2]  # 移除 ".x"
            if asset_version_clean.startswith(base_version):
                return {
                    "is_match": True,
                    "match_type": MatchType.EXACT_PRODUCT_VERSION_RANGE,
                }
        
        # 3. 主版本匹配（如 "7" 匹配 "7.0", "7.1", "7.2" 等）
        threat_version_parts = threat_version_clean.split(".")
        asset_version_parts = asset_version_clean.split(".")
        
        if len(threat_version_parts) >= 1 and len(asset_version_parts) >= 1:
            if threat_version_parts[0] == asset_version_parts[0]:
                return {
                    "is_match": True,
                    "match_type": MatchType.EXACT_PRODUCT_MAJOR_VERSION,
                }
        
        return {
            "is_match": False,
            "match_type": None,
        }
    
    def _match_operating_system(
        self,
        threat: Threat,
        asset: Asset,
    ) -> Optional[AssociationResult]:
        """
        比對作業系統（AC-010-1）
        
        Args:
            threat: 威脅聚合根
            asset: 資產聚合根
        
        Returns:
            Optional[AssociationResult]: 比對結果
        """
        # 檢查威脅是否影響作業系統
        os_products = [
            p for p in threat.products
            if p.product_type and p.product_type.lower() in ["operating system", "os", "作業系統"]
        ]
        
        if not os_products:
            return None
        
        for os_product in os_products:
            # 使用產品名稱比對器進行比對
            os_match_result = self.product_name_matcher.match(
                os_product.product_name,
                asset.operating_system,
                allow_fuzzy=True,
            )
            
            # 精確匹配
            if os_match_result.is_exact and os_match_result.is_match:
                return AssociationResult(
                    threat_id=threat.id,
                    asset_id=asset.id,
                    confidence=0.9,  # 作業系統匹配的信心分數
                    match_type=MatchType.OS_MATCH,
                    matched_products=[
                        {
                            "threat_os": os_product.product_name,
                            "asset_os": asset.operating_system,
                        }
                    ],
                    os_match=True,
                )
            
            # 模糊匹配
            if os_match_result.is_match and not os_match_result.is_exact:
                return AssociationResult(
                    threat_id=threat.id,
                    asset_id=asset.id,
                    confidence=0.8 * os_match_result.similarity,  # 模糊匹配的信心分數
                    match_type=MatchType.OS_MATCH,
                    matched_products=[
                        {
                            "threat_os": os_product.product_name,
                            "asset_os": asset.operating_system,
                        }
                    ],
                    os_match=True,
                )
        
        return None
    
    def _normalize_version(self, version: str) -> str:
        """
        標準化版本字串
        
        Args:
            version: 版本字串
        
        Returns:
            str: 標準化後的版本字串
        """
        if not version:
            return ""
        
        # 移除前後空格
        normalized = version.strip()
        
        # 移除常見前綴（如 "v", "version"）
        normalized = re.sub(r'^v(ersion)?\s*', '', normalized, flags=re.IGNORECASE)
        
        return normalized
    
    
    def _calculate_confidence(
        self,
        is_exact_product: bool,
        version_match_type: MatchType,
        product_similarity: Optional[float] = None,
    ) -> float:
        """
        計算比對信心分數
        
        Args:
            is_exact_product: 是否為精確產品名稱匹配
            version_match_type: 版本匹配類型（已經確定是精確或模糊）
            product_similarity: 產品名稱相似度（僅用於模糊匹配）
        
        Returns:
            float: 信心分數（0.0 - 1.0）
        """
        base_confidence = 1.0 if is_exact_product else (product_similarity or 0.8)
        
        # 根據版本匹配類型調整信心分數
        version_multipliers = {
            MatchType.EXACT_PRODUCT_EXACT_VERSION: 1.0,
            MatchType.EXACT_PRODUCT_VERSION_RANGE: 0.9,
            MatchType.EXACT_PRODUCT_MAJOR_VERSION: 0.8,
            MatchType.EXACT_PRODUCT_NO_VERSION: 0.7,
            MatchType.FUZZY_PRODUCT_EXACT_VERSION: 0.9,
            MatchType.FUZZY_PRODUCT_VERSION_RANGE: 0.8,
            MatchType.FUZZY_PRODUCT_MAJOR_VERSION: 0.7,
            MatchType.FUZZY_PRODUCT_NO_VERSION: 0.6,
            MatchType.OS_MATCH: 0.9,
        }
        
        multiplier = version_multipliers.get(version_match_type, 0.5)
        
        return min(base_confidence * multiplier, 1.0)

