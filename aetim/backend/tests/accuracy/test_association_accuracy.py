"""
關聯分析準確度測試

測試關聯分析的準確度，目標 ≥ 90%（AC-010-1）
"""

import pytest
from typing import List, Dict, Any
from analysis_assessment.domain.domain_services.association_analysis_service import (
    AssociationAnalysisService,
)
from analysis_assessment.domain.domain_services.product_name_matcher import ProductNameMatcher
from analysis_assessment.domain.domain_services.version_matcher import VersionMatcher
from threat_intelligence.domain.aggregates.threat import Threat, ThreatProduct
from asset_management.domain.aggregates.asset import Asset, AssetProduct
from asset_management.domain.value_objects.data_sensitivity import DataSensitivity
from asset_management.domain.value_objects.business_criticality import BusinessCriticality


class TestAssociationAccuracy:
    """關聯分析準確度測試"""

    @pytest.fixture
    def association_service(self):
        """建立關聯分析服務"""
        product_matcher = ProductNameMatcher()
        version_matcher = VersionMatcher()
        return AssociationAnalysisService(
            product_matcher=product_matcher,
            version_matcher=version_matcher,
        )

    @pytest.fixture
    def test_cases(self) -> List[Dict[str, Any]]:
        """
        建立測試案例
        
        包含各種產品名稱格式、版本格式、邊界情況
        """
        return [
            # 精確匹配案例
            {
                "name": "精確產品名稱和版本匹配",
                "threat_product": "Apache HTTP Server",
                "threat_version": "2.4.41",
                "asset_product": "Apache HTTP Server",
                "asset_version": "2.4.41",
                "expected_match": True,
                "expected_confidence": 1.0,
                "expected_match_type": "exact_product_exact_version",
            },
            {
                "name": "精確產品名稱，無版本",
                "threat_product": "Apache HTTP Server",
                "threat_version": None,
                "asset_product": "Apache HTTP Server",
                "asset_version": None,
                "expected_match": True,
                "expected_confidence": 0.8,
                "expected_match_type": "exact_product_no_version",
            },
            # 版本範圍匹配案例
            {
                "name": "版本範圍匹配（7.0.x）",
                "threat_product": "Windows",
                "threat_version": "7.0.1",
                "asset_product": "Windows",
                "asset_version": "7.0.x",
                "expected_match": True,
                "expected_confidence": 0.9,
                "expected_match_type": "exact_product_version_range",
            },
            {
                "name": "版本範圍匹配（>= 7.0）",
                "threat_product": "Windows",
                "threat_version": "7.1",
                "asset_product": "Windows",
                "asset_version": ">= 7.0",
                "expected_match": True,
                "expected_confidence": 0.9,
                "expected_match_type": "exact_product_version_range",
            },
            # 主版本匹配案例
            {
                "name": "主版本匹配",
                "threat_product": "Apache HTTP Server",
                "threat_version": "2.4.50",
                "asset_product": "Apache HTTP Server",
                "asset_version": "2.4.41",
                "expected_match": True,
                "expected_confidence": 0.85,
                "expected_match_type": "exact_product_major_version",
            },
            # 模糊匹配案例
            {
                "name": "模糊產品名稱匹配（Apache vs Apache HTTP Server）",
                "threat_product": "Apache",
                "threat_version": "2.4.41",
                "asset_product": "Apache HTTP Server",
                "asset_version": "2.4.41",
                "expected_match": True,
                "expected_confidence": 0.75,
                "expected_match_type": "fuzzy_product_exact_version",
            },
            {
                "name": "模糊產品名稱匹配（Windows 10 vs Windows）",
                "threat_product": "Windows 10",
                "threat_version": "10.0.19041",
                "asset_product": "Windows",
                "asset_version": "10.0.19041",
                "expected_match": True,
                "expected_confidence": 0.8,
                "expected_match_type": "fuzzy_product_exact_version",
            },
            # 不匹配案例
            {
                "name": "產品名稱不匹配",
                "threat_product": "Apache HTTP Server",
                "threat_version": "2.4.41",
                "asset_product": "Nginx",
                "asset_version": "1.18.0",
                "expected_match": False,
                "expected_confidence": 0.0,
                "expected_match_type": None,
            },
            {
                "name": "版本不匹配（超出範圍）",
                "threat_product": "Windows",
                "threat_version": "6.1",
                "asset_product": "Windows",
                "asset_version": ">= 7.0",
                "expected_match": False,
                "expected_confidence": 0.0,
                "expected_match_type": None,
            },
            # 邊界情況
            {
                "name": "空版本匹配",
                "threat_product": "Apache HTTP Server",
                "threat_version": "",
                "asset_product": "Apache HTTP Server",
                "asset_version": "",
                "expected_match": True,
                "expected_confidence": 0.8,
                "expected_match_type": "exact_product_no_version",
            },
            {
                "name": "特殊字符處理（Apache HTTP Server 2.4 vs Apache HTTP Server 2.4）",
                "threat_product": "Apache HTTP Server 2.4",
                "threat_version": "2.4.41",
                "asset_product": "Apache HTTP Server",
                "asset_version": "2.4.41",
                "expected_match": True,
                "expected_confidence": 0.9,
                "expected_match_type": "fuzzy_product_exact_version",
            },
        ]

    def test_product_name_matching_accuracy(
        self, association_service: AssociationAnalysisService, test_cases: List[Dict[str, Any]]
    ):
        """
        測試產品名稱比對準確度（目標 ≥ 90%）
        """
        correct_matches = 0
        total_cases = len(test_cases)

        for case in test_cases:
            # 建立威脅產品
            threat_product = ThreatProduct(
                id="test-threat-product",
                product_name=case["threat_product"],
                product_version=case["threat_version"],
            )

            # 建立資產產品
            asset_product = AssetProduct(
                id="test-asset-product",
                product_name=case["asset_product"],
                product_version=case["asset_version"],
            )

            # 執行匹配
            result = association_service._match_products(
                threat_product, asset_product, "test-threat", "test-asset"
            )

            # 驗證結果
            if case["expected_match"]:
                if result is not None and result.match_type is not None:
                    correct_matches += 1
            else:
                if result is None or result.match_type is None:
                    correct_matches += 1

        accuracy = (correct_matches / total_cases) * 100
        print(f"\n產品名稱比對準確度: {accuracy:.2f}% ({correct_matches}/{total_cases})")

        assert accuracy >= 90.0, f"產品名稱比對準確度 {accuracy:.2f}% 低於目標 90%"

    def test_version_matching_accuracy(
        self, association_service: AssociationAnalysisService, test_cases: List[Dict[str, Any]]
    ):
        """
        測試版本範圍比對準確度（目標 ≥ 90%）
        """
        correct_matches = 0
        total_cases = len([c for c in test_cases if c["threat_version"] and c["asset_version"]])

        for case in test_cases:
            if not case["threat_version"] or not case["asset_version"]:
                continue

            # 建立威脅產品
            threat_product = ThreatProduct(
                id="test-threat-product",
                product_name=case["threat_product"],
                product_version=case["threat_version"],
            )

            # 建立資產產品
            asset_product = AssetProduct(
                id="test-asset-product",
                product_name=case["asset_product"],
                product_version=case["asset_version"],
            )

            # 執行匹配
            result = association_service._match_products(
                threat_product, asset_product, "test-threat", "test-asset"
            )

            # 驗證版本匹配
            if case["expected_match"]:
                if result is not None and result.match_type and "version" in result.match_type.value:
                    correct_matches += 1
            else:
                if result is None or not result.match_type or "version" not in result.match_type.value:
                    correct_matches += 1

        if total_cases > 0:
            accuracy = (correct_matches / total_cases) * 100
            print(f"\n版本範圍比對準確度: {accuracy:.2f}% ({correct_matches}/{total_cases})")

            assert accuracy >= 90.0, f"版本範圍比對準確度 {accuracy:.2f}% 低於目標 90%"

    def test_overall_association_accuracy(
        self, association_service: AssociationAnalysisService, test_cases: List[Dict[str, Any]]
    ):
        """
        測試整體關聯分析準確度（目標 ≥ 90%）
        """
        correct_matches = 0
        total_cases = len(test_cases)

        for case in test_cases:
            # 建立威脅
            threat_products = [
                ThreatProduct(
                    id="test-threat-product",
                    product_name=case["threat_product"],
                    product_version=case["threat_version"],
                )
            ]
            threat = Threat.create(
                id="test-threat",
                threat_feed_id="test-feed",
                title="Test Threat",
                products=threat_products,
            )

            # 建立資產
            asset_products = [
                AssetProduct(
                    id="test-asset-product",
                    product_name=case["asset_product"],
                    product_version=case["asset_version"],
                )
            ]
            asset = Asset.create(
                id="test-asset",
                name="Test Asset",
                asset_type="Server",
                data_sensitivity=DataSensitivity.MEDIUM,
                business_criticality=BusinessCriticality.MEDIUM,
                products=asset_products,
            )

            # 執行關聯分析
            result = association_service._match_threat_to_asset(threat, asset)

            # 驗證結果
            if case["expected_match"]:
                if result is not None and result.match_type is not None:
                    # 驗證信心分數（允許 ±0.1 的誤差）
                    expected_confidence = case["expected_confidence"]
                    actual_confidence = result.confidence
                    if abs(actual_confidence - expected_confidence) <= 0.1:
                        correct_matches += 1
            else:
                if result is None or result.match_type is None:
                    correct_matches += 1

        accuracy = (correct_matches / total_cases) * 100
        print(f"\n整體關聯分析準確度: {accuracy:.2f}% ({correct_matches}/{total_cases})")

        assert accuracy >= 90.0, f"整體關聯分析準確度 {accuracy:.2f}% 低於目標 90%"

    def test_confidence_score_calculation(
        self, association_service: AssociationAnalysisService
    ):
        """
        測試信心分數計算的準確性
        """
        test_cases = [
            {
                "product_match": "exact",
                "version_match": "exact",
                "expected_min": 0.95,
                "expected_max": 1.0,
            },
            {
                "product_match": "exact",
                "version_match": "range",
                "expected_min": 0.85,
                "expected_max": 0.95,
            },
            {
                "product_match": "exact",
                "version_match": "major",
                "expected_min": 0.80,
                "expected_max": 0.90,
            },
            {
                "product_match": "fuzzy",
                "version_match": "exact",
                "expected_min": 0.70,
                "expected_max": 0.85,
            },
        ]

        for case in test_cases:
            # 建立測試數據
            threat_product = ThreatProduct(
                id="test",
                product_name="Apache HTTP Server",
                product_version="2.4.41",
            )
            asset_product = AssetProduct(
                id="test",
                product_name="Apache HTTP Server",
                product_version="2.4.41",
            )

            # 執行匹配
            result = association_service._match_products(
                threat_product, asset_product, "test-threat", "test-asset"
            )

            # 驗證結果存在
            assert result is not None, "匹配結果不應為 None"

            # 驗證信心分數範圍
            assert (
                case["expected_min"] <= result.confidence <= case["expected_max"]
            ), f"信心分數 {result.confidence} 不在預期範圍 [{case['expected_min']}, {case['expected_max']}]"

