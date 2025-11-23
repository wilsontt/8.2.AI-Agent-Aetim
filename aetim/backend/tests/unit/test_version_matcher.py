"""
版本比對器單元測試

測試版本比對邏輯的精確匹配、範圍匹配和版本解析功能。
"""

import pytest

from analysis_assessment.domain.domain_services.version_matcher import (
    VersionMatcher,
    VersionMatchResult,
    VersionMatchType,
)


class TestVersionMatcher:
    """版本比對器測試"""
    
    @pytest.fixture
    def matcher(self):
        """建立版本比對器實例"""
        return VersionMatcher()
    
    def test_exact_match_same_version(self, matcher):
        """測試精確匹配：相同版本"""
        result = matcher.exact_match("7.0.1", "7.0.1")
        
        assert result.is_match is True
        assert result.match_type == VersionMatchType.EXACT
    
    def test_exact_match_different_version(self, matcher):
        """測試精確匹配：不同版本"""
        result = matcher.exact_match("7.0.1", "7.0.2")
        
        assert result.is_match is False
        assert result.match_type is None
    
    def test_exact_match_case_insensitive(self, matcher):
        """測試精確匹配：大小寫不敏感（版本前綴）"""
        result = matcher.exact_match("v7.0.1", "7.0.1")
        
        assert result.is_match is True
        assert result.match_type == VersionMatchType.EXACT
    
    def test_exact_match_no_version(self, matcher):
        """測試精確匹配：無版本"""
        result = matcher.exact_match(None, None)
        
        assert result.is_match is True
        assert result.match_type == VersionMatchType.NO_VERSION
    
    def test_exact_match_threat_no_version(self, matcher):
        """測試精確匹配：威脅版本為空（視為影響所有版本）"""
        result = matcher.exact_match(None, "7.0.1")
        
        assert result.is_match is True
        assert result.match_type == VersionMatchType.NO_VERSION
    
    def test_exact_match_asset_no_version(self, matcher):
        """測試精確匹配：資產版本為空（無法比對）"""
        result = matcher.exact_match("7.0.1", None)
        
        assert result.is_match is False
        assert result.match_type is None
    
    def test_range_match_version_range(self, matcher):
        """測試版本範圍匹配：版本範圍格式"""
        test_cases = [
            ("7.0.x", "7.0.1", True),
            ("7.0.x", "7.0.2", True),
            ("7.0.x", "7.1.0", False),  # 不匹配，因為主版本不同
            ("7.0.x", "8.0.1", False),  # 不匹配
        ]
        
        for threat_version, asset_version, should_match in test_cases:
            result = matcher.range_match(threat_version, asset_version)
            assert result.is_match == should_match, (
                f"Failed for {threat_version} vs {asset_version}"
            )
            if should_match:
                assert result.match_type == VersionMatchType.RANGE
    
    def test_range_match_major_version(self, matcher):
        """測試版本範圍匹配：主版本匹配"""
        test_cases = [
            ("7", "7.0", True),
            ("7", "7.1", True),
            ("7", "7.2.1", True),
            ("7", "8.0", False),  # 不匹配
        ]
        
        for threat_version, asset_version, should_match in test_cases:
            result = matcher.range_match(threat_version, asset_version)
            assert result.is_match == should_match, (
                f"Failed for {threat_version} vs {asset_version}"
            )
            if should_match:
                assert result.match_type == VersionMatchType.MAJOR
    
    def test_range_match_version_comparison(self, matcher):
        """測試版本範圍匹配：版本比較"""
        test_cases = [
            (">= 7.0", "7.0", True),
            (">= 7.0", "7.1", True),
            (">= 7.0", "8.0", True),
            (">= 7.0", "6.9", False),
            ("<= 7.0", "7.0", True),
            ("<= 7.0", "6.9", True),
            ("<= 7.0", "7.1", False),
            ("> 7.0", "7.1", True),
            ("> 7.0", "7.0", False),
            ("< 7.0", "6.9", True),
            ("< 7.0", "7.0", False),
        ]
        
        for threat_version, asset_version, should_match in test_cases:
            result = matcher.range_match(threat_version, asset_version)
            assert result.is_match == should_match, (
                f"Failed for {threat_version} vs {asset_version}"
            )
            if should_match:
                assert result.match_type == VersionMatchType.COMPARISON
    
    def test_parse_version_semantic_version(self, matcher):
        """測試版本號解析：語義版本格式"""
        test_cases = [
            ("7.0.1", (7, 0, 1)),
            ("7.0", (7, 0,)),
            ("7", (7,)),
            ("10.0.1", (10, 0, 1)),
        ]
        
        for version_str, expected_parsed in test_cases:
            parsed = matcher.parse_version(version_str)
            assert parsed == expected_parsed, f"Failed for {version_str}"
    
    def test_parse_version_with_prefix(self, matcher):
        """測試版本號解析：帶前綴的版本"""
        test_cases = [
            ("v7.0.1", (7, 0, 1)),
            ("version 7.0.1", (7, 0, 1)),
            ("V7.0.1", (7, 0, 1)),
        ]
        
        for version_str, expected_parsed in test_cases:
            parsed = matcher.parse_version(version_str)
            assert parsed == expected_parsed, f"Failed for {version_str}"
    
    def test_parse_version_year_format(self, matcher):
        """測試版本號解析：年份格式"""
        test_cases = [
            ("2017", (2017,)),
            ("2019", (2019,)),
            ("2022", (2022,)),
        ]
        
        for version_str, expected_parsed in test_cases:
            parsed = matcher.parse_version(version_str)
            assert parsed == expected_parsed, f"Failed for {version_str}"
    
    def test_parse_version_with_suffix(self, matcher):
        """測試版本號解析：帶後綴的版本"""
        test_cases = [
            ("7.0.1-beta", (7, 0, 1)),
            ("7.0.1-rc1", (7, 0, 1)),
            ("7.0.1-SNAPSHOT", (7, 0, 1)),
        ]
        
        for version_str, expected_parsed in test_cases:
            parsed = matcher.parse_version(version_str)
            assert parsed == expected_parsed, f"Failed for {version_str}"
    
    def test_parse_version_invalid(self, matcher):
        """測試版本號解析：無效版本"""
        test_cases = [
            ("", None),
            ("invalid", None),
            ("abc.def", None),
        ]
        
        for version_str, expected_parsed in test_cases:
            parsed = matcher.parse_version(version_str)
            assert parsed == expected_parsed, f"Failed for {version_str}"
    
    def test_compare_versions_equal(self, matcher):
        """測試版本比較：相等"""
        result = matcher.compare_versions((7, 0, 1), (7, 0, 1))
        assert result == 0
    
    def test_compare_versions_greater(self, matcher):
        """測試版本比較：大於"""
        test_cases = [
            ((7, 0, 2), (7, 0, 1), 1),
            ((7, 1, 0), (7, 0, 1), 1),
            ((8, 0, 0), (7, 0, 1), 1),
        ]
        
        for version1, version2, expected in test_cases:
            result = matcher.compare_versions(version1, version2)
            assert result == expected, f"Failed for {version1} vs {version2}"
    
    def test_compare_versions_less(self, matcher):
        """測試版本比較：小於"""
        test_cases = [
            ((7, 0, 1), (7, 0, 2), -1),
            ((7, 0, 1), (7, 1, 0), -1),
            ((7, 0, 1), (8, 0, 0), -1),
        ]
        
        for version1, version2, expected in test_cases:
            result = matcher.compare_versions(version1, version2)
            assert result == expected, f"Failed for {version1} vs {version2}"
    
    def test_compare_versions_different_length(self, matcher):
        """測試版本比較：不同長度"""
        test_cases = [
            ((7, 0, 1), (7, 0), 1),  # 7.0.1 > 7.0
            ((7, 0), (7, 0, 1), -1),  # 7.0 < 7.0.1
            ((7, 0), (7, 0), 0),  # 7.0 == 7.0
        ]
        
        for version1, version2, expected in test_cases:
            result = matcher.compare_versions(version1, version2)
            assert result == expected, f"Failed for {version1} vs {version2}"
    
    def test_match_exact_first(self, matcher):
        """測試 match 方法：優先精確匹配"""
        result = matcher.match("7.0.1", "7.0.1", allow_range=True)
        
        assert result.is_match is True
        assert result.match_type == VersionMatchType.EXACT
    
    def test_match_range_fallback(self, matcher):
        """測試 match 方法：精確匹配失敗時使用範圍匹配"""
        result = matcher.match("7.0.x", "7.0.1", allow_range=True)
        
        assert result.is_match is True
        assert result.match_type == VersionMatchType.RANGE
    
    def test_match_no_range(self, matcher):
        """測試 match 方法：不允許範圍匹配"""
        result = matcher.match("7.0.x", "7.0.1", allow_range=False)
        
        assert result.is_match is False
    
    def test_normalize_version(self, matcher):
        """測試版本標準化"""
        test_cases = [
            ("v7.0.1", "7.0.1"),
            ("version 7.0.1", "7.0.1"),
            ("V7.0.1", "7.0.1"),
            ("  7.0.1  ", "7.0.1"),
        ]
        
        for input_version, expected_normalized in test_cases:
            normalized = matcher._normalize_version(input_version)
            assert normalized == expected_normalized, f"Failed for {input_version}"
    
    def test_version_range_comprehensive(self, matcher):
        """測試版本範圍匹配的綜合測試"""
        # 測試各種版本範圍格式
        test_cases = [
            ("7.0.x", "7.0.1", True),
            ("7.0.x", "7.0.2", True),
            ("7.0.x", "7.0.10", True),
            ("7.0.x", "7.1.0", False),
            ("7", "7.0", True),
            ("7", "7.1", True),
            ("7", "7.2.1", True),
            ("7", "8.0", False),
        ]
        
        for threat_version, asset_version, should_match in test_cases:
            result = matcher.range_match(threat_version, asset_version)
            assert result.is_match == should_match, (
                f"Failed for {threat_version} vs {asset_version}"
            )

