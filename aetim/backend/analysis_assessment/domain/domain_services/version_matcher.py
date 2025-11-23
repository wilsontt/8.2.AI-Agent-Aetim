"""
版本比對器

實作版本的精確與範圍比對邏輯（Domain Service）。
"""

from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re

from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class VersionMatchType(Enum):
    """版本匹配類型"""
    
    EXACT = "exact"  # 精確版本匹配
    RANGE = "range"  # 版本範圍匹配（如 "7.0.x"）
    MAJOR = "major"  # 主版本匹配（如 "7" 匹配 "7.x"）
    COMPARISON = "comparison"  # 版本比較匹配（如 ">= 7.0"）
    NO_VERSION = "no_version"  # 無版本匹配


@dataclass
class VersionMatchResult:
    """
    版本比對結果
    
    表示版本比對的結果。
    """
    
    is_match: bool
    match_type: Optional[VersionMatchType]
    threat_version_parsed: Optional[Tuple[int, ...]]  # 解析後的威脅版本
    asset_version_parsed: Optional[Tuple[int, ...]]  # 解析後的資產版本
    
    def __str__(self) -> str:
        return (
            f"VersionMatchResult(is_match={self.is_match}, "
            f"match_type={self.match_type.value if self.match_type else None})"
        )


class VersionMatcher:
    """
    版本比對器（Domain Service）
    
    負責版本的精確與範圍比對（AC-010-1, AC-010-2）。
    """
    
    def exact_match(
        self,
        threat_version: Optional[str],
        asset_version: Optional[str],
    ) -> VersionMatchResult:
        """
        精確版本匹配（AC-010-1）
        
        完全相同的版本號（如 "7.0.1" = "7.0.1"）。
        
        Args:
            threat_version: 威脅產品版本
            asset_version: 資產產品版本
        
        Returns:
            VersionMatchResult: 比對結果
        """
        # 如果兩個版本都為空，視為匹配（無版本資訊）
        if not threat_version and not asset_version:
            return VersionMatchResult(
                is_match=True,
                match_type=VersionMatchType.NO_VERSION,
                threat_version_parsed=None,
                asset_version_parsed=None,
            )
        
        # 如果威脅版本為空，視為匹配（威脅影響所有版本）
        if not threat_version:
            return VersionMatchResult(
                is_match=True,
                match_type=VersionMatchType.NO_VERSION,
                threat_version_parsed=None,
                asset_version_parsed=self.parse_version(asset_version),
            )
        
        # 如果資產版本為空，無法比對
        if not asset_version:
            return VersionMatchResult(
                is_match=False,
                match_type=None,
                threat_version_parsed=self.parse_version(threat_version),
                asset_version_parsed=None,
            )
        
        # 標準化版本字串
        threat_version_clean = self._normalize_version(threat_version)
        asset_version_clean = self._normalize_version(asset_version)
        
        # 精確版本匹配
        is_match = threat_version_clean == asset_version_clean
        
        logger.debug(
            f"精確版本匹配：{threat_version} vs {asset_version}",
            extra={
                "threat_version": threat_version,
                "asset_version": asset_version,
                "threat_version_clean": threat_version_clean,
                "asset_version_clean": asset_version_clean,
                "is_match": is_match,
            }
        )
        
        return VersionMatchResult(
            is_match=is_match,
            match_type=VersionMatchType.EXACT if is_match else None,
            threat_version_parsed=self.parse_version(threat_version),
            asset_version_parsed=self.parse_version(asset_version),
        )
    
    def range_match(
        self,
        threat_version: Optional[str],
        asset_version: Optional[str],
    ) -> VersionMatchResult:
        """
        版本範圍匹配（AC-010-2）
        
        支援：
        - 版本範圍格式（如 "7.0.x" 匹配 "7.0.1", "7.0.2" 等）
        - 主版本匹配（如 "7" 匹配 "7.0", "7.1", "7.2" 等）
        - 版本比較（如 ">= 7.0" 匹配 "7.0" 及以上版本）
        
        Args:
            threat_version: 威脅產品版本
            asset_version: 資產產品版本
        
        Returns:
            VersionMatchResult: 比對結果
        """
        # 先嘗試精確匹配
        exact_result = self.exact_match(threat_version, asset_version)
        if exact_result.is_match:
            return exact_result
        
        # 如果威脅版本為空或資產版本為空，返回精確匹配結果
        if not threat_version or not asset_version:
            return exact_result
        
        # 標準化版本字串
        threat_version_clean = self._normalize_version(threat_version)
        asset_version_clean = self._normalize_version(asset_version)
        
        # 解析版本號
        threat_version_parsed = self.parse_version(threat_version)
        asset_version_parsed = self.parse_version(asset_version)
        
        if not threat_version_parsed or not asset_version_parsed:
            return VersionMatchResult(
                is_match=False,
                match_type=None,
                threat_version_parsed=threat_version_parsed,
                asset_version_parsed=asset_version_parsed,
            )
        
        # 1. 版本範圍匹配（如 "7.0.x" 匹配 "7.0.1", "7.0.2" 等）
        if threat_version_clean.endswith(".x"):
            base_version = threat_version_clean[:-2]  # 移除 ".x"
            if asset_version_clean.startswith(base_version):
                logger.debug(
                    f"版本範圍匹配：{threat_version} vs {asset_version}",
                    extra={
                        "threat_version": threat_version,
                        "asset_version": asset_version,
                        "base_version": base_version,
                    }
                )
                return VersionMatchResult(
                    is_match=True,
                    match_type=VersionMatchType.RANGE,
                    threat_version_parsed=threat_version_parsed,
                    asset_version_parsed=asset_version_parsed,
                )
        
        # 2. 主版本匹配（如 "7" 匹配 "7.0", "7.1", "7.2" 等）
        if len(threat_version_parsed) >= 1 and len(asset_version_parsed) >= 1:
            if threat_version_parsed[0] == asset_version_parsed[0]:
                logger.debug(
                    f"主版本匹配：{threat_version} vs {asset_version}",
                    extra={
                        "threat_version": threat_version,
                        "asset_version": asset_version,
                        "major_version": threat_version_parsed[0],
                    }
                )
                return VersionMatchResult(
                    is_match=True,
                    match_type=VersionMatchType.MAJOR,
                    threat_version_parsed=threat_version_parsed,
                    asset_version_parsed=asset_version_parsed,
                )
        
        # 3. 版本比較匹配（如 ">= 7.0" 匹配 "7.0" 及以上版本）
        comparison_result = self._match_version_comparison(
            threat_version_clean,
            asset_version_parsed,
        )
        if comparison_result:
            return VersionMatchResult(
                is_match=True,
                match_type=VersionMatchType.COMPARISON,
                threat_version_parsed=threat_version_parsed,
                asset_version_parsed=asset_version_parsed,
            )
        
        return VersionMatchResult(
            is_match=False,
            match_type=None,
            threat_version_parsed=threat_version_parsed,
            asset_version_parsed=asset_version_parsed,
        )
    
    def parse_version(self, version: str) -> Optional[Tuple[int, ...]]:
        """
        版本號解析（AC-010-2）
        
        解析各種版本格式（"7.0.1", "v7.0.1", "2017" 等），
        標準化為語義版本格式（Major.Minor.Patch）。
        
        Args:
            version: 版本字串
        
        Returns:
            Optional[Tuple[int, ...]]: 解析後的版本號元組，如果無法解析則返回 None
        """
        if not version:
            return None
        
        # 標準化版本字串
        normalized = self._normalize_version(version)
        
        # 嘗試解析語義版本（Major.Minor.Patch）
        # 例如："7.0.1" -> (7, 0, 1)
        parts = normalized.split(".")
        version_parts = []
        
        for part in parts:
            # 移除非數字字元（如 "7.0.1-beta" -> "7.0.1"）
            part_clean = re.sub(r'[^\d]', '', part)
            if part_clean:
                try:
                    version_parts.append(int(part_clean))
                except ValueError:
                    # 如果無法轉換為整數，跳過
                    break
        
        if not version_parts:
            # 如果無法解析，嘗試解析年份格式（如 "2017", "2019"）
            year_match = re.match(r'^(\d{4})', normalized)
            if year_match:
                year = int(year_match.group(1))
                return (year,)
            
            return None
        
        return tuple(version_parts)
    
    def compare_versions(
        self,
        version1: Optional[Tuple[int, ...]],
        version2: Optional[Tuple[int, ...]],
    ) -> int:
        """
        版本比較（AC-010-2）
        
        比較兩個版本號的大小。
        支援語義版本比較。
        
        Args:
            version1: 版本號 1（解析後的元組）
            version2: 版本號 2（解析後的元組）
        
        Returns:
            int: 
                - 如果 version1 > version2，返回 1
                - 如果 version1 < version2，返回 -1
                - 如果 version1 == version2，返回 0
                - 如果無法比較，返回 0
        """
        if not version1 or not version2:
            return 0
        
        # 比較版本號的每個部分
        max_length = max(len(version1), len(version2))
        
        for i in range(max_length):
            v1_part = version1[i] if i < len(version1) else 0
            v2_part = version2[i] if i < len(version2) else 0
            
            if v1_part > v2_part:
                return 1
            elif v1_part < v2_part:
                return -1
        
        return 0
    
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
    
    def _match_version_comparison(
        self,
        threat_version: str,
        asset_version_parsed: Tuple[int, ...],
    ) -> bool:
        """
        版本比較匹配（如 ">= 7.0" 匹配 "7.0" 及以上版本）
        
        Args:
            threat_version: 威脅版本字串
            asset_version_parsed: 資產版本（解析後的元組）
        
        Returns:
            bool: 是否匹配
        """
        # 匹配版本比較運算子（如 ">= 7.0", "<= 7.0", "> 7.0", "< 7.0"）
        comparison_pattern = r'^(>=|<=|>|<)\s*(\d+(?:\.\d+)*)'
        match = re.match(comparison_pattern, threat_version)
        
        if not match:
            return False
        
        operator = match.group(1)
        version_str = match.group(2)
        
        # 解析比較版本
        comparison_version = self.parse_version(version_str)
        if not comparison_version:
            return False
        
        # 比較版本
        comparison_result = self.compare_versions(asset_version_parsed, comparison_version)
        
        if operator == ">=":
            return comparison_result >= 0
        elif operator == "<=":
            return comparison_result <= 0
        elif operator == ">":
            return comparison_result > 0
        elif operator == "<":
            return comparison_result < 0
        
        return False
    
    def match(
        self,
        threat_version: Optional[str],
        asset_version: Optional[str],
        allow_range: bool = True,
    ) -> VersionMatchResult:
        """
        比對版本（精確或範圍）
        
        先嘗試精確匹配，如果失敗且允許範圍匹配，則嘗試範圍匹配。
        
        Args:
            threat_version: 威脅產品版本
            asset_version: 資產產品版本
            allow_range: 是否允許範圍匹配（預設 True）
        
        Returns:
            VersionMatchResult: 比對結果
        """
        # 先嘗試精確匹配
        exact_result = self.exact_match(threat_version, asset_version)
        if exact_result.is_match:
            return exact_result
        
        # 如果精確匹配失敗且允許範圍匹配，嘗試範圍匹配
        if allow_range:
            return self.range_match(threat_version, asset_version)
        
        # 不允許範圍匹配，返回失敗結果
        return exact_result

