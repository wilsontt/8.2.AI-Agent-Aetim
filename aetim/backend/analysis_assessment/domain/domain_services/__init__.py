"""
領域服務

包含領域層的服務類別。
"""

from .association_analysis_service import AssociationAnalysisService, AssociationResult
from .product_name_matcher import ProductNameMatcher, ProductMatchResult
from .version_matcher import VersionMatcher, VersionMatchResult, VersionMatchType

__all__ = [
    "AssociationAnalysisService",
    "AssociationResult",
    "ProductNameMatcher",
    "ProductMatchResult",
    "VersionMatcher",
    "VersionMatchResult",
    "VersionMatchType",
]

