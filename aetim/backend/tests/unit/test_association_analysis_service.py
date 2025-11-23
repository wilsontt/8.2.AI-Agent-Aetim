"""
關聯分析服務單元測試

測試關聯分析服務的各種比對邏輯。
"""

import pytest
from datetime import datetime

from analysis_assessment.domain.domain_services.association_analysis_service import (
    AssociationAnalysisService,
    AssociationResult,
    MatchType,
)
from threat_intelligence.domain.aggregates.threat import Threat
from threat_intelligence.domain.entities.threat_product import ThreatProduct
from threat_intelligence.domain.value_objects.threat_severity import ThreatSeverity
from asset_management.domain.aggregates.asset import Asset
from asset_management.domain.entities.asset_product import AssetProduct
from asset_management.domain.value_objects.data_sensitivity import DataSensitivity
from asset_management.domain.value_objects.business_criticality import BusinessCriticality


class TestAssociationAnalysisService:
    """關聯分析服務測試"""
    
    @pytest.fixture
    def service(self):
        """建立關聯分析服務實例"""
        return AssociationAnalysisService()
    
    @pytest.fixture
    def sample_threat(self):
        """建立範例威脅"""
        threat = Threat.create(
            threat_feed_id="feed-123",
            title="Test Threat",
            description="Test threat description",
            cve_id="CVE-2024-12345",
            cvss_base_score=7.5,
            severity=ThreatSeverity("High"),
        )
        return threat
    
    @pytest.fixture
    def sample_asset(self):
        """建立範例資產"""
        asset = Asset.create(
            host_name="test-server",
            operating_system="Windows Server 2019",
            running_applications="IIS, SQL Server",
            owner="admin",
            data_sensitivity="High",
            business_criticality="High",
        )
        return asset
    
    def test_exact_product_exact_version_match(self, service, sample_threat, sample_asset):
        """測試精確產品名稱 + 精確版本匹配"""
        # 添加威脅產品
        threat_product = ThreatProduct(
            id="tp-1",
            product_name="Microsoft SQL Server",
            product_version="2019",
        )
        sample_threat.products.append(threat_product)
        
        # 添加資產產品
        asset_product = AssetProduct(
            id="ap-1",
            product_name="Microsoft SQL Server",
            product_version="2019",
        )
        sample_asset.products.append(asset_product)
        
        # 執行分析
        results = service.analyze(sample_threat, [sample_asset])
        
        # 驗證結果
        assert len(results) == 1
        assert results[0].threat_id == sample_threat.id
        assert results[0].asset_id == sample_asset.id
        assert results[0].match_type == MatchType.EXACT_PRODUCT_EXACT_VERSION
        assert results[0].confidence >= 0.9
    
    def test_exact_product_version_range_match(self, service, sample_threat, sample_asset):
        """測試精確產品名稱 + 版本範圍匹配"""
        # 添加威脅產品（版本範圍）
        threat_product = ThreatProduct(
            id="tp-1",
            product_name="Microsoft SQL Server",
            product_version="2019.x",
        )
        sample_threat.products.append(threat_product)
        
        # 添加資產產品
        asset_product = AssetProduct(
            id="ap-1",
            product_name="Microsoft SQL Server",
            product_version="2019.1",
        )
        sample_asset.products.append(asset_product)
        
        # 執行分析
        results = service.analyze(sample_threat, [sample_asset])
        
        # 驗證結果
        assert len(results) == 1
        assert results[0].match_type == MatchType.EXACT_PRODUCT_VERSION_RANGE
        assert results[0].confidence >= 0.8
    
    def test_exact_product_major_version_match(self, service, sample_threat, sample_asset):
        """測試精確產品名稱 + 主版本匹配"""
        # 添加威脅產品（主版本）
        threat_product = ThreatProduct(
            id="tp-1",
            product_name="Microsoft SQL Server",
            product_version="2019",
        )
        sample_threat.products.append(threat_product)
        
        # 添加資產產品（不同小版本）
        asset_product = AssetProduct(
            id="ap-1",
            product_name="Microsoft SQL Server",
            product_version="2019.1",
        )
        sample_asset.products.append(asset_product)
        
        # 執行分析
        results = service.analyze(sample_threat, [sample_asset])
        
        # 驗證結果（應該匹配主版本）
        assert len(results) == 1
        assert results[0].match_type == MatchType.EXACT_PRODUCT_MAJOR_VERSION
        assert results[0].confidence >= 0.7
    
    def test_exact_product_no_version_match(self, service, sample_threat, sample_asset):
        """測試精確產品名稱 + 無版本匹配"""
        # 添加威脅產品（無版本）
        threat_product = ThreatProduct(
            id="tp-1",
            product_name="Microsoft SQL Server",
            product_version=None,
        )
        sample_threat.products.append(threat_product)
        
        # 添加資產產品
        asset_product = AssetProduct(
            id="ap-1",
            product_name="Microsoft SQL Server",
            product_version="2019",
        )
        sample_asset.products.append(asset_product)
        
        # 執行分析
        results = service.analyze(sample_threat, [sample_asset])
        
        # 驗證結果
        assert len(results) == 1
        assert results[0].match_type == MatchType.EXACT_PRODUCT_NO_VERSION
        assert results[0].confidence >= 0.6
    
    def test_fuzzy_product_exact_version_match(self, service, sample_threat, sample_asset):
        """測試模糊產品名稱 + 精確版本匹配"""
        # 添加威脅產品
        threat_product = ThreatProduct(
            id="tp-1",
            product_name="SQL Server",
            product_version="2019",
        )
        sample_threat.products.append(threat_product)
        
        # 添加資產產品（完整產品名稱）
        asset_product = AssetProduct(
            id="ap-1",
            product_name="Microsoft SQL Server",
            product_version="2019",
        )
        sample_asset.products.append(asset_product)
        
        # 執行分析
        results = service.analyze(sample_threat, [sample_asset])
        
        # 驗證結果
        assert len(results) == 1
        assert results[0].match_type == MatchType.FUZZY_PRODUCT_EXACT_VERSION
        assert results[0].confidence >= 0.7
    
    def test_fuzzy_product_version_range_match(self, service, sample_threat, sample_asset):
        """測試模糊產品名稱 + 版本範圍匹配"""
        # 添加威脅產品
        threat_product = ThreatProduct(
            id="tp-1",
            product_name="SQL Server",
            product_version="2019.x",
        )
        sample_threat.products.append(threat_product)
        
        # 添加資產產品
        asset_product = AssetProduct(
            id="ap-1",
            product_name="Microsoft SQL Server",
            product_version="2019.1",
        )
        sample_asset.products.append(asset_product)
        
        # 執行分析
        results = service.analyze(sample_threat, [sample_asset])
        
        # 驗證結果
        assert len(results) == 1
        assert results[0].match_type == MatchType.FUZZY_PRODUCT_VERSION_RANGE
        assert results[0].confidence >= 0.6
    
    def test_os_match(self, service, sample_threat, sample_asset):
        """測試作業系統匹配"""
        # 添加威脅產品（作業系統）
        threat_product = ThreatProduct(
            id="tp-1",
            product_name="Windows Server",
            product_type="Operating System",
        )
        sample_threat.products.append(threat_product)
        
        # 資產作業系統為 "Windows Server 2019"
        
        # 執行分析
        results = service.analyze(sample_threat, [sample_asset])
        
        # 驗證結果
        assert len(results) == 1
        assert results[0].match_type == MatchType.OS_MATCH
        assert results[0].os_match is True
        assert results[0].confidence >= 0.8
    
    def test_no_match(self, service, sample_threat, sample_asset):
        """測試無匹配情況"""
        # 添加威脅產品
        threat_product = ThreatProduct(
            id="tp-1",
            product_name="Linux",
            product_version="Ubuntu 20.04",
        )
        sample_threat.products.append(threat_product)
        
        # 資產產品為 Windows Server
        
        # 執行分析
        results = service.analyze(sample_threat, [sample_asset])
        
        # 驗證結果
        assert len(results) == 0
    
    def test_multiple_assets(self, service, sample_threat):
        """測試多個資產的分析"""
        # 添加威脅產品
        threat_product = ThreatProduct(
            id="tp-1",
            product_name="Microsoft SQL Server",
            product_version="2019",
        )
        sample_threat.products.append(threat_product)
        
        # 建立多個資產
        asset1 = Asset.create(
            host_name="server-1",
            operating_system="Windows Server 2019",
            running_applications="SQL Server",
            owner="admin",
            data_sensitivity="High",
            business_criticality="High",
        )
        asset1_product = AssetProduct(
            id="ap-1",
            product_name="Microsoft SQL Server",
            product_version="2019",
        )
        asset1.products.append(asset1_product)
        
        asset2 = Asset.create(
            host_name="server-2",
            operating_system="Linux",
            running_applications="MySQL",
            owner="admin",
            data_sensitivity="Medium",
            business_criticality="Medium",
        )
        
        # 執行分析
        results = service.analyze(sample_threat, [asset1, asset2])
        
        # 驗證結果（只有 asset1 匹配）
        assert len(results) == 1
        assert results[0].asset_id == asset1.id
    
    def test_product_name_normalization(self, service):
        """測試產品名稱標準化"""
        # 測試各種產品名稱變體
        test_cases = [
            ("MS SQL Server", "microsoft sql server"),
            ("mssql", "microsoft sql server"),
            ("SQL Server", "microsoft sql server"),
            ("Windows Server 2019", "windows server"),
            ("Win Server", "windows server"),
        ]
        
        for input_name, expected_normalized in test_cases:
            normalized = service._normalize_product_name(input_name)
            assert normalized == expected_normalized, f"Failed for {input_name}"
    
    def test_version_normalization(self, service):
        """測試版本標準化"""
        # 測試各種版本格式
        test_cases = [
            ("v1.0", "1.0"),
            ("version 2.0", "2.0"),
            ("3.0.1", "3.0.1"),
            ("  4.0  ", "4.0"),
        ]
        
        for input_version, expected_normalized in test_cases:
            normalized = service._normalize_version(input_version)
            assert normalized == expected_normalized, f"Failed for {input_version}"
    
    def test_version_range_matching(self, service):
        """測試版本範圍匹配"""
        # 測試版本範圍匹配
        test_cases = [
            ("7.0.x", "7.0.1", True),
            ("7.0.x", "7.0.2", True),
            ("7.0.x", "7.1.0", False),  # 不匹配，因為主版本不同
            ("7.0.x", "8.0.1", False),  # 不匹配
        ]
        
        for threat_version, asset_version, should_match in test_cases:
            result = service._match_version(threat_version, asset_version)
            assert result["is_match"] == should_match, (
                f"Failed for {threat_version} vs {asset_version}"
            )
    
    def test_major_version_matching(self, service):
        """測試主版本匹配"""
        # 測試主版本匹配
        test_cases = [
            ("7", "7.0", True),
            ("7", "7.1", True),
            ("7", "7.2.1", True),
            ("7", "8.0", False),  # 不匹配
        ]
        
        for threat_version, asset_version, should_match in test_cases:
            result = service._match_version(threat_version, asset_version)
            assert result["is_match"] == should_match, (
                f"Failed for {threat_version} vs {asset_version}"
            )
    
    def test_product_similarity_calculation(self, service):
        """測試產品名稱相似度計算"""
        # 測試相似度計算
        similarity = service._calculate_product_similarity(
            "microsoft sql server",
            "sql server",
        )
        
        # 相似度應該 >= 0.8（閾值）
        assert similarity >= 0.8
    
    def test_confidence_calculation(self, service):
        """測試信心分數計算"""
        # 測試各種匹配類型的信心分數
        test_cases = [
            (True, MatchType.EXACT_PRODUCT_EXACT_VERSION, 1.0),
            (True, MatchType.EXACT_PRODUCT_VERSION_RANGE, 0.9),
            (True, MatchType.EXACT_PRODUCT_MAJOR_VERSION, 0.8),
            (True, MatchType.EXACT_PRODUCT_NO_VERSION, 0.7),
            (False, MatchType.FUZZY_PRODUCT_EXACT_VERSION, 0.9),
            (False, MatchType.FUZZY_PRODUCT_VERSION_RANGE, 0.8),
            (False, MatchType.FUZZY_PRODUCT_MAJOR_VERSION, 0.7),
            (False, MatchType.FUZZY_PRODUCT_NO_VERSION, 0.6),
        ]
        
        for is_exact, match_type, expected_min_confidence in test_cases:
            confidence = service._calculate_confidence(
                is_exact_product=is_exact,
                version_match_type=match_type,
                product_similarity=0.85 if not is_exact else None,
            )
            assert confidence >= expected_min_confidence * 0.9, (
                f"Failed for {match_type}: expected >= {expected_min_confidence * 0.9}, got {confidence}"
            )

