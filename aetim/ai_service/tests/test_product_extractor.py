"""
產品名稱與版本提取器單元測試

測試 ProductExtractor 的各種功能，包括：
- 關鍵字匹配
- 版本號提取
- 信心分數計算
- 邊界情況處理
"""

import pytest
from app.processors.product_extractor import ProductExtractor


class TestProductExtractor:
    """產品名稱與版本提取器測試"""
    
    @pytest.fixture
    def extractor(self):
        """建立 ProductExtractor 實例（不載入 spaCy 模型以加快測試）"""
        return ProductExtractor(nlp=None)
    
    # ========== extract 方法測試 ==========
    
    def test_extract_keyword_match_with_version(self, extractor):
        """測試關鍵字匹配（含版本號）"""
        text = "VMware ESXi 7.0.3 is affected by this vulnerability"
        result = extractor.extract(text)
        
        assert len(result) > 0
        vmware_product = next((p for p in result if p["name"] == "VMware"), None)
        assert vmware_product is not None
        assert vmware_product["version"] == "7.0.3"
        assert vmware_product["confidence"] == 0.8
    
    def test_extract_keyword_match_without_version(self, extractor):
        """測試關鍵字匹配（無版本號）"""
        text = "VMware is mentioned in this security advisory"
        result = extractor.extract(text)
        
        assert len(result) > 0
        vmware_product = next((p for p in result if p["name"] == "VMware"), None)
        assert vmware_product is not None
        assert vmware_product["version"] is None
        assert vmware_product["confidence"] == 0.8
    
    def test_extract_multiple_products(self, extractor):
        """測試提取多個產品"""
        text = "VMware ESXi 7.0.3 and Windows Server 2022 are both affected"
        result = extractor.extract(text)
        
        assert len(result) >= 2
        product_names = [p["name"] for p in result]
        assert "VMware" in product_names
        assert "Windows Server" in product_names
    
    def test_extract_case_insensitive(self, extractor):
        """測試大小寫不敏感匹配"""
        text = "vmware esxi 7.0.3 is affected"
        result = extractor.extract(text)
        
        assert len(result) > 0
        vmware_product = next((p for p in result if p["name"] == "VMware"), None)
        assert vmware_product is not None
    
    def test_extract_no_products(self, extractor):
        """測試文字中沒有產品時返回空列表"""
        text = "This is a general security notice with no specific products"
        result = extractor.extract(text)
        
        assert result == []
    
    def test_extract_empty_string(self, extractor):
        """測試空字串"""
        result = extractor.extract("")
        assert result == []
    
    def test_extract_none_input(self, extractor):
        """測試 None 輸入"""
        result = extractor.extract(None)
        assert result == []
    
    def test_extract_non_string_input(self, extractor):
        """測試非字串輸入"""
        result = extractor.extract(12345)
        assert result == []
    
    # ========== _extract_version 方法測試 ==========
    
    def test_extract_version_standard_format(self, extractor):
        """測試標準版本格式提取"""
        test_cases = [
            ("VMware ESXi 7.0.3", "VMware", "7.0.3"),
            ("Windows Server 2022", "Windows Server", "2022"),
            ("Apache 2.4.41", "Apache", "2.4.41"),
            ("MySQL 8.0.21", "MySQL", "8.0.21"),
        ]
        
        for text, product, expected_version in test_cases:
            version = extractor._extract_version(text, product)
            assert version == expected_version, f"Failed for {text}"
    
    def test_extract_version_with_v_prefix(self, extractor):
        """測試帶 v 前綴的版本號"""
        test_cases = [
            ("VMware v7.0.3", "VMware", "7.0.3"),
            ("Apache v2.4", "Apache", "2.4"),
            ("MySQL v8.0", "MySQL", "8.0"),
        ]
        
        for text, product, expected_version in test_cases:
            version = extractor._extract_version(text, product)
            assert version == expected_version, f"Failed for {text}"
    
    def test_extract_version_simple_format(self, extractor):
        """測試簡單版本格式"""
        test_cases = [
            ("VMware 7", "VMware", "7"),
            ("Apache 2", "Apache", "2"),
            ("MySQL 8", "MySQL", "8"),
        ]
        
        for text, product, expected_version in test_cases:
            version = extractor._extract_version(text, product)
            assert version == expected_version, f"Failed for {text}"
    
    def test_extract_version_year_format(self, extractor):
        """測試年份格式版本號"""
        test_cases = [
            ("Windows Server 2022", "Windows Server", "2022"),
            ("Windows Server 2019", "Windows Server", "2019"),
            ("SQL Server 2016", "SQL Server", "2016"),
        ]
        
        for text, product, expected_version in test_cases:
            version = extractor._extract_version(text, product)
            assert version == expected_version, f"Failed for {text}"
    
    def test_extract_version_not_found(self, extractor):
        """測試未找到版本號"""
        text = "VMware is mentioned but no version specified"
        version = extractor._extract_version(text, "VMware")
        
        assert version is None
    
    def test_extract_version_empty_input(self, extractor):
        """測試空輸入"""
        version = extractor._extract_version("", "VMware")
        assert version is None
        
        version = extractor._extract_version("VMware 7.0.3", "")
        assert version is None
    
    # ========== _is_valid_version 方法測試 ==========
    
    def test_is_valid_version_valid_formats(self, extractor):
        """測試有效的版本號格式"""
        valid_versions = [
            "1.0",
            "1.0.3",
            "7.0.3",
            "2.4.41",
            "8.0.21",
            "2022",
            "2019",
            "1",
            "7",
        ]
        
        for version in valid_versions:
            assert extractor._is_valid_version(version), f"Should be valid: {version}"
    
    def test_is_valid_version_invalid_formats(self, extractor):
        """測試無效的版本號格式"""
        invalid_versions = [
            "v1.0",  # 包含字母
            "1.0.3.4.5",  # 過多點號
            "abc",  # 非數字
            "",  # 空字串
            None,  # None
            "1.0.3-beta",  # 包含特殊字元
        ]
        
        for version in invalid_versions:
            assert not extractor._is_valid_version(version), f"Should be invalid: {version}"
    
    # ========== _is_likely_product 方法測試 ==========
    
    def test_is_likely_product_known_keywords(self, extractor):
        """測試已知產品關鍵字"""
        known_products = [
            "VMware",
            "Windows Server",
            "Apache",
            "MySQL",
        ]
        
        for product in known_products:
            assert extractor._is_likely_product(product), f"Should be product: {product}"
    
    def test_is_likely_product_with_indicators(self, extractor):
        """測試包含產品特徵的文字"""
        products_with_indicators = [
            "Web Server",
            "Database System",
            "Application Framework",
            "Cloud Platform",
        ]
        
        for product in products_with_indicators:
            assert extractor._is_likely_product(product), f"Should be product: {product}"
    
    def test_is_likely_product_not_product(self, extractor):
        """測試非產品文字"""
        not_products = [
            "vulnerability",
            "security",
            "attack",
            "",
            None,
        ]
        
        for text in not_products:
            if text:  # 跳過空字串和 None（這些會在其他測試中處理）
                assert not extractor._is_likely_product(text), f"Should not be product: {text}"
    
    # ========== 真實場景測試 ==========
    
    def test_extract_from_security_advisory(self, extractor):
        """測試從安全通報中提取產品"""
        text = """
        VMware has released a security advisory for VMware ESXi 7.0.3.
        This vulnerability affects VMware ESXi versions 7.0.3 and earlier.
        """
        result = extractor.extract(text)
        
        assert len(result) > 0
        vmware_products = [p for p in result if p["name"] == "VMware"]
        assert len(vmware_products) > 0
        assert any(p["version"] == "7.0.3" for p in vmware_products)
    
    def test_extract_from_multiple_advisories(self, extractor):
        """測試從多個安全通報中提取產品"""
        text = """
        Multiple vulnerabilities have been discovered:
        - Windows Server 2022 is affected
        - SQL Server 2019 is affected
        - Apache 2.4.41 is affected
        """
        result = extractor.extract(text)
        
        assert len(result) >= 3
        product_names = [p["name"] for p in result]
        assert "Windows Server" in product_names
        assert "SQL Server" in product_names
        assert "Apache" in product_names
    
    def test_extract_duplicate_products(self, extractor):
        """測試重複產品去重"""
        text = "VMware ESXi 7.0.3 is mentioned. VMware ESXi 7.0.3 is affected."
        result = extractor.extract(text)
        
        # 應去重，只返回一個產品
        vmware_products = [p for p in result if p["name"] == "VMware" and p["version"] == "7.0.3"]
        assert len(vmware_products) <= 1
    
    def test_extract_confidence_scores(self, extractor):
        """測試信心分數"""
        text = "VMware ESXi 7.0.3 is affected"
        result = extractor.extract(text)
        
        assert len(result) > 0
        # 關鍵字匹配的信心分數應為 0.8
        vmware_product = next((p for p in result if p["name"] == "VMware"), None)
        assert vmware_product is not None
        assert vmware_product["confidence"] == 0.8

