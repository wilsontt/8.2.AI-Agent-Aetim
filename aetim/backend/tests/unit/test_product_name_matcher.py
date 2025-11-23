"""
產品名稱比對器單元測試

測試產品名稱比對邏輯的精確匹配、模糊匹配和標準化功能。
"""

import pytest

from analysis_assessment.domain.domain_services.product_name_matcher import (
    ProductNameMatcher,
    ProductMatchResult,
)


class TestProductNameMatcher:
    """產品名稱比對器測試"""
    
    @pytest.fixture
    def matcher(self):
        """建立產品名稱比對器實例"""
        return ProductNameMatcher()
    
    def test_exact_match_same_name(self, matcher):
        """測試精確匹配：相同名稱"""
        result = matcher.exact_match("Microsoft SQL Server", "Microsoft SQL Server")
        
        assert result.is_match is True
        assert result.is_exact is True
        assert result.similarity == 1.0
    
    def test_exact_match_case_insensitive(self, matcher):
        """測試精確匹配：大小寫不敏感"""
        result = matcher.exact_match("Microsoft SQL Server", "MICROSOFT SQL SERVER")
        
        assert result.is_match is True
        assert result.is_exact is True
        assert result.similarity == 1.0
    
    def test_exact_match_different_name(self, matcher):
        """測試精確匹配：不同名稱"""
        result = matcher.exact_match("Microsoft SQL Server", "MySQL")
        
        assert result.is_match is False
        assert result.is_exact is True
        assert result.similarity == 0.0
    
    def test_exact_match_with_version(self, matcher):
        """測試精確匹配：包含版本號（應該標準化後匹配）"""
        result = matcher.exact_match("Microsoft SQL Server 2019", "Microsoft SQL Server")
        
        assert result.is_match is True
        assert result.is_exact is True
    
    def test_fuzzy_match_similar_names(self, matcher):
        """測試模糊匹配：相似名稱"""
        result = matcher.fuzzy_match("SQL Server", "Microsoft SQL Server")
        
        assert result.is_match is True
        assert result.is_exact is False
        assert result.similarity >= 0.8
    
    def test_fuzzy_match_windows_server_variants(self, matcher):
        """測試模糊匹配：Windows Server 變體"""
        test_cases = [
            ("Windows Server", "Windows Server 2016"),
            ("Windows Server 2019", "Windows Server 2022"),
            ("Win Server", "Windows Server"),
        ]
        
        for name1, name2 in test_cases:
            result = matcher.fuzzy_match(name1, name2)
            assert result.is_match is True, f"Failed for {name1} vs {name2}"
            assert result.similarity >= 0.8
    
    def test_fuzzy_match_vmware_esxi_variants(self, matcher):
        """測試模糊匹配：VMware ESXi 變體"""
        result = matcher.fuzzy_match("VMware ESXi", "VMware ESXi 7.0")
        
        assert result.is_match is True
        assert result.similarity >= 0.8
    
    def test_fuzzy_match_different_products(self, matcher):
        """測試模糊匹配：不同產品（不應該匹配）"""
        result = matcher.fuzzy_match("Microsoft SQL Server", "MySQL")
        
        assert result.is_match is False
        assert result.similarity < 0.8
    
    def test_fuzzy_match_custom_threshold(self, matcher):
        """測試模糊匹配：自訂相似度閾值"""
        # 使用較低的閾值
        result = matcher.fuzzy_match("SQL", "SQL Server", similarity_threshold=0.5)
        
        assert result.is_match is True
        assert result.similarity >= 0.5
    
    def test_normalize_product_name_remove_version(self, matcher):
        """測試產品名稱標準化：移除版本號"""
        test_cases = [
            ("Windows Server 2019", "windows server"),
            ("Microsoft SQL Server 2019", "microsoft sql server"),
            ("VMware ESXi 7.0", "vmware esxi"),
            ("Apache Tomcat 9.0", "apache tomcat"),
        ]
        
        for input_name, expected_normalized in test_cases:
            normalized = matcher.normalize_product_name(input_name)
            assert normalized == expected_normalized, f"Failed for {input_name}"
    
    def test_normalize_product_name_remove_special_chars(self, matcher):
        """測試產品名稱標準化：移除特殊字元"""
        test_cases = [
            ("Microsoft SQL Server!", "microsoft sql server"),
            ("Windows Server (2019)", "windows server"),
            ("VMware ESXi - 7.0", "vmware esxi"),
        ]
        
        for input_name, expected_normalized in test_cases:
            normalized = matcher.normalize_product_name(input_name)
            assert normalized == expected_normalized, f"Failed for {input_name}"
    
    def test_normalize_product_name_common_variants(self, matcher):
        """測試產品名稱標準化：處理常見變體"""
        test_cases = [
            ("MS SQL Server", "microsoft sql server"),
            ("MSSQL", "microsoft sql server"),
            ("SQL Server", "microsoft sql server"),
            ("Win Server", "windows server"),
            ("Win", "windows"),
            ("ESXi", "vmware esxi"),
            ("PostgreSQL", "postgresql"),
            ("Postgres", "postgresql"),
        ]
        
        for input_name, expected_normalized in test_cases:
            normalized = matcher.normalize_product_name(input_name)
            assert normalized == expected_normalized, f"Failed for {input_name}"
    
    def test_normalize_product_name_empty(self, matcher):
        """測試產品名稱標準化：空字串"""
        normalized = matcher.normalize_product_name("")
        assert normalized == ""
    
    def test_normalize_product_name_whitespace(self, matcher):
        """測試產品名稱標準化：處理空格"""
        normalized = matcher.normalize_product_name("  Microsoft   SQL   Server  ")
        assert normalized == "microsoft sql server"
    
    def test_match_exact_first(self, matcher):
        """測試 match 方法：優先精確匹配"""
        result = matcher.match("Microsoft SQL Server", "Microsoft SQL Server")
        
        assert result.is_match is True
        assert result.is_exact is True
    
    def test_match_fuzzy_fallback(self, matcher):
        """測試 match 方法：精確匹配失敗時使用模糊匹配"""
        result = matcher.match("SQL Server", "Microsoft SQL Server", allow_fuzzy=True)
        
        assert result.is_match is True
        assert result.is_exact is False
    
    def test_match_no_fuzzy(self, matcher):
        """測試 match 方法：不允許模糊匹配"""
        result = matcher.match("SQL Server", "Microsoft SQL Server", allow_fuzzy=False)
        
        assert result.is_match is False
    
    def test_similarity_calculation(self, matcher):
        """測試相似度計算"""
        # 完全相同的字串
        similarity1 = matcher._calculate_similarity("microsoft sql server", "microsoft sql server")
        assert similarity1 == 1.0
        
        # 相似的字串
        similarity2 = matcher._calculate_similarity("sql server", "microsoft sql server")
        assert 0.5 <= similarity2 <= 1.0
        
        # 不同的字串
        similarity3 = matcher._calculate_similarity("microsoft sql server", "mysql")
        assert similarity3 < 0.5
    
    def test_product_name_variants_comprehensive(self, matcher):
        """測試產品名稱變體的綜合測試"""
        # 測試各種 SQL Server 變體
        sql_server_variants = [
            "Microsoft SQL Server",
            "MS SQL Server",
            "MSSQL",
            "SQL Server",
            "SQL Server 2019",
            "Microsoft SQL Server 2019",
        ]
        
        for variant1 in sql_server_variants:
            for variant2 in sql_server_variants:
                result = matcher.match(variant1, variant2, allow_fuzzy=True)
                assert result.is_match is True, (
                    f"Failed: {variant1} should match {variant2}"
                )
    
    def test_windows_server_variants_comprehensive(self, matcher):
        """測試 Windows Server 變體的綜合測試"""
        windows_server_variants = [
            "Windows Server",
            "Windows Server 2016",
            "Windows Server 2019",
            "Windows Server 2022",
            "Win Server",
            "Win Server 2019",
        ]
        
        for variant1 in windows_server_variants:
            for variant2 in windows_server_variants:
                result = matcher.match(variant1, variant2, allow_fuzzy=True)
                assert result.is_match is True, (
                    f"Failed: {variant1} should match {variant2}"
                )
    
    def test_accuracy_requirement(self, matcher):
        """測試比對準確度要求（≥ 90%）"""
        # 測試案例：應該匹配的產品名稱對
        should_match_pairs = [
            ("SQL Server", "Microsoft SQL Server"),
            ("Windows Server 2019", "Windows Server 2022"),
            ("VMware ESXi 7.0", "VMware ESXi"),
            ("MS SQL", "Microsoft SQL Server"),
            ("Postgres", "PostgreSQL"),
        ]
        
        match_count = 0
        for name1, name2 in should_match_pairs:
            result = matcher.match(name1, name2, allow_fuzzy=True)
            if result.is_match:
                match_count += 1
        
        accuracy = match_count / len(should_match_pairs)
        assert accuracy >= 0.9, f"比對準確度 {accuracy:.2%} 低於 90%"
        
        # 測試案例：不應該匹配的產品名稱對
        should_not_match_pairs = [
            ("Microsoft SQL Server", "MySQL"),
            ("Windows Server", "Linux"),
            ("VMware ESXi", "Hyper-V"),
        ]
        
        no_match_count = 0
        for name1, name2 in should_not_match_pairs:
            result = matcher.match(name1, name2, allow_fuzzy=True)
            if not result.is_match:
                no_match_count += 1
        
        accuracy = no_match_count / len(should_not_match_pairs)
        assert accuracy >= 0.9, f"比對準確度 {accuracy:.2%} 低於 90%"

