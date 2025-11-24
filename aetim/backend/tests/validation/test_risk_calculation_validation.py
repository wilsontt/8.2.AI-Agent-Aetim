"""
風險計算邏輯驗證

驗證風險計算邏輯的正確性，符合 plan.md 設計
"""

import pytest
from decimal import Decimal
from analysis_assessment.domain.domain_services.risk_calculation_service import (
    RiskCalculationService,
)
from analysis_assessment.domain.domain_services.cvss_score_calculator import CVSSScoreCalculator
from analysis_assessment.domain.domain_services.weight_factor_calculator import (
    WeightFactorCalculator,
)
from analysis_assessment.domain.domain_services.risk_level_classifier import RiskLevelClassifier
from threat_intelligence.domain.aggregates.threat import Threat, ThreatProduct
from asset_management.domain.aggregates.asset import Asset, AssetProduct
from asset_management.domain.value_objects.data_sensitivity import DataSensitivity
from asset_management.domain.value_objects.business_criticality import BusinessCriticality
from analysis_assessment.domain.aggregates.pir import PIR, PIRPriority, PIRCondition


class TestRiskCalculationValidation:
    """風險計算邏輯驗證測試"""

    @pytest.fixture
    def risk_calculation_service(self):
        """建立風險計算服務"""
        cvss_calculator = CVSSScoreCalculator()
        weight_calculator = WeightFactorCalculator()
        risk_classifier = RiskLevelClassifier()
        return RiskCalculationService(
            cvss_calculator=cvss_calculator,
            weight_calculator=weight_calculator,
            risk_classifier=risk_classifier,
        )

    @pytest.fixture
    def sample_threat(self):
        """建立範例威脅"""
        products = [
            ThreatProduct(
                id="test-product",
                product_name="Apache HTTP Server",
                product_version="2.4.41",
            )
        ]
        return Threat.create(
            id="test-threat",
            threat_feed_id="test-feed",
            title="CVE-2020-12345: Apache HTTP Server Vulnerability",
            cve_id="CVE-2020-12345",
            cvss_base_score=7.5,
            products=products,
        )

    @pytest.fixture
    def sample_assets(self):
        """建立範例資產"""
        assets = []
        # 高敏感度、高關鍵性資產
        assets.append(
            Asset.create(
                id="asset-high-high",
                name="High Sensitivity High Criticality Asset",
                asset_type="Server",
                data_sensitivity=DataSensitivity.HIGH,
                business_criticality=BusinessCriticality.HIGH,
                products=[
                    AssetProduct(
                        id="asset-product-1",
                        product_name="Apache HTTP Server",
                        product_version="2.4.41",
                    )
                ],
            )
        )
        # 中敏感度、中關鍵性資產
        assets.append(
            Asset.create(
                id="asset-medium-medium",
                name="Medium Sensitivity Medium Criticality Asset",
                asset_type="Server",
                data_sensitivity=DataSensitivity.MEDIUM,
                business_criticality=BusinessCriticality.MEDIUM,
                products=[
                    AssetProduct(
                        id="asset-product-2",
                        product_name="Apache HTTP Server",
                        product_version="2.4.41",
                    )
                ],
            )
        )
        # 低敏感度、低關鍵性資產
        assets.append(
            Asset.create(
                id="asset-low-low",
                name="Low Sensitivity Low Criticality Asset",
                asset_type="Server",
                data_sensitivity=DataSensitivity.LOW,
                business_criticality=BusinessCriticality.LOW,
                products=[
                    AssetProduct(
                        id="asset-product-3",
                        product_name="Apache HTTP Server",
                        product_version="2.4.41",
                    )
                ],
            )
        )
        return assets

    def test_cvss_score_calculation(self, risk_calculation_service: RiskCalculationService):
        """
        測試 CVSS 基礎分數計算
        """
        test_cases = [
            {
                "cvss_score": 9.8,
                "cvss_vector": None,
                "expected": 9.8,
            },
            {
                "cvss_score": None,
                "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                "expected": 9.8,  # 根據 CVSS v3.1 計算
            },
            {
                "cvss_score": 5.5,
                "cvss_vector": None,
                "expected": 5.5,
            },
        ]

        for case in test_cases:
            threat = Threat.create(
                id="test-threat",
                threat_feed_id="test-feed",
                title="Test Threat",
                cve_id="CVE-2020-12345",
                cvss_base_score=case["cvss_score"],
                cvss_vector=case["cvss_vector"],
            )

            base_score = risk_calculation_service.cvss_calculator.calculate_base_score(threat)
            assert abs(base_score - case["expected"]) < 0.1, (
                f"CVSS 分數計算錯誤: 預期 {case['expected']}, 實際 {base_score}"
            )

    def test_asset_importance_weight_calculation(
        self, risk_calculation_service: RiskCalculationService, sample_assets
    ):
        """
        測試資產重要性加權計算
        
        公式：weight = data_sensitivity.weight * business_criticality.weight
        權重值：高=1.5、中=1.0、低=0.5
        """
        test_cases = [
            {
                "assets": [sample_assets[0]],  # 高-高
                "expected_min": 2.0,  # 1.5 * 1.5 = 2.25，但實際是平均
                "expected_max": 2.5,
            },
            {
                "assets": [sample_assets[1]],  # 中-中
                "expected_min": 0.9,
                "expected_max": 1.1,  # 1.0 * 1.0 = 1.0
            },
            {
                "assets": [sample_assets[2]],  # 低-低
                "expected_min": 0.2,
                "expected_max": 0.3,  # 0.5 * 0.5 = 0.25
            },
            {
                "assets": sample_assets,  # 混合
                "expected_min": 0.8,
                "expected_max": 1.2,  # 平均值
            },
        ]

        for case in test_cases:
            weight = risk_calculation_service.weight_calculator.calculate_asset_importance_weight(
                case["assets"]
            )
            assert case["expected_min"] <= weight <= case["expected_max"], (
                f"資產重要性加權計算錯誤: 預期範圍 [{case['expected_min']}, {case['expected_max']}], "
                f"實際 {weight}"
            )

    def test_asset_count_weight_calculation(
        self, risk_calculation_service: RiskCalculationService
    ):
        """
        測試受影響資產數量加權計算
        
        公式：weight = (affected_count / 10.0) * 0.1
        每增加 10 個資產，風險分數增加 0.1
        """
        test_cases = [
            {"count": 0, "expected": 0.0},
            {"count": 10, "expected": 0.1},
            {"count": 20, "expected": 0.2},
            {"count": 50, "expected": 0.5},
            {"count": 100, "expected": 1.0},
        ]

        for case in test_cases:
            # 建立測試資產
            assets = []
            for i in range(case["count"]):
                assets.append(
                    Asset.create(
                        id=f"asset-{i}",
                        name=f"Asset {i}",
                        asset_type="Server",
                        data_sensitivity=DataSensitivity.MEDIUM,
                        business_criticality=BusinessCriticality.MEDIUM,
                    )
                )

            weight = risk_calculation_service.weight_calculator.calculate_asset_count_weight(
                case["count"]
            )
            assert abs(weight - case["expected"]) < 0.01, (
                f"資產數量加權計算錯誤: 預期 {case['expected']}, 實際 {weight}"
            )

    def test_pir_match_weight_calculation(
        self, risk_calculation_service: RiskCalculationService, sample_threat
    ):
        """
        測試 PIR 符合度加權計算
        
        符合高優先級 PIR，返回 0.3
        否則返回 0.0
        """
        # 建立高優先級 PIR
        high_priority_pir = PIR.create(
            id="pir-high",
            name="High Priority PIR",
            description="Test PIR",
            priority=PIRPriority.HIGH,
            conditions=[
                PIRCondition(
                    field="product_name",
                    operator="contains",
                    value="Apache",
                )
            ],
        )

        # 建立中優先級 PIR
        medium_priority_pir = PIR.create(
            id="pir-medium",
            name="Medium Priority PIR",
            description="Test PIR",
            priority=PIRPriority.MEDIUM,
            conditions=[
                PIRCondition(
                    field="product_name",
                    operator="contains",
                    value="Apache",
                )
            ],
        )

        # 測試高優先級 PIR 匹配
        weight_high = risk_calculation_service.weight_calculator.calculate_pir_match_weight(
            sample_threat, [high_priority_pir]
        )
        assert weight_high == 0.3, f"高優先級 PIR 加權應為 0.3，實際為 {weight_high}"

        # 測試中優先級 PIR 匹配（不應有加權）
        weight_medium = risk_calculation_service.weight_calculator.calculate_pir_match_weight(
            sample_threat, [medium_priority_pir]
        )
        assert weight_medium == 0.0, f"中優先級 PIR 加權應為 0.0，實際為 {weight_medium}"

        # 測試無 PIR 匹配
        weight_none = risk_calculation_service.weight_calculator.calculate_pir_match_weight(
            sample_threat, []
        )
        assert weight_none == 0.0, f"無 PIR 匹配加權應為 0.0，實際為 {weight_none}"

    def test_cisa_kev_weight_calculation(
        self, risk_calculation_service: RiskCalculationService, sample_threat
    ):
        """
        測試 CISA KEV 加權計算
        
        在 CISA KEV 清單中，返回 0.5
        否則返回 0.0
        """
        # 測試 CISA KEV 威脅
        weight_kev = risk_calculation_service.weight_calculator.calculate_cisa_kev_weight(
            sample_threat, threat_feed_name="CISA KEV"
        )
        assert weight_kev == 0.5, f"CISA KEV 加權應為 0.5，實際為 {weight_kev}"

        # 測試非 CISA KEV 威脅
        weight_non_kev = risk_calculation_service.weight_calculator.calculate_cisa_kev_weight(
            sample_threat, threat_feed_name="NVD"
        )
        assert weight_non_kev == 0.0, f"非 CISA KEV 加權應為 0.0，實際為 {weight_non_kev}"

    def test_final_risk_score_calculation(
        self,
        risk_calculation_service: RiskCalculationService,
        sample_threat,
        sample_assets,
    ):
        """
        測試最終風險分數計算
        
        公式：final_score = base_score * asset_weight + asset_count_weight + pir_weight + cisa_kev_weight
        上限：10.0
        """
        # 測試案例 1: 基礎計算
        risk_assessment = risk_calculation_service.calculate_risk(
            threat=sample_threat,
            associated_assets=[sample_assets[1]],  # 中-中資產
            threat_asset_association_id="test-association",
            pirs=[],
            threat_feed_name="NVD",
        )

        # 驗證計算公式
        base_score = 7.5
        asset_weight = 1.0  # 中-中
        asset_count_weight = 0.1  # 1 個資產
        pir_weight = 0.0
        cisa_kev_weight = 0.0

        expected_score = base_score * asset_weight + asset_count_weight + pir_weight + cisa_kev_weight
        expected_score = min(10.0, max(0.0, expected_score))

        assert abs(risk_assessment.final_risk_score - expected_score) < 0.1, (
            f"最終風險分數計算錯誤: 預期 {expected_score}, 實際 {risk_assessment.final_risk_score}"
        )

        # 測試案例 2: 上限測試（超過 10.0）
        high_cvss_threat = Threat.create(
            id="test-threat-high",
            threat_feed_id="test-feed",
            title="High CVSS Threat",
            cve_id="CVE-2020-99999",
            cvss_base_score=9.5,
        )

        risk_assessment_high = risk_calculation_service.calculate_risk(
            threat=high_cvss_threat,
            associated_assets=[sample_assets[0]],  # 高-高資產
            threat_asset_association_id="test-association",
            pirs=[],
            threat_feed_name="CISA KEV",
        )

        assert risk_assessment_high.final_risk_score <= 10.0, (
            f"最終風險分數應不超過 10.0，實際為 {risk_assessment_high.final_risk_score}"
        )

    def test_risk_level_classification(
        self, risk_calculation_service: RiskCalculationService
    ):
        """
        測試風險等級分類
        
        Critical: >= 9.0
        High: >= 7.0 and < 9.0
        Medium: >= 4.0 and < 7.0
        Low: < 4.0
        """
        test_cases = [
            {"score": 9.5, "expected": "Critical"},
            {"score": 9.0, "expected": "Critical"},
            {"score": 8.5, "expected": "High"},
            {"score": 7.0, "expected": "High"},
            {"score": 5.5, "expected": "Medium"},
            {"score": 4.0, "expected": "Medium"},
            {"score": 3.5, "expected": "Low"},
            {"score": 0.0, "expected": "Low"},
        ]

        for case in test_cases:
            level = risk_calculation_service.risk_classifier.classify(case["score"])
            assert level == case["expected"], (
                f"風險等級分類錯誤: 分數 {case['score']}, 預期 {case['expected']}, 實際 {level}"
            )

    def test_boundary_values(self, risk_calculation_service: RiskCalculationService):
        """
        測試邊界值處理
        """
        # 測試最小風險分數（0.0）
        low_threat = Threat.create(
            id="test-threat-low",
            threat_feed_id="test-feed",
            title="Low CVSS Threat",
            cve_id="CVE-2020-00001",
            cvss_base_score=0.1,
        )

        low_asset = Asset.create(
            id="test-asset-low",
            name="Low Asset",
            asset_type="Server",
            data_sensitivity=DataSensitivity.LOW,
            business_criticality=BusinessCriticality.LOW,
        )

        risk_assessment_low = risk_calculation_service.calculate_risk(
            threat=low_threat,
            associated_assets=[low_asset],
            threat_asset_association_id="test-association",
            pirs=[],
            threat_feed_name="NVD",
        )

        assert risk_assessment_low.final_risk_score >= 0.0, (
            f"風險分數應 >= 0.0，實際為 {risk_assessment_low.final_risk_score}"
        )

        # 測試最大風險分數（10.0）
        high_threat = Threat.create(
            id="test-threat-high",
            threat_feed_id="test-feed",
            title="High CVSS Threat",
            cve_id="CVE-2020-99999",
            cvss_base_score=10.0,
        )

        high_asset = Asset.create(
            id="test-asset-high",
            name="High Asset",
            asset_type="Server",
            data_sensitivity=DataSensitivity.HIGH,
            business_criticality=BusinessCriticality.HIGH,
        )

        # 建立多個資產以增加加權
        many_assets = [high_asset] * 100

        risk_assessment_high = risk_calculation_service.calculate_risk(
            threat=high_threat,
            associated_assets=many_assets,
            threat_asset_association_id="test-association",
            pirs=[],
            threat_feed_name="CISA KEV",
        )

        assert risk_assessment_high.final_risk_score <= 10.0, (
            f"風險分數應 <= 10.0，實際為 {risk_assessment_high.final_risk_score}"
        )

    def test_comprehensive_scenario(
        self,
        risk_calculation_service: RiskCalculationService,
        sample_threat,
        sample_assets,
    ):
        """
        測試綜合場景
        
        包含所有加權因子的完整計算
        """
        # 建立高優先級 PIR
        high_priority_pir = PIR.create(
            id="pir-high",
            name="High Priority PIR",
            description="Test PIR",
            priority=PIRPriority.HIGH,
            conditions=[
                PIRCondition(
                    field="product_name",
                    operator="contains",
                    value="Apache",
                )
            ],
        )

        # 計算風險評估
        risk_assessment = risk_calculation_service.calculate_risk(
            threat=sample_threat,
            associated_assets=sample_assets,
            threat_asset_association_id="test-association",
            pirs=[high_priority_pir],
            threat_feed_name="CISA KEV",
        )

        # 驗證所有字段
        assert risk_assessment.base_cvss_score == 7.5
        assert risk_assessment.affected_asset_count == 3
        assert risk_assessment.pir_match_weight == 0.3
        assert risk_assessment.cisa_kev_weight == 0.5
        assert risk_assessment.final_risk_score <= 10.0
        assert risk_assessment.final_risk_score >= 0.0
        assert risk_assessment.risk_level in ["Critical", "High", "Medium", "Low"]
        assert risk_assessment.calculation_details is not None

        # 驗證計算詳情包含所有必要字段
        details = risk_assessment.calculation_details
        assert "base_cvss_score" in details
        assert "asset_importance_weight" in details
        assert "affected_asset_count" in details
        assert "asset_count_weight" in details
        assert "pir_match_weight" in details
        assert "cisa_kev_weight" in details
        assert "final_risk_score" in details
        assert "risk_level" in details
        assert "calculation_formula" in details

