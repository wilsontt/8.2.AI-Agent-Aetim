"""
整合提取服務

整合所有提取器（CVE、產品、TTP、IOC），提供統一的威脅資訊提取介面。
符合 AC-009-1 至 AC-009-5 要求。
"""

from typing import Dict, List, Optional, Any
from app.processors.cve_extractor import CVEExtractor
from app.processors.product_extractor import ProductExtractor
from app.processors.ttp_extractor import TTPExtractor
from app.processors.ioc_extractor import IOCExtractor
import logging

logger = logging.getLogger(__name__)


class ExtractionService:
    """
    整合提取服務
    
    整合所有提取器，提供統一的威脅資訊提取介面。
    計算整體信心分數。
    """
    
    # 信心分數權重
    CVE_WEIGHT = 0.3
    PRODUCTS_WEIGHT = 0.3
    TTPS_WEIGHT = 0.2
    IOCS_WEIGHT = 0.2
    
    def __init__(
        self,
        cve_extractor: Optional[CVEExtractor] = None,
        product_extractor: Optional[ProductExtractor] = None,
        ttp_extractor: Optional[TTPExtractor] = None,
        ioc_extractor: Optional[IOCExtractor] = None,
    ):
        """
        初始化整合提取服務
        
        Args:
            cve_extractor: CVE 提取器（可選，如果未提供則建立新實例）
            product_extractor: 產品提取器（可選，如果未提供則建立新實例）
            ttp_extractor: TTP 提取器（可選，如果未提供則建立新實例）
            ioc_extractor: IOC 提取器（可選，如果未提供則建立新實例）
        """
        self.cve_extractor = cve_extractor or CVEExtractor()
        self.product_extractor = product_extractor or ProductExtractor()
        self.ttp_extractor = ttp_extractor or TTPExtractor()
        self.ioc_extractor = ioc_extractor or IOCExtractor()
    
    def extract(self, text: str) -> Dict[str, Any]:
        """
        提取所有威脅資訊
        
        整合所有提取器，從文字中提取 CVE、產品、TTPs、IOCs 等威脅資訊。
        計算整體信心分數。
        
        Args:
            text: 要提取的文字內容
        
        Returns:
            Dict[str, Any]: 提取結果，包含：
                - cve: List[str] - CVE 編號列表
                - products: List[Dict] - 產品資訊列表
                - ttps: List[str] - TTP ID 列表
                - iocs: Dict[str, List[str]] - IOC 字典（ips、domains、hashes）
                - confidence: float - 整體信心分數（0.0-1.0）
        
        Examples:
            >>> service = ExtractionService()
            >>> result = service.extract("CVE-2024-12345 affects VMware ESXi 7.0.3")
            >>> result["cve"]
            ['CVE-2024-12345']
            >>> result["products"]
            [{'name': 'VMware', 'version': '7.0.3', 'confidence': 0.8}]
        """
        if not text or not isinstance(text, str):
            return self._empty_result()
        
        result = {
            "cve": [],
            "products": [],
            "ttps": [],
            "iocs": {"ips": [], "domains": [], "hashes": []},
            "confidence": 0.0,
        }
        
        # 1. 提取 CVE 編號
        try:
            cve_list = self.cve_extractor.extract_all(text)
            result["cve"] = cve_list
        except Exception as e:
            logger.error(f"CVE 提取失敗: {e}", exc_info=True)
            result["cve"] = []
        
        # 2. 提取產品名稱與版本
        try:
            products = self.product_extractor.extract(text)
            result["products"] = products
        except Exception as e:
            logger.error(f"產品提取失敗: {e}", exc_info=True)
            result["products"] = []
        
        # 3. 提取 TTPs
        try:
            ttps = self.ttp_extractor.extract(text)
            result["ttps"] = ttps
        except Exception as e:
            logger.error(f"TTP 提取失敗: {e}", exc_info=True)
            result["ttps"] = []
        
        # 4. 提取 IOCs
        try:
            iocs = self.ioc_extractor.extract(text)
            result["iocs"] = iocs
        except Exception as e:
            logger.error(f"IOC 提取失敗: {e}", exc_info=True)
            result["iocs"] = {"ips": [], "domains": [], "hashes": []}
        
        # 5. 計算整體信心分數
        result["confidence"] = self._calculate_confidence(
            result["cve"],
            result["products"],
            result["ttps"],
            result["iocs"],
        )
        
        return result
    
    def _calculate_confidence(
        self,
        cve: List[str],
        products: List[Dict],
        ttps: List[str],
        iocs: Dict[str, List[str]],
    ) -> float:
        """
        計算整體信心分數
        
        根據提取結果計算整體信心分數：
        - CVE：0.3（如果有 CVE）
        - Products：0.3（如果有產品）
        - TTPs：0.2（如果有 TTP）
        - IOCs：0.2（如果有 IOC）
        
        Args:
            cve: CVE 編號列表
            products: 產品資訊列表
            ttps: TTP ID 列表
            iocs: IOC 字典
        
        Returns:
            float: 整體信心分數（0.0-1.0）
        """
        score = 0.0
        
        # CVE 權重：0.3
        if cve and len(cve) > 0:
            score += self.CVE_WEIGHT
        
        # Products 權重：0.3
        if products and len(products) > 0:
            score += self.PRODUCTS_WEIGHT
        
        # TTPs 權重：0.2
        if ttps and len(ttps) > 0:
            score += self.TTPS_WEIGHT
        
        # IOCs 權重：0.2
        if iocs:
            has_ioc = False
            if iocs.get("ips") and len(iocs["ips"]) > 0:
                has_ioc = True
            if iocs.get("domains") and len(iocs["domains"]) > 0:
                has_ioc = True
            if iocs.get("hashes") and len(iocs["hashes"]) > 0:
                has_ioc = True
            
            if has_ioc:
                score += self.IOCS_WEIGHT
        
        # 確保分數在 0.0-1.0 範圍內
        return min(max(score, 0.0), 1.0)
    
    def _empty_result(self) -> Dict[str, Any]:
        """
        返回空的提取結果
        
        Returns:
            Dict[str, Any]: 空的提取結果
        """
        return {
            "cve": [],
            "products": [],
            "ttps": [],
            "iocs": {"ips": [], "domains": [], "hashes": []},
            "confidence": 0.0,
        }

