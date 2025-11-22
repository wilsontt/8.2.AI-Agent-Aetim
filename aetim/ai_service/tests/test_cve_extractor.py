"""
CVE 編號提取器單元測試

測試 CVEExtractor 的各種功能，包括：
- 提取單一 CVE
- 提取所有 CVE
- 格式驗證
- 邊界情況處理
"""

import pytest
from app.processors.cve_extractor import CVEExtractor


class TestCVEExtractor:
    """CVE 編號提取器測試"""
    
    @pytest.fixture
    def extractor(self):
        """建立 CVEExtractor 實例"""
        return CVEExtractor()
    
    # ========== extract 方法測試 ==========
    
    def test_extract_single_cve_standard_format(self, extractor):
        """測試提取標準格式的 CVE"""
        text = "This vulnerability is CVE-2024-12345"
        result = extractor.extract(text)
        
        assert result == "CVE-2024-12345"
    
    def test_extract_single_cve_lowercase(self, extractor):
        """測試提取小寫格式的 CVE"""
        text = "This vulnerability is cve-2024-12345"
        result = extractor.extract(text)
        
        assert result == "CVE-2024-12345"  # 應轉換為大寫
    
    def test_extract_single_cve_with_space(self, extractor):
        """測試提取帶空格的 CVE"""
        text = "This vulnerability is CVE 2024 12345"
        result = extractor.extract(text)
        
        assert result == "CVE-2024-12345"  # 應標準化為連字號格式
    
    def test_extract_single_cve_with_hyphen_variations(self, extractor):
        """測試提取各種連字號變體的 CVE"""
        test_cases = [
            ("CVE-2024-12345", "CVE-2024-12345"),
            ("CVE 2024-12345", "CVE-2024-12345"),
            ("CVE-2024 12345", "CVE-2024-12345"),
            ("CVE 2024 12345", "CVE-2024-12345"),
        ]
        
        for input_text, expected in test_cases:
            result = extractor.extract(input_text)
            assert result == expected, f"Failed for input: {input_text}"
    
    def test_extract_single_cve_multiple_in_text(self, extractor):
        """測試文字中包含多個 CVE 時提取第一個"""
        text = "CVE-2024-12345 and CVE-2024-67890 are both vulnerabilities"
        result = extractor.extract(text)
        
        assert result == "CVE-2024-12345"  # 應返回第一個
    
    def test_extract_single_cve_not_found(self, extractor):
        """測試文字中沒有 CVE 時返回 None"""
        text = "This text has no CVE numbers"
        result = extractor.extract(text)
        
        assert result is None
    
    def test_extract_single_cve_invalid_year_too_old(self, extractor):
        """測試年份過舊的 CVE（應被過濾）"""
        text = "CVE-1998-12345"  # CVE 從 1999 年開始
        result = extractor.extract(text)
        
        assert result is None
    
    def test_extract_single_cve_invalid_year_too_new(self, extractor):
        """測試年份過新的 CVE（應被過濾）"""
        text = "CVE-2100-12345"  # 超過最大年份
        result = extractor.extract(text)
        
        assert result is None
    
    def test_extract_single_cve_invalid_format(self, extractor):
        """測試無效格式的 CVE"""
        invalid_cases = [
            "CVE-2024-123",  # 序號太短（少於 4 位）
            "CVE-2024-12345678",  # 序號太長（超過 7 位）
            "CVE-24-12345",  # 年份太短
            "CVE-20245-12345",  # 年份太長
            "CVE2024-12345",  # 缺少連字號
            "2024-12345",  # 缺少 CVE 前綴
        ]
        
        for invalid_text in invalid_cases:
            result = extractor.extract(invalid_text)
            assert result is None, f"Should not extract invalid CVE: {invalid_text}"
    
    def test_extract_single_cve_empty_string(self, extractor):
        """測試空字串"""
        result = extractor.extract("")
        assert result is None
    
    def test_extract_single_cve_none_input(self, extractor):
        """測試 None 輸入"""
        result = extractor.extract(None)
        assert result is None
    
    def test_extract_single_cve_non_string_input(self, extractor):
        """測試非字串輸入"""
        result = extractor.extract(12345)
        assert result is None
    
    # ========== extract_all 方法測試 ==========
    
    def test_extract_all_multiple_cves(self, extractor):
        """測試提取多個 CVE"""
        text = "CVE-2024-12345 and CVE-2024-67890 are both vulnerabilities"
        result = extractor.extract_all(text)
        
        assert len(result) == 2
        assert "CVE-2024-12345" in result
        assert "CVE-2024-67890" in result
    
    def test_extract_all_duplicate_cves(self, extractor):
        """測試提取重複的 CVE（應去重）"""
        text = "CVE-2024-12345 appears twice. CVE-2024-12345 is mentioned again."
        result = extractor.extract_all(text)
        
        assert len(result) == 1
        assert result[0] == "CVE-2024-12345"
    
    def test_extract_all_sorted(self, extractor):
        """測試提取的 CVE 是否排序"""
        text = "CVE-2024-99999, CVE-2024-11111, CVE-2023-12345"
        result = extractor.extract_all(text)
        
        # 應按年份和序號排序
        assert result == ["CVE-2023-12345", "CVE-2024-11111", "CVE-2024-99999"]
    
    def test_extract_all_no_cves(self, extractor):
        """測試沒有 CVE 時返回空列表"""
        text = "This text has no CVE numbers"
        result = extractor.extract_all(text)
        
        assert result == []
    
    def test_extract_all_mixed_valid_invalid(self, extractor):
        """測試混合有效和無效的 CVE"""
        text = "CVE-2024-12345 is valid, but CVE-1998-12345 is too old"
        result = extractor.extract_all(text)
        
        # 應只提取有效的 CVE
        assert len(result) == 1
        assert result[0] == "CVE-2024-12345"
    
    def test_extract_all_various_formats(self, extractor):
        """測試各種格式變體的 CVE"""
        text = "CVE-2024-12345, cve-2024-67890, CVE 2024-11111, CVE-2024 22222"
        result = extractor.extract_all(text)
        
        assert len(result) == 4
        assert "CVE-2024-12345" in result
        assert "CVE-2024-67890" in result
        assert "CVE-2024-11111" in result
        assert "CVE-2024-22222" in result
    
    def test_extract_all_empty_string(self, extractor):
        """測試空字串"""
        result = extractor.extract_all("")
        assert result == []
    
    def test_extract_all_none_input(self, extractor):
        """測試 None 輸入"""
        result = extractor.extract_all(None)
        assert result == []
    
    # ========== is_valid_cve 方法測試 ==========
    
    def test_is_valid_cve_valid_format(self, extractor):
        """測試有效的 CVE 格式"""
        valid_cves = [
            "CVE-2024-12345",
            "CVE-1999-1234",
            "CVE-2099-1234567",
            "cve-2024-12345",  # 大小寫不敏感
        ]
        
        for cve in valid_cves:
            assert extractor.is_valid_cve(cve), f"Should be valid: {cve}"
    
    def test_is_valid_cve_invalid_format(self, extractor):
        """測試無效的 CVE 格式"""
        invalid_cves = [
            "CVE-2024-123",  # 序號太短
            "CVE-2024-12345678",  # 序號太長
            "CVE-1998-12345",  # 年份太舊
            "CVE-2100-12345",  # 年份太新
            "CVE2024-12345",  # 缺少連字號
            "2024-12345",  # 缺少 CVE 前綴
            "INVALID",
            "",
            None,
        ]
        
        for cve in invalid_cves:
            assert not extractor.is_valid_cve(cve), f"Should be invalid: {cve}"
    
    def test_is_valid_cve_edge_cases(self, extractor):
        """測試邊界情況"""
        # 最小有效年份
        assert extractor.is_valid_cve("CVE-1999-1234")
        
        # 最大有效年份
        assert extractor.is_valid_cve("CVE-2099-1234567")
        
        # 最小序號長度
        assert extractor.is_valid_cve("CVE-2024-1234")
        
        # 最大序號長度
        assert extractor.is_valid_cve("CVE-2024-1234567")
        
        # 年份太舊
        assert not extractor.is_valid_cve("CVE-1998-12345")
        
        # 年份太新
        assert not extractor.is_valid_cve("CVE-2100-12345")
        
        # 序號太短
        assert not extractor.is_valid_cve("CVE-2024-123")
        
        # 序號太長
        assert not extractor.is_valid_cve("CVE-2024-12345678")
    
    # ========== 真實場景測試 ==========
    
    def test_extract_from_security_advisory(self, extractor):
        """測試從安全通報中提取 CVE"""
        text = """
        VMware has released a security advisory for CVE-2024-12345.
        This vulnerability affects VMware ESXi 7.0.3.
        Please refer to CVE-2024-12345 for more details.
        """
        result = extractor.extract_all(text)
        
        assert len(result) == 1
        assert result[0] == "CVE-2024-12345"
    
    def test_extract_from_multiple_advisories(self, extractor):
        """測試從多個安全通報中提取 CVE"""
        text = """
        Multiple vulnerabilities have been discovered:
        - CVE-2024-11111 affects Windows Server
        - CVE-2024-22222 affects SQL Server
        - CVE-2024-33333 affects Apache
        """
        result = extractor.extract_all(text)
        
        assert len(result) == 3
        assert "CVE-2024-11111" in result
        assert "CVE-2024-22222" in result
        assert "CVE-2024-33333" in result
    
    def test_extract_from_mixed_content(self, extractor):
        """測試從混合內容中提取 CVE"""
        text = """
        This is a security notice about CVE-2024-12345.
        The vulnerability was discovered in 2024.
        Reference: CVE-2024-12345
        """
        result = extractor.extract_all(text)
        
        # 應正確提取，不會誤判 "2024" 為 CVE 的一部分
        assert len(result) == 1
        assert result[0] == "CVE-2024-12345"

