"""
加權因子計算服務單元測試

測試加權因子計算邏輯，符合 AC-012-2 的要求。
"""

import pytest

from analysis_assessment.domain.domain_services.weight_factor_calculator import (
    WeightFactorCalculator,
)
from threat_intelligence.domain.aggregates.threat import Threat
from asset_management.domain.aggregates.asset import Asset
from analysis_assessment.domain.aggregates.pir import PIR


class TestWeightFactorCalculator:
    """加權因子計算服務測試"""
    
    @pytest.fixture
    def calculator(self):
        """建立加權因子計算器實例"""
        return WeightFactorCalculator()
    
    @pytest.fixture
    def sample_threat(self):
        """建立測試用的威脅"""
        return Threat.create(
            threat_feed_id="feed-1",
            title="Test Threat",
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
    
    def test_calculate_asset_importance_weight(self, calculator, sample_assets):
        """測試計算資產重要性加權"""
        weight = calculator.calculate_asset_importance_weight(sample_assets)
        # 資產1：高(1.5) * 高(1.5) = 2.25
        # 資產2：中(1.0) * 中(1.0) = 1.0
        # 平均：(2.25 + 1.0) / 2 = 1.625
        assert weight == 1.625
    
    def test_calculate_asset_importance_weight_empty(self, calculator):
        """測試計算資產重要性加權（空清單）"""
        weight = calculator.calculate_asset_importance_weight([])
        assert weight == 1.0  # 預設權重
    
    def test_calculate_asset_count_weight(self, calculator):
        """測試計算資產數量加權"""
        # 10 個資產：10 / 10.0 * 0.1 = 0.1
        weight = calculator.calculate_asset_count_weight(10)
        assert weight == 0.1
        
        # 20 個資產：20 / 10.0 * 0.1 = 0.2
        weight = calculator.calculate_asset_count_weight(20)
        assert weight == 0.2
        
        # 5 個資產：5 / 10.0 * 0.1 = 0.05
        weight = calculator.calculate_asset_count_weight(5)
        assert weight == 0.05
    
    def test_calculate_asset_count_weight_zero(self, calculator):
        """測試計算資產數量加權（零個資產）"""
        weight = calculator.calculate_asset_count_weight(0)
        assert weight == 0.0
    
    def test_calculate_pir_match_weight(self, calculator, sample_threat, sample_pirs):
        """測試計算 PIR 符合度加權"""
        weight = calculator.calculate_pir_match_weight(sample_threat, sample_pirs)
        # 威脅的 CVE 是 "CVE-2024-0001"，符合 PIR 條件 "CVE-2024-"
        assert weight == 0.3  # 高優先級 PIR 加權
    
    def test_calculate_pir_match_weight_no_match(
        self,
        calculator,
        sample_threat,
    ):
        """測試計算 PIR 符合度加權（不符合）"""
        pirs = [
            PIR.create(
                name="PIR-1",
                description="Test PIR",
                priority="高",
                condition_type="CVE 編號",
                condition_value="CVE-2023-",
            ),
        ]
        weight = calculator.calculate_pir_match_weight(sample_threat, pirs)
        assert weight == 0.0
    
    def test_calculate_pir_match_weight_disabled(
        self,
        calculator,
        sample_threat,
    ):
        """測試計算 PIR 符合度加權（PIR 已停用）"""
        pir = PIR.create(
            name="PIR-1",
            description="Test PIR",
            priority="高",
            condition_type="CVE 編號",
            condition_value="CVE-2024-",
        )
        pir.disable()
        weight = calculator.calculate_pir_match_weight(sample_threat, [pir])
        assert weight == 0.0
    
    def test_calculate_cisa_kev_weight(self, calculator, sample_threat):
        """測試計算 CISA KEV 加權"""
        weight = calculator.calculate_cisa_kev_weight(
            sample_threat,
            threat_feed_name="CISA KEV",
        )
        assert weight == 0.5
    
    def test_calculate_cisa_kev_weight_not_in_list(
        self,
        calculator,
        sample_threat,
    ):
        """測試計算 CISA KEV 加權（不在清單中）"""
        weight = calculator.calculate_cisa_kev_weight(
            sample_threat,
            threat_feed_name="NVD",
        )
        assert weight == 0.0
    
    def test_calculate_cisa_kev_weight_no_feed_name(
        self,
        calculator,
        sample_threat,
    ):
        """測試計算 CISA KEV 加權（沒有來源名稱）"""
        weight = calculator.calculate_cisa_kev_weight(sample_threat, threat_feed_name=None)
        assert weight == 0.0

