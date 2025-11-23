"""
威脅-資產關聯服務單元測試

測試威脅-資產關聯的建立和管理功能。
"""

import pytest
import sys
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from analysis_assessment.application.services.threat_asset_association_service import (
    ThreatAssetAssociationService,
)
from analysis_assessment.domain.domain_services.association_analysis_service import (
    AssociationResult,
    MatchType,
)
from threat_intelligence.domain.aggregates.threat import Threat
from threat_intelligence.domain.value_objects.threat_severity import ThreatSeverity
from threat_intelligence.domain.value_objects.threat_status import ThreatStatus
from asset_management.domain.aggregates.asset import Asset
from asset_management.domain.value_objects.data_sensitivity import DataSensitivity
from asset_management.domain.value_objects.business_criticality import BusinessCriticality


class TestThreatAssetAssociationService:
    """威脅-資產關聯服務測試"""
    
    @pytest.fixture
    def mock_threat_repository(self):
        """建立模擬的威脅 Repository"""
        repository = MagicMock()
        repository.get_by_id = AsyncMock()
        repository.save = AsyncMock()
        return repository
    
    @pytest.fixture
    def mock_asset_repository(self):
        """建立模擬的資產 Repository"""
        repository = MagicMock()
        repository.get_all = AsyncMock(return_value=([], 0))
        return repository
    
    @pytest.fixture
    def mock_association_repository(self):
        """建立模擬的關聯 Repository"""
        repository = MagicMock()
        repository.save_association = AsyncMock()
        repository.get_by_threat_id = AsyncMock(return_value=[])
        repository.get_by_asset_id = AsyncMock(return_value=[])
        repository.delete_association = AsyncMock()
        return repository
    
    @pytest.fixture
    def mock_association_analysis_service(self):
        """建立模擬的關聯分析服務"""
        service = MagicMock()
        service.analyze = MagicMock(return_value=[])
        return service
    
    @pytest.fixture
    def service(
        self,
        mock_threat_repository,
        mock_asset_repository,
        mock_association_repository,
        mock_association_analysis_service,
    ):
        """建立威脅-資產關聯服務實例"""
        return ThreatAssetAssociationService(
            threat_repository=mock_threat_repository,
            asset_repository=mock_asset_repository,
            association_repository=mock_association_repository,
            association_analysis_service=mock_association_analysis_service,
        )
    
    @pytest.fixture
    def sample_threat(self):
        """建立範例威脅"""
        return Threat.create(
            threat_feed_id="feed-123",
            title="Test Threat",
            description="Test threat description",
            cve_id="CVE-2024-12345",
            cvss_base_score=7.5,
            severity=ThreatSeverity("High"),
        )
    
    @pytest.fixture
    def sample_association_results(self, sample_threat):
        """建立範例關聯分析結果"""
        return [
            AssociationResult(
                threat_id=sample_threat.id,
                asset_id="asset-1",
                confidence=0.9,
                match_type=MatchType.EXACT_PRODUCT_EXACT_VERSION,
                matched_products=[
                    {
                        "threat_product": "Microsoft SQL Server",
                        "threat_version": "2019",
                        "asset_product": "Microsoft SQL Server",
                        "asset_version": "2019",
                    }
                ],
            ),
            AssociationResult(
                threat_id=sample_threat.id,
                asset_id="asset-2",
                confidence=0.8,
                match_type=MatchType.FUZZY_PRODUCT_EXACT_VERSION,
                matched_products=[
                    {
                        "threat_product": "SQL Server",
                        "threat_version": "2019",
                        "asset_product": "Microsoft SQL Server",
                        "asset_version": "2019",
                    }
                ],
            ),
        ]
    
    @pytest.mark.asyncio
    async def test_create_associations_success(
        self,
        service,
        mock_threat_repository,
        mock_association_repository,
        sample_threat,
        sample_association_results,
    ):
        """測試建立關聯：成功"""
        # 設定模擬
        mock_threat_repository.get_by_id.return_value = sample_threat
        
        # 執行
        result = await service.create_associations(
            sample_threat.id,
            sample_association_results,
        )
        
        # 驗證
        assert result["success"] is True
        assert result["associations_created"] == 2
        assert len(result["errors"]) == 0
        
        # 驗證 Repository 被呼叫
        assert mock_association_repository.save_association.call_count == 2
        assert mock_threat_repository.save.call_count == 2  # 一次更新為 Analyzing，一次更新為 Processed
    
    @pytest.mark.asyncio
    async def test_create_associations_threat_not_found(
        self,
        service,
        mock_threat_repository,
        sample_threat,
        sample_association_results,
    ):
        """測試建立關聯：威脅不存在"""
        # 設定模擬
        mock_threat_repository.get_by_id.return_value = None
        
        # 執行
        result = await service.create_associations(
            sample_threat.id,
            sample_association_results,
        )
        
        # 驗證
        assert result["success"] is False
        assert result["associations_created"] == 0
        assert len(result["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_create_associations_updates_threat_status(
        self,
        service,
        mock_threat_repository,
        mock_association_repository,
        sample_threat,
        sample_association_results,
    ):
        """測試建立關聯：更新威脅狀態（AC-010-4）"""
        # 設定模擬
        mock_threat_repository.get_by_id.return_value = sample_threat
        
        # 執行
        await service.create_associations(
            sample_threat.id,
            sample_association_results,
        )
        
        # 驗證威脅狀態被更新
        assert sample_threat.status.value == "Processed"
        assert mock_threat_repository.save.call_count == 2
    
    @pytest.mark.asyncio
    async def test_create_associations_with_errors(
        self,
        service,
        mock_threat_repository,
        mock_association_repository,
        sample_threat,
        sample_association_results,
    ):
        """測試建立關聯：部分失敗"""
        # 設定模擬
        mock_threat_repository.get_by_id.return_value = sample_threat
        # 第一個關聯成功，第二個失敗
        mock_association_repository.save_association.side_effect = [
            None,
            Exception("Database error"),
        ]
        
        # 執行
        result = await service.create_associations(
            sample_threat.id,
            sample_association_results,
        )
        
        # 驗證
        assert result["success"] is True  # 部分成功仍視為成功
        assert result["associations_created"] == 1
        assert len(result["errors"]) == 1
    
    @pytest.mark.asyncio
    async def test_analyze_and_create_associations(
        self,
        service,
        mock_threat_repository,
        mock_asset_repository,
        mock_association_repository,
        mock_association_analysis_service,
        sample_threat,
        sample_association_results,
    ):
        """測試執行關聯分析並建立關聯"""
        # 設定模擬
        mock_threat_repository.get_by_id.return_value = sample_threat
        mock_asset_repository.get_all.return_value = ([], 0)
        mock_association_analysis_service.analyze.return_value = sample_association_results
        
        # 執行
        result = await service.analyze_and_create_associations(sample_threat.id)
        
        # 驗證
        assert result["success"] is True
        assert result["associations_created"] == 2
        assert mock_association_analysis_service.analyze.called
    
    @pytest.mark.asyncio
    async def test_update_associations(
        self,
        service,
        mock_threat_repository,
        mock_association_repository,
        sample_threat,
        sample_association_results,
    ):
        """測試更新關聯"""
        # 建立模擬的現有關聯
        from analysis_assessment.infrastructure.persistence.models import (
            ThreatAssetAssociation as ThreatAssetAssociationModel,
        )
        
        existing_assoc = MagicMock(spec=ThreatAssetAssociationModel)
        existing_assoc.asset_id = "asset-3"
        
        mock_association_repository.get_by_threat_id.return_value = [existing_assoc]
        mock_threat_repository.get_by_id.return_value = sample_threat
        
        # 執行
        result = await service.update_associations(
            sample_threat.id,
            sample_association_results,
        )
        
        # 驗證
        assert result["success"] is True
        assert result["associations_created"] == 2
        assert result["associations_deleted"] == 1
        assert mock_association_repository.delete_association.called
    
    @pytest.mark.asyncio
    async def test_get_associations_by_threat_id(
        self,
        service,
        mock_association_repository,
    ):
        """測試查詢威脅的所有關聯"""
        # 建立模擬的關聯記錄
        from analysis_assessment.infrastructure.persistence.models import (
            ThreatAssetAssociation as ThreatAssetAssociationModel,
        )
        
        assoc1 = MagicMock(spec=ThreatAssetAssociationModel)
        assoc1.id = "assoc-1"
        assoc1.threat_id = "threat-1"
        assoc1.asset_id = "asset-1"
        assoc1.match_confidence = 0.9
        assoc1.match_type = "exact_product_exact_version"
        assoc1.match_details = '{"matched_products": []}'
        assoc1.created_at = datetime(2024, 1, 1)
        
        mock_association_repository.get_by_threat_id.return_value = [assoc1]
        
        # 執行
        result = await service.get_associations_by_threat_id("threat-1")
        
        # 驗證
        assert len(result) == 1
        assert result[0]["threat_id"] == "threat-1"
        assert result[0]["asset_id"] == "asset-1"
        assert result[0]["match_confidence"] == 0.9
    
    @pytest.mark.asyncio
    async def test_get_associations_by_asset_id(
        self,
        service,
        mock_association_repository,
    ):
        """測試查詢資產的所有關聯"""
        # 建立模擬的關聯記錄
        from analysis_assessment.infrastructure.persistence.models import (
            ThreatAssetAssociation as ThreatAssetAssociationModel,
        )
        
        assoc1 = MagicMock(spec=ThreatAssetAssociationModel)
        assoc1.id = "assoc-1"
        assoc1.threat_id = "threat-1"
        assoc1.asset_id = "asset-1"
        assoc1.match_confidence = 0.9
        assoc1.match_type = "exact_product_exact_version"
        assoc1.match_details = '{"matched_products": []}'
        assoc1.created_at = datetime(2024, 1, 1)
        
        mock_association_repository.get_by_asset_id.return_value = [assoc1]
        
        # 執行
        result = await service.get_associations_by_asset_id("asset-1")
        
        # 驗證
        assert len(result) == 1
        assert result[0]["threat_id"] == "threat-1"
        assert result[0]["asset_id"] == "asset-1"
        assert result[0]["match_confidence"] == 0.9

