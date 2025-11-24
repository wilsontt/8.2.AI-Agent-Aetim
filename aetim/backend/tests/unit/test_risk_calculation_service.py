"""
風險計算服務單元測試

測試風險計算服務的計算邏輯，符合 AC-012-1 至 AC-012-5 的要求。
"""

import pytest
from datetime import datetime

from analysis_assessment.domain.domain_services.risk_calculation_service import (
    RiskCalculationService,
)
from analysis_assessment.domain.aggregates.risk_assessment import RiskAssessment
from threat_intelligence.domain.aggregates.threat import Threat
from asset_management.domain.aggregates.asset import Asset
from analysis_assessment.domain.aggregates.pir import PIR
from analysis_assessment.domain.value_objects.pir_priority import PIRPriority


class TestRiskCalculationService:
    """風險計算服務測試"""
    
    @pytest.fixture
    def risk_calculation_service(self):
        """建立風險計算服務實例"""
        return RiskCalculationService()
    
    @pytest.fixture
    def sample_threat(self):
        """建立測試用的威脅"""
        return Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
            description="Test threat description",
            cve_id="CVE-2024-0001",
            cvss_base_score=7.5,
        )
    
    @pytest.fixture
    def sample_assets(self):
        """建立測試用的資產清單"""
        return [
            Asset.create(
                host_name="asset-1",
                operating_system="Windows Server 2016",
                running_applications="Test Application",
                owner="admin",
                data_sensitivity="高",
                business_criticality="高",
            ),
            Asset.create(
                host_name="asset-2",
                operating_system="Linux",
                running_applications="Test Application 2",
                owner="admin",
                data_sensitivity="中",
                business_criticality="中",
            ),
        ]
    
    @pytest.fixture
    def sample_pirs(self):
        """建立測試用的 PIR 清單"""
        return [
            PIR.create(
                name="PIR-1",
                description="Test PIR",
                priority="高",
                condition_type="CVE 編號",
                condition_value="CVE-2024-",
            ),
        ]
    
    def test_calculate_base_cvss_score(self, risk_calculation_service, sample_threat):
        """測試計算基礎 CVSS 分數（AC-012-1）"""
        base_score = risk_calculation_service._calculate_base_cvss_score(sample_threat)
        assert base_score == 7.5
    
    def test_calculate_base_cvss_score_without_cvss(
        self,
        risk_calculation_service,
    ):
        """測試計算基礎 CVSS 分數（沒有 CVSS 分數）"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
            cvss_base_score=None,
        )
        base_score = risk_calculation_service._calculate_base_cvss_score(threat)
        assert base_score == 0.0
    
    def test_calculate_asset_importance_weight(
        self,
        risk_calculation_service,
        sample_assets,
    ):
        """測試計算資產重要性加權（AC-012-2）"""
        weight = risk_calculation_service._calculate_asset_importance_weight(sample_assets)
        # 資產1：高(1.5) * 高(1.5) = 2.25
        # 資產2：中(1.0) * 中(1.0) = 1.0
        # 平均：(2.25 + 1.0) / 2 = 1.625
        assert weight == 1.625
    
    def test_calculate_asset_importance_weight_empty(
        self,
        risk_calculation_service,
    ):
        """測試計算資產重要性加權（空清單）"""
        weight = risk_calculation_service._calculate_asset_importance_weight([])
        assert weight == 1.0  # 預設權重
    
    def test_calculate_asset_count_weight(
        self,
        risk_calculation_service,
    ):
        """測試計算資產數量加權（AC-012-2）"""
        # 10 個資產：10 / 10.0 * 0.1 = 0.1
        weight = risk_calculation_service._calculate_asset_count_weight(10)
        assert weight == 0.1
        
        # 20 個資產：20 / 10.0 * 0.1 = 0.2
        weight = risk_calculation_service._calculate_asset_count_weight(20)
        assert weight == 0.2
        
        # 5 個資產：5 / 10.0 * 0.1 = 0.05
        weight = risk_calculation_service._calculate_asset_count_weight(5)
        assert weight == 0.05
    
    def test_check_pir_match(
        self,
        risk_calculation_service,
        sample_threat,
        sample_pirs,
    ):
        """測試檢查 PIR 符合度（AC-012-2）"""
        weight = risk_calculation_service._check_pir_match(sample_threat, sample_pirs)
        # 威脅的 CVE 是 "CVE-2024-0001"，符合 PIR 條件 "CVE-2024-"
        assert weight == 0.3  # 高優先級 PIR 加權
    
    def test_check_pir_match_no_match(
        self,
        risk_calculation_service,
        sample_threat,
    ):
        """測試檢查 PIR 符合度（不符合）"""
        pirs = [
            PIR.create(
                name="PIR-1",
                description="Test PIR",
                priority="高",
                condition_type="CVE 編號",
                condition_value="CVE-2023-",
            ),
        ]
        weight = risk_calculation_service._check_pir_match(sample_threat, pirs)
        assert weight == 0.0
    
    def test_check_pir_match_disabled(
        self,
        risk_calculation_service,
        sample_threat,
    ):
        """測試檢查 PIR 符合度（PIR 已停用）"""
        pir = PIR.create(
            name="PIR-1",
            description="Test PIR",
            priority="高",
            condition_type="CVE 編號",
            condition_value="CVE-2024-",
        )
        pir.disable()
        weight = risk_calculation_service._check_pir_match(sample_threat, [pir])
        assert weight == 0.0
    
    def test_check_cisa_kev(
        self,
        risk_calculation_service,
        sample_threat,
    ):
        """測試檢查 CISA KEV（AC-012-2）"""
        weight = risk_calculation_service._check_cisa_kev(
            sample_threat,
            threat_feed_name="CISA KEV",
        )
        assert weight == 0.5
    
    def test_check_cisa_kev_not_in_list(
        self,
        risk_calculation_service,
        sample_threat,
    ):
        """測試檢查 CISA KEV（不在清單中）"""
        weight = risk_calculation_service._check_cisa_kev(
            sample_threat,
            threat_feed_name="NVD",
        )
        assert weight == 0.0
    
    def test_calculate_risk_full(
        self,
        risk_calculation_service,
        sample_threat,
        sample_assets,
        sample_pirs,
    ):
        """測試完整風險計算（AC-012-1 至 AC-012-5）"""
        risk_assessment = risk_calculation_service.calculate_risk(
            threat=sample_threat,
            associated_assets=sample_assets,
            threat_asset_association_id="assoc-1",
            pirs=sample_pirs,
            threat_feed_name="CISA KEV",
        )
        
        # 驗證結果
        assert isinstance(risk_assessment, RiskAssessment)
        assert risk_assessment.threat_id == sample_threat.id
        assert risk_assessment.base_cvss_score == 7.5
        assert risk_assessment.affected_asset_count == 2
        assert risk_assessment.pir_match_weight == 0.3
        assert risk_assessment.cisa_kev_weight == 0.5
        
        # 驗證最終風險分數計算
        # base_score * asset_weight + asset_count_weight + pir_weight + cisa_kev_weight
        # = 7.5 * 1.625 + 0.02 + 0.3 + 0.5
        # = 12.1875 + 0.02 + 0.3 + 0.5
        # = 13.0075 -> 限制為 10.0
        assert risk_assessment.final_risk_score == 10.0
        assert risk_assessment.risk_level == "Critical"
        
        # 驗證計算詳情
        assert risk_assessment.calculation_details is not None
        assert "base_cvss_score" in risk_assessment.calculation_details
        assert "final_risk_score" in risk_assessment.calculation_details
        assert "risk_level" in risk_assessment.calculation_details
    
    def test_determine_risk_level(self):
        """測試決定風險等級（AC-012-4）"""
        assert RiskAssessment.determine_risk_level(9.0) == "Critical"
        assert RiskAssessment.determine_risk_level(8.0) == "Critical"
        assert RiskAssessment.determine_risk_level(7.0) == "High"
        assert RiskAssessment.determine_risk_level(6.0) == "High"
        assert RiskAssessment.determine_risk_level(5.0) == "Medium"
        assert RiskAssessment.determine_risk_level(4.0) == "Medium"
        assert RiskAssessment.determine_risk_level(3.0) == "Low"
        assert RiskAssessment.determine_risk_level(0.0) == "Low"
    
    def test_calculate_risk_score_clamping(
        self,
        risk_calculation_service,
    ):
        """測試風險分數限制在 0.0 - 10.0 範圍內（AC-012-3）"""
        threat = Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
            cvss_base_score=10.0,
        )
        # 使用高權重資產，讓最終分數超過 10.0
        assets = [
            Asset.create(
                host_name="asset-1",
                operating_system="Windows",
                running_applications="Test",
                owner="admin",
                data_sensitivity="高",
                business_criticality="高",
            ),
        ] * 100  # 100 個高權重資產
        
        risk_assessment = risk_calculation_service.calculate_risk(
            threat=threat,
            associated_assets=assets,
            threat_asset_association_id="assoc-1",
            pirs=[],
        )
        
        assert risk_assessment.final_risk_score <= 10.0
        assert risk_assessment.final_risk_score >= 0.0

