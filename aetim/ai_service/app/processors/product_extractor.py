"""
產品名稱與版本提取器

從文字內容中提取產品名稱與版本資訊。
符合 AC-009-2 要求：識別產品名稱與版本資訊。
"""

import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass

try:
    import spacy
    from spacy.language import Language
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    Language = None


@dataclass
class ProductInfo:
    """產品資訊"""
    name: str
    version: Optional[str] = None
    confidence: float = 0.0


class ProductExtractor:
    """
    產品名稱與版本提取器
    
    使用關鍵字匹配和 spaCy NER 從文字中提取產品名稱與版本資訊。
    """
    
    # 常見產品關鍵字列表
    PRODUCT_KEYWORDS = [
        "Windows Server",
        "VMware",
        "SQL Server",
        "Apache",
        "MySQL",
        "Delphi",
        "EEP",
        "Ruby On Rails",
        "Windows",
        "Linux",
        "Ubuntu",
        "CentOS",
        "Red Hat",
        "Oracle",
        "PostgreSQL",
        "MongoDB",
        "Redis",
        "Nginx",
        "IIS",
        "Tomcat",
        "Java",
        "Python",
        "Node.js",
        "PHP",
        "Ruby",
        "Docker",
        "Kubernetes",
        "ESXi",
        "vSphere",
        "Hyper-V",
    ]
    
    # 信心分數設定
    KEYWORD_MATCH_CONFIDENCE = 0.8
    NER_MATCH_CONFIDENCE = 0.7
    
    def __init__(self, nlp: Optional[Language] = None):
        """
        初始化產品提取器
        
        Args:
            nlp: spaCy Language 物件（可選，如果未提供則嘗試載入）
        """
        self.nlp = nlp
        if nlp is None and SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("zh_core_web_sm")
            except OSError:
                # 如果中文模型不存在，嘗試載入英文模型
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                except OSError:
                    print("⚠️  spaCy 模型未載入，將僅使用關鍵字匹配")
                    self.nlp = None
    
    def extract(self, text: str) -> List[Dict[str, any]]:
        """
        提取產品名稱與版本
        
        使用關鍵字匹配和 spaCy NER 從文字中提取產品名稱與版本資訊。
        
        Args:
            text: 要提取的文字內容
        
        Returns:
            List[Dict]: 產品資訊列表，每個包含 name、version、confidence
        
        Examples:
            >>> extractor = ProductExtractor()
            >>> extractor.extract("VMware ESXi 7.0.3 is affected")
            [{'name': 'VMware', 'version': '7.0.3', 'confidence': 0.8}]
        """
        if not text or not isinstance(text, str):
            return []
        
        products: List[ProductInfo] = []
        seen_products: Set[str] = set()  # 用於去重
        
        # 1. 使用關鍵字匹配
        for keyword in self.PRODUCT_KEYWORDS:
            if self._contains_keyword(text, keyword):
                version = self._extract_version(text, keyword)
                product_key = f"{keyword.lower()}:{version or ''}"
                
                if product_key not in seen_products:
                    products.append(ProductInfo(
                        name=keyword,
                        version=version,
                        confidence=self.KEYWORD_MATCH_CONFIDENCE,
                    ))
                    seen_products.add(product_key)
        
        # 2. 使用 spaCy NER（如果可用）
        if self.nlp is not None:
            try:
                doc = self.nlp(text)
                for ent in doc.ents:
                    # 檢查是否為產品實體
                    if ent.label_ == "PRODUCT" or self._is_likely_product(ent.text):
                        # 避免與關鍵字匹配重複
                        if not any(p.name.lower() == ent.text.lower() for p in products):
                            version = self._extract_version(text, ent.text)
                            product_key = f"{ent.text.lower()}:{version or ''}"
                            
                            if product_key not in seen_products:
                                products.append(ProductInfo(
                                    name=ent.text,
                                    version=version,
                                    confidence=self.NER_MATCH_CONFIDENCE,
                                ))
                                seen_products.add(product_key)
            except Exception as e:
                # 如果 NER 處理失敗，僅記錄錯誤但不中斷
                print(f"⚠️  spaCy NER 處理失敗: {e}")
        
        # 轉換為字典格式
        return [
            {
                "name": p.name,
                "version": p.version,
                "confidence": p.confidence,
            }
            for p in products
        ]
    
    def _contains_keyword(self, text: str, keyword: str) -> bool:
        """
        檢查文字是否包含關鍵字（不區分大小寫）
        
        Args:
            text: 文字內容
            keyword: 關鍵字
        
        Returns:
            bool: 如果包含關鍵字則返回 True
        """
        return keyword.lower() in text.lower()
    
    def _extract_version(self, text: str, product_name: str) -> Optional[str]:
        """
        提取版本號
        
        從文字中提取與產品名稱相關的版本號。
        支援多種版本格式：v1.0、1.0、7.0.3、2024 等。
        
        Args:
            text: 文字內容
            product_name: 產品名稱
        
        Returns:
            Optional[str]: 版本號，如果未找到則返回 None
        
        Examples:
            >>> extractor = ProductExtractor()
            >>> extractor._extract_version("VMware ESXi 7.0.3", "VMware")
            '7.0.3'
            >>> extractor._extract_version("Windows Server 2022", "Windows Server")
            '2022'
        """
        if not text or not product_name:
            return None
        
        # 版本號模式列表（按優先順序）
        version_patterns = [
            # 格式：產品名稱 v1.0.3 或 產品名稱 1.0.3
            rf'{re.escape(product_name)}\s+[vV]?(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)',
            # 格式：產品名稱 v1.0 或 產品名稱 1.0
            rf'{re.escape(product_name)}\s+[vV]?(\d+\.\d+)',
            # 格式：產品名稱 v1 或 產品名稱 1
            rf'{re.escape(product_name)}\s+[vV]?(\d+)',
            # 格式：產品名稱 2024（年份格式）
            rf'{re.escape(product_name)}\s+(\d{{4}})',
            # 格式：產品名稱後的版本號（更寬鬆的匹配）
            rf'{re.escape(product_name)}[^\w]*(\d+\.\d+(?:\.\d+)?)',
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                version = match.group(1)
                # 驗證版本號格式（避免誤判）
                if self._is_valid_version(version):
                    return version
        
        return None
    
    def _is_valid_version(self, version: str) -> bool:
        """
        驗證版本號格式是否有效
        
        Args:
            version: 版本號字串
        
        Returns:
            bool: 如果格式有效則返回 True
        """
        if not version:
            return False
        
        # 檢查是否為有效的版本號格式
        # 允許：數字、點號、年份格式（4位數）
        version_pattern = r'^(\d+\.\d+(?:\.\d+)?(?:\.\d+)?|\d{4}|\d+)$'
        return bool(re.match(version_pattern, version))
    
    def _is_likely_product(self, text: str) -> bool:
        """
        判斷文字是否可能是產品名稱
        
        Args:
            text: 文字內容
        
        Returns:
            bool: 如果可能是產品名稱則返回 True
        """
        if not text:
            return False
        
        # 檢查是否包含常見的產品關鍵字
        text_lower = text.lower()
        for keyword in self.PRODUCT_KEYWORDS:
            if keyword.lower() in text_lower or text_lower in keyword.lower():
                return True
        
        # 檢查是否包含常見的產品特徵（如 "Server"、"Database" 等）
        product_indicators = [
            "server", "database", "system", "platform", "framework",
            "software", "application", "service", "engine",
        ]
        
        return any(indicator in text_lower for indicator in product_indicators)

