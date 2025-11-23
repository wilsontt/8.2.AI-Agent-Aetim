"""
威脅提取服務

提供威脅資訊提取功能，整合 AI 服務與規則基礎方法。
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass

from ...infrastructure.external_services.ai_service_client import AIServiceClient
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractedThreatInfo:
    """提取的威脅資訊"""
    
    cves: List[str]
    products: List[Dict]
    ttps: List[str]
    iocs: Dict[str, List[str]]
    confidence: float
    source: str  # "ai" 或 "rule_based"


class ThreatExtractionService:
    """
    威脅提取服務
    
    提供威脅資訊提取功能，整合 AI 服務與規則基礎方法。
    當 AI 服務不可用時，自動回退到規則基礎方法。
    """
    
    def __init__(
        self,
        ai_service_client: Optional[AIServiceClient] = None,
        use_fallback: bool = True,
    ):
        """
        初始化威脅提取服務
        
        Args:
            ai_service_client: AI 服務客戶端（可選）
            use_fallback: 是否使用回退機制（規則基礎方法）
        """
        self.ai_service_client = ai_service_client
        self.use_fallback = use_fallback
        self._ai_service_available: Optional[bool] = None
    
    async def check_ai_service_health(self) -> bool:
        """
        檢查 AI 服務健康狀態
        
        Returns:
            bool: AI 服務是否可用
        """
        if not self.ai_service_client:
            return False
        
        try:
            import httpx
            health_url = f"{self.ai_service_client.base_url}/health"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url)
                response.raise_for_status()
                self._ai_service_available = True
                return True
        except Exception as e:
            logger.warning(
                f"AI 服務健康檢查失敗：{str(e)}",
                extra={"error": str(e)}
            )
            self._ai_service_available = False
            return False
    
    async def extract_threat_info(
        self,
        text: str,
        force_fallback: bool = False,
    ) -> ExtractedThreatInfo:
        """
        提取威脅資訊
        
        Args:
            text: 要提取的文字內容
            force_fallback: 強制使用回退機制（規則基礎方法）
        
        Returns:
            ExtractedThreatInfo: 提取的威脅資訊
        """
        # 如果強制使用回退機制，或 AI 服務不可用，使用規則基礎方法
        if force_fallback or not self._should_use_ai():
            return await self._extract_with_rule_based(text)
        
        # 嘗試使用 AI 服務
        try:
            ai_result = await self.ai_service_client.extract_threat_info(text)
            
            # 轉換 AI 服務回應格式
            return ExtractedThreatInfo(
                cves=ai_result.get("cves", []),
                products=ai_result.get("products", []),
                ttps=ai_result.get("ttps", []),
                iocs=ai_result.get("iocs", {"ips": [], "domains": [], "hashes": []}),
                confidence=ai_result.get("confidence", 0.0),
                source="ai",
            )
        except Exception as e:
            logger.warning(
                f"AI 服務提取失敗，使用回退機制：{str(e)}",
                extra={"error": str(e)}
            )
            self._ai_service_available = False
            
            # 如果啟用回退機制，使用規則基礎方法
            if self.use_fallback:
                return await self._extract_with_rule_based(text)
            else:
                # 如果未啟用回退機制，返回空結果
                return ExtractedThreatInfo(
                    cves=[],
                    products=[],
                    ttps=[],
                    iocs={"ips": [], "domains": [], "hashes": []},
                    confidence=0.0,
                    source="none",
                )
    
    def _should_use_ai(self) -> bool:
        """
        判斷是否應該使用 AI 服務
        
        Returns:
            bool: 是否應該使用 AI 服務
        """
        if not self.ai_service_client:
            return False
        
        # 如果已經檢查過且不可用，直接返回 False
        if self._ai_service_available is False:
            return False
        
        # 如果尚未檢查，假設可用
        if self._ai_service_available is None:
            return True
        
        return self._ai_service_available
    
    async def _extract_with_rule_based(self, text: str) -> ExtractedThreatInfo:
        """
        使用規則基礎方法提取威脅資訊（回退機制）
        
        Args:
            text: 要提取的文字內容
        
        Returns:
            ExtractedThreatInfo: 提取的威脅資訊
        """
        logger.info("使用規則基礎方法提取威脅資訊")
        
        cves = self._extract_cves(text)
        products = self._extract_products(text)
        ttps = self._extract_ttps(text)
        iocs = self._extract_iocs(text)
        
        # 計算信心分數（規則基礎方法的信心分數較低）
        confidence = 0.5 if (cves or products or ttps or any(iocs.values())) else 0.0
        
        return ExtractedThreatInfo(
            cves=cves,
            products=products,
            ttps=ttps,
            iocs=iocs,
            confidence=confidence,
            source="rule_based",
        )
    
    def _extract_cves(self, text: str) -> List[str]:
        """
        使用正則表達式提取 CVE 編號
        
        Args:
            text: 要提取的文字內容
        
        Returns:
            List[str]: CVE 編號列表
        """
        # CVE 編號格式：CVE-YYYY-NNNNN
        pattern = r"CVE-\d{4}-\d{4,}"
        matches = re.findall(pattern, text, re.IGNORECASE)
        return list(set(matches))  # 去重
    
    def _extract_products(self, text: str) -> List[Dict]:
        """
        使用規則基礎方法提取產品資訊
        
        Args:
            text: 要提取的文字內容
        
        Returns:
            List[Dict]: 產品資訊列表
        """
        products = []
        
        # 常見產品關鍵字
        product_keywords = [
            "Windows", "Linux", "macOS", "iOS", "Android",
            "Apache", "Nginx", "IIS", "Tomcat",
            "MySQL", "PostgreSQL", "MongoDB", "Redis",
            "WordPress", "Drupal", "Joomla",
            "VMware", "VirtualBox", "Docker", "Kubernetes",
        ]
        
        for keyword in product_keywords:
            if keyword.lower() in text.lower():
                # 嘗試提取版本號
                version_pattern = rf"{re.escape(keyword)}\s+([\d.]+)"
                version_match = re.search(version_pattern, text, re.IGNORECASE)
                version = version_match.group(1) if version_match else None
                
                products.append({
                    "product_name": keyword,
                    "product_version": version,
                    "product_type": "Software",
                    "original_text": keyword + (f" {version}" if version else ""),
                })
        
        return products
    
    def _extract_ttps(self, text: str) -> List[str]:
        """
        使用規則基礎方法提取 TTPs
        
        Args:
            text: 要提取的文字內容
        
        Returns:
            List[str]: TTPs 列表
        """
        ttps = []
        
        # MITRE ATT&CK TTP 格式：T#### 或 T####.###
        pattern = r"T\d{4}(?:\.\d{3})?"
        matches = re.findall(pattern, text, re.IGNORECASE)
        ttps.extend(matches)
        
        return list(set(ttps))  # 去重
    
    def _extract_iocs(self, text: str) -> Dict[str, List[str]]:
        """
        使用規則基礎方法提取 IOCs
        
        Args:
            text: 要提取的文字內容
        
        Returns:
            Dict[str, List[str]]: IOCs 字典
        """
        iocs = {
            "ips": [],
            "domains": [],
            "hashes": [],
        }
        
        # IP 位址格式
        ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
        ip_matches = re.findall(ip_pattern, text)
        iocs["ips"] = list(set(ip_matches))  # 去重
        
        # 網域格式
        domain_pattern = r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b"
        domain_matches = re.findall(domain_pattern, text)
        iocs["domains"] = list(set(domain_matches))  # 去重
        
        # 雜湊值格式（MD5, SHA1, SHA256）
        hash_patterns = [
            r"\b[a-fA-F0-9]{32}\b",  # MD5
            r"\b[a-fA-F0-9]{40}\b",  # SHA1
            r"\b[a-fA-F0-9]{64}\b",  # SHA256
        ]
        for pattern in hash_patterns:
            hash_matches = re.findall(pattern, text)
            iocs["hashes"].extend(hash_matches)
        iocs["hashes"] = list(set(iocs["hashes"]))  # 去重
        
        return iocs

