"""
產品名稱比對器

實作產品名稱的精確與模糊比對邏輯（Domain Service）。
"""

from typing import Optional, Dict
from dataclasses import dataclass
import re
from difflib import SequenceMatcher

from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProductMatchResult:
    """
    產品名稱比對結果
    
    表示產品名稱比對的結果。
    """
    
    is_match: bool
    is_exact: bool  # 是否為精確匹配
    similarity: float  # 相似度（0.0 - 1.0）
    normalized_name1: str  # 標準化後的產品名稱 1
    normalized_name2: str  # 標準化後的產品名稱 2
    
    def __str__(self) -> str:
        return (
            f"ProductMatchResult(is_match={self.is_match}, "
            f"is_exact={self.is_exact}, "
            f"similarity={self.similarity:.2f})"
        )


class ProductNameMatcher:
    """
    產品名稱比對器（Domain Service）
    
    負責產品名稱的精確與模糊比對（AC-010-1, AC-010-2）。
    """
    
    # 產品名稱相似度閾值（≥ 0.8 視為匹配）
    SIMILARITY_THRESHOLD = 0.8
    
    # 產品名稱標準化映射（處理常見變體）
    PRODUCT_NAME_NORMALIZATIONS = {
        "ms sql": "microsoft sql server",
        "mssql": "microsoft sql server",
        "sql server": "microsoft sql server",
        "win server": "windows server",
        "win": "windows",
        "vmware esxi": "vmware esxi",
        "esxi": "vmware esxi",
        "iis": "internet information services",
        "apache httpd": "apache http server",
        "apache http server": "apache http server",
        "nginx": "nginx",
        "tomcat": "apache tomcat",
        "apache tomcat": "apache tomcat",
        "mysql": "mysql",
        "postgresql": "postgresql",
        "postgres": "postgresql",
        "oracle database": "oracle database",
        "oracle db": "oracle database",
        "mssql server": "microsoft sql server",
    }
    
    def exact_match(
        self,
        name1: str,
        name2: str,
    ) -> ProductMatchResult:
        """
        精確匹配（AC-010-1）
        
        完全相同的產品名稱（大小寫不敏感），經過標準化處理。
        
        Args:
            name1: 產品名稱 1
            name2: 產品名稱 2
        
        Returns:
            ProductMatchResult: 比對結果
        """
        normalized1 = self.normalize_product_name(name1)
        normalized2 = self.normalize_product_name(name2)
        
        is_match = normalized1 == normalized2
        
        logger.debug(
            f"精確匹配：{name1} vs {name2}",
            extra={
                "name1": name1,
                "name2": name2,
                "normalized1": normalized1,
                "normalized2": normalized2,
                "is_match": is_match,
            }
        )
        
        return ProductMatchResult(
            is_match=is_match,
            is_exact=True,
            similarity=1.0 if is_match else 0.0,
            normalized_name1=normalized1,
            normalized_name2=normalized2,
        )
    
    def fuzzy_match(
        self,
        name1: str,
        name2: str,
        similarity_threshold: Optional[float] = None,
    ) -> ProductMatchResult:
        """
        模糊匹配（AC-010-2）
        
        產品名稱變體處理，使用字串相似度演算法。
        支援的變體範例：
        - "SQL Server" vs "Microsoft SQL Server"
        - "Windows Server" vs "Windows Server 2016"
        - "VMware ESXi" vs "VMware ESXi 7.0"
        
        Args:
            name1: 產品名稱 1
            name2: 產品名稱 2
            similarity_threshold: 相似度閾值（預設使用類別常數）
        
        Returns:
            ProductMatchResult: 比對結果
        """
        normalized1 = self.normalize_product_name(name1)
        normalized2 = self.normalize_product_name(name2)
        
        # 先嘗試精確匹配
        if normalized1 == normalized2:
            return ProductMatchResult(
                is_match=True,
                is_exact=True,
                similarity=1.0,
                normalized_name1=normalized1,
                normalized_name2=normalized2,
            )
        
        # 計算相似度
        similarity = self._calculate_similarity(normalized1, normalized2)
        
        # 使用提供的閾值或預設閾值
        threshold = similarity_threshold or self.SIMILARITY_THRESHOLD
        is_match = similarity >= threshold
        
        logger.debug(
            f"模糊匹配：{name1} vs {name2}",
            extra={
                "name1": name1,
                "name2": name2,
                "normalized1": normalized1,
                "normalized2": normalized2,
                "similarity": similarity,
                "threshold": threshold,
                "is_match": is_match,
            }
        )
        
        return ProductMatchResult(
            is_match=is_match,
            is_exact=False,
            similarity=similarity,
            normalized_name1=normalized1,
            normalized_name2=normalized2,
        )
    
    def normalize_product_name(self, product_name: str) -> str:
        """
        標準化產品名稱（AC-010-2）
        
        處理：
        - 移除版本號
        - 移除特殊字元
        - 統一大小寫
        - 處理常見變體（如 "MS SQL" → "Microsoft SQL Server"）
        
        Args:
            product_name: 產品名稱
        
        Returns:
            str: 標準化後的產品名稱
        """
        if not product_name:
            return ""
        
        # 轉為小寫
        normalized = product_name.lower().strip()
        
        # 移除版本號（如 "Windows Server 2019" -> "Windows Server"）
        # 匹配常見版本格式：年份（如 2019, 2020）、版本號（如 7.0, 10.0）
        normalized = re.sub(r'\s+\d{4}$', '', normalized)  # 移除年份
        normalized = re.sub(r'\s+\d+\.\d+.*$', '', normalized)  # 移除版本號（如 "7.0", "10.0"）
        normalized = re.sub(r'\s+v\d+.*$', '', normalized)  # 移除版本號（如 "v7.0", "v10.0"）
        normalized = re.sub(r'\s+version\s+\d+.*$', '', normalized, flags=re.IGNORECASE)  # 移除 "version X"
        
        # 處理常見變體
        for variant, standard in self.PRODUCT_NAME_NORMALIZATIONS.items():
            if variant in normalized:
                normalized = normalized.replace(variant, standard)
        
        # 移除特殊字元（保留空格）
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # 移除多餘空格
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _calculate_similarity(
        self,
        name1: str,
        name2: str,
    ) -> float:
        """
        計算產品名稱相似度（使用 SequenceMatcher）
        
        使用 Python 的 difflib.SequenceMatcher 計算字串相似度。
        這是一個基於最長公共子序列的演算法，類似於 Levenshtein 距離。
        
        Args:
            name1: 標準化後的產品名稱 1
            name2: 標準化後的產品名稱 2
        
        Returns:
            float: 相似度（0.0 - 1.0）
        """
        return SequenceMatcher(None, name1, name2).ratio()
    
    def match(
        self,
        name1: str,
        name2: str,
        allow_fuzzy: bool = True,
    ) -> ProductMatchResult:
        """
        比對產品名稱（精確或模糊）
        
        先嘗試精確匹配，如果失敗且允許模糊匹配，則嘗試模糊匹配。
        
        Args:
            name1: 產品名稱 1
            name2: 產品名稱 2
            allow_fuzzy: 是否允許模糊匹配（預設 True）
        
        Returns:
            ProductMatchResult: 比對結果
        """
        # 先嘗試精確匹配
        exact_result = self.exact_match(name1, name2)
        if exact_result.is_match:
            return exact_result
        
        # 如果精確匹配失敗且允許模糊匹配，嘗試模糊匹配
        if allow_fuzzy:
            return self.fuzzy_match(name1, name2)
        
        # 不允許模糊匹配，返回失敗結果
        return exact_result

