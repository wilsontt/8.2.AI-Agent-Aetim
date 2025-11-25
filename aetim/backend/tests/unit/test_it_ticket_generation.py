"""
IT 工單生成服務單元測試

測試 IT 工單生成功能，包括風險分數檢查、工單內容生成、格式支援。
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from reporting_notification.domain.domain_services.report_generation_service import (
    ReportGenerationService,
)
from reporting_notification.domain.value_objects.report_type import ReportType
from reporting_notification.domain.value_objects.file_format import FileFormat
from reporting_notification.domain.value_objects.ticket_status import TicketStatus
from threat_intelligence.domain.aggregates.threat import Threat
from threat_intelligence.domain.value_objects.threat_severity import ThreatSeverity
from threat_intelligence.domain.value_objects.threat_status import ThreatStatus
from analysis_assessment.domain.aggregates.risk_assessment import RiskAssessment
from asset_management.domain.aggregates.asset import Asset
from asset_management.domain.value_objects.data_sensitivity import DataSensitivity
from asset_management.domain.value_objects.business_criticality import BusinessCriticality
from threat_intelligence.infrastructure.persistence.threat_asset_association_repository import (
    ThreatAssetAssociationRepository,
)


class TestITTicketGeneration:
    """測試 IT 工單生成"""

    @pytest.fixture
    def mock_threat_repository(self):
        """建立模擬威脅 Repository"""
        repository = MagicMock()
        repository.get_by_id = AsyncMock()
        return repository

    @pytest.fixture
    def mock_risk_assessment_repository(self):
        """建立模擬風險評估 Repository"""
        repository = MagicMock()
        repository.get_by_id = AsyncMock()
        return repository

    @pytest.fixture
    def mock_asset_repository(self):
        """建立模擬資產 Repository"""
        repository = MagicMock()
        repository.get_by_id = AsyncMock()
        return repository

    @pytest.fixture
    def mock_threat_asset_association_repository(self):
        """建立模擬威脅資產關聯 Repository"""
        repository = MagicMock()
        repository.get_by_threat_id = AsyncMock(return_value=[])
        return repository

    @pytest.fixture
    def report_generation_service(
        self,
        mock_threat_repository,
        mock_risk_assessment_repository,
        mock_asset_repository,
        mock_threat_asset_association_repository,
    ):
        """建立報告生成服務"""
        return ReportGenerationService(
            threat_repository=mock_threat_repository,
            risk_assessment_repository=mock_risk_assessment_repository,
            asset_repository=mock_asset_repository,
            threat_asset_association_repository=mock_threat_asset_association_repository,
        )

    @pytest.fixture
    def sample_threat(self):
        """建立範例威脅"""
        return Threat.create(
            threat_feed_id="feed-1",
            title="Test CVE Vulnerability",
            description="This is a test vulnerability",
            cve_id="CVE-2025-0001",
            cvss_base_score=7.5,
            source_url="https://example.com/cve-2025-0001",
        )

    @pytest.fixture
    def sample_risk_assessment_high(self):
        """建立高風險評估（風險分數 >= 6.0）"""
        return RiskAssessment.create(
            threat_id="threat-1",
            threat_asset_association_id="association-1",
            base_cvss_score=7.5,
            asset_importance_weight=1.5,
            affected_asset_count=5,
            asset_count_weight=0.5,
            final_risk_score=8.5,
            risk_level="Critical",
        )

    @pytest.fixture
    def sample_risk_assessment_low(self):
        """建立低風險評估（風險分數 < 6.0）"""
        return RiskAssessment.create(
            threat_id="threat-2",
            threat_asset_association_id="association-2",
            base_cvss_score=4.0,
            asset_importance_weight=1.0,
            affected_asset_count=2,
            asset_count_weight=0.2,
            final_risk_score=4.5,
            risk_level="Medium",
        )

    @pytest.mark.asyncio
    async def test_generate_it_ticket_high_risk(
        self,
        report_generation_service: ReportGenerationService,
        mock_threat_repository,
        sample_threat: Threat,
        sample_risk_assessment_high: RiskAssessment,
    ):
        """測試生成高風險工單（AC-017-1）"""
        mock_threat_repository.get_by_id = AsyncMock(return_value=sample_threat)

        report = await report_generation_service.generate_it_ticket(
            risk_assessment=sample_risk_assessment_high,
            file_format=FileFormat.TEXT,
        )

        assert report is not None
        assert report.report_type == ReportType.IT_TICKET
        assert report.file_format == FileFormat.TEXT
        assert report.metadata is not None
        assert report.metadata["ticket_status"] == TicketStatus.PENDING.value
        assert report.metadata["risk_score"] == 8.5

    @pytest.mark.asyncio
    async def test_generate_it_ticket_low_risk_raises_error(
        self,
        report_generation_service: ReportGenerationService,
        sample_risk_assessment_low: RiskAssessment,
    ):
        """測試低風險不生成工單（AC-017-1）"""
        with pytest.raises(ValueError, match="風險分數.*低於 6.0"):
            await report_generation_service.generate_it_ticket(
                risk_assessment=sample_risk_assessment_low,
                file_format=FileFormat.TEXT,
            )

    @pytest.mark.asyncio
    async def test_generate_ticket_content_text_format(
        self,
        report_generation_service: ReportGenerationService,
        sample_threat: Threat,
        sample_risk_assessment_high: RiskAssessment,
    ):
        """測試生成 TEXT 格式工單內容（AC-017-2, AC-017-3）"""
        affected_assets = [
            {
                "asset_id": "asset-1",
                "host_name": "Test Server",
                "ip_address": "10.0.0.1",
                "owner": "admin@example.com",
                "products": [{"product_name": "Apache", "version": "2.4.0"}],
                "operating_system": "Linux",
                "match_confidence": 0.95,
                "match_type": "Exact",
            }
        ]

        content = await report_generation_service._generate_ticket_content(
            threat=sample_threat,
            risk_assessment=sample_risk_assessment_high,
            affected_assets=affected_assets,
            file_format=FileFormat.TEXT,
        )

        assert isinstance(content, str)
        assert "CVE-2025-0001" in content
        assert "Test CVE Vulnerability" in content
        assert "8.50" in content  # 風險分數
        assert "Critical" in content
        assert "Test Server" in content
        assert "10.0.0.1" in content
        assert "admin@example.com" in content
        assert "待處理" in content

    @pytest.mark.asyncio
    async def test_generate_ticket_content_json_format(
        self,
        report_generation_service: ReportGenerationService,
        sample_threat: Threat,
        sample_risk_assessment_high: RiskAssessment,
    ):
        """測試生成 JSON 格式工單內容（AC-017-2, AC-017-3）"""
        affected_assets = [
            {
                "asset_id": "asset-1",
                "host_name": "Test Server",
                "ip_address": "10.0.0.1",
                "owner": "admin@example.com",
                "products": [{"product_name": "Apache", "version": "2.4.0"}],
                "operating_system": "Linux",
                "match_confidence": 0.95,
                "match_type": "Exact",
            }
        ]

        content = await report_generation_service._generate_ticket_content(
            threat=sample_threat,
            risk_assessment=sample_risk_assessment_high,
            affected_assets=affected_assets,
            file_format=FileFormat.JSON,
        )

        assert isinstance(content, str)
        import json

        ticket_data = json.loads(content)
        assert ticket_data["cve_info"]["cve_id"] == "CVE-2025-0001"
        assert ticket_data["risk_scores"]["final_risk_score"] == 8.5
        assert ticket_data["risk_scores"]["risk_level"] == "Critical"
        assert len(ticket_data["affected_assets"]) == 1
        assert ticket_data["ticket_status"] == TicketStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_get_affected_assets_for_ticket(
        self,
        report_generation_service: ReportGenerationService,
        mock_threat_asset_association_repository,
        mock_asset_repository,
    ):
        """測試取得受影響的資產清單（AC-017-2）"""
        # 模擬關聯
        association_model = MagicMock()
        association_model.asset_id = "asset-1"
        association_model.match_confidence = 0.95
        association_model.match_type = "Exact"
        mock_threat_asset_association_repository.get_by_threat_id = AsyncMock(
            return_value=[association_model]
        )

        # 模擬資產
        asset = Asset.create(
            host_name="Test Server",
            operating_system="Linux",
            running_applications="Apache 2.4.0",
            owner="admin@example.com",
            data_sensitivity="高",
            business_criticality="高",
            ip="10.0.0.1",
        )
        asset.id = "asset-1"
        mock_asset_repository.get_by_id = AsyncMock(return_value=asset)

        affected_assets = await report_generation_service._get_affected_assets_for_ticket(
            "threat-1"
        )

        assert len(affected_assets) == 1
        assert affected_assets[0]["asset_id"] == "asset-1"
        assert affected_assets[0]["host_name"] == "Test Server"
        assert affected_assets[0]["ip_address"] == "10.0.0.1"
        assert affected_assets[0]["owner"] == "admin@example.com"

    @pytest.mark.asyncio
    async def test_ticket_status_set_to_pending(
        self,
        report_generation_service: ReportGenerationService,
        mock_threat_repository,
        sample_threat: Threat,
        sample_risk_assessment_high: RiskAssessment,
    ):
        """測試工單狀態設定為「待處理」（AC-017-5）"""
        mock_threat_repository.get_by_id = AsyncMock(return_value=sample_threat)

        report = await report_generation_service.generate_it_ticket(
            risk_assessment=sample_risk_assessment_high,
            file_format=FileFormat.TEXT,
        )

        assert report.metadata["ticket_status"] == TicketStatus.PENDING.value

