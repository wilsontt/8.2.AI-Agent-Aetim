"""
工單格式測試

測試工單格式（TEXT、JSON）的生成和內容完整性。
"""

import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

from reporting_notification.domain.domain_services.report_generation_service import (
    ReportGenerationService,
)
from reporting_notification.domain.value_objects.file_format import FileFormat
from reporting_notification.domain.value_objects.ticket_status import TicketStatus
from reporting_notification.infrastructure.services.template_renderer import TemplateRenderer
from threat_intelligence.domain.aggregates.threat import Threat
from analysis_assessment.domain.aggregates.risk_assessment import RiskAssessment


class TestTicketFormat:
    """測試工單格式"""

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
        return repository

    @pytest.fixture
    def mock_asset_repository(self):
        """建立模擬資產 Repository"""
        repository = MagicMock()
        return repository

    @pytest.fixture
    def mock_threat_asset_association_repository(self):
        """建立模擬威脅資產關聯 Repository"""
        repository = MagicMock()
        repository.get_by_threat_id = AsyncMock(return_value=[])
        return repository

    @pytest.fixture
    def template_renderer(self, tmp_path):
        """建立模板渲染服務"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        return TemplateRenderer(templates_dir=templates_dir)

    @pytest.fixture
    def report_generation_service(
        self,
        mock_threat_repository,
        mock_risk_assessment_repository,
        mock_asset_repository,
        mock_threat_asset_association_repository,
        template_renderer,
    ):
        """建立報告生成服務"""
        return ReportGenerationService(
            threat_repository=mock_threat_repository,
            risk_assessment_repository=mock_risk_assessment_repository,
            asset_repository=mock_asset_repository,
            threat_asset_association_repository=mock_threat_asset_association_repository,
            template_renderer=template_renderer,
        )

    @pytest.fixture
    def sample_threat(self):
        """建立範例威脅"""
        return Threat.create(
            threat_feed_id="feed-1",
            title="Test CVE Vulnerability",
            description="This is a test vulnerability description",
            cve_id="CVE-2025-0001",
            cvss_base_score=7.5,
            source_url="https://example.com/cve-2025-0001",
            published_date=datetime(2025, 1, 20),
        )

    @pytest.fixture
    def sample_risk_assessment(self):
        """建立範例風險評估"""
        return RiskAssessment.create(
            threat_id="threat-1",
            threat_asset_association_id="association-1",
            base_cvss_score=7.5,
            asset_importance_weight=1.5,
            affected_asset_count=3,
            asset_count_weight=0.3,
            final_risk_score=8.5,
            risk_level="Critical",
        )

    @pytest.fixture
    def sample_affected_assets(self):
        """建立範例受影響資產"""
        return [
            {
                "asset_id": "asset-1",
                "host_name": "Test Server 1",
                "ip_address": "10.0.0.1",
                "owner": "admin@example.com",
                "products": [
                    {"product_name": "Apache HTTP Server", "version": "2.4.0"},
                    {"product_name": "MySQL", "version": "8.0.0"},
                ],
                "operating_system": "Linux Ubuntu 20.04",
                "match_confidence": 0.95,
                "match_type": "Exact",
            },
            {
                "asset_id": "asset-2",
                "host_name": "Test Server 2",
                "ip_address": "10.0.0.2",
                "owner": "admin2@example.com",
                "products": [
                    {"product_name": "Apache HTTP Server", "version": "2.4.1"},
                ],
                "operating_system": "Linux CentOS 7",
                "match_confidence": 0.88,
                "match_type": "Fuzzy",
            },
        ]

    def test_generate_ticket_text_format_with_template(
        self,
        report_generation_service: ReportGenerationService,
        sample_threat: Threat,
        sample_risk_assessment: RiskAssessment,
        sample_affected_assets: list,
        template_renderer: TemplateRenderer,
        tmp_path,
    ):
        """測試使用模板生成 TEXT 格式工單內容（AC-017-2, AC-017-3）"""
        # 建立模板檔案
        template_file = tmp_path / "templates" / "it_ticket.txt"
        template_file.write_text("""IT 工單 - {{ ticket_data.cve_id or ticket_data.title }}

CVE 編號：{{ ticket_data.cve_id or "N/A" }}
標題：{{ ticket_data.title }}
描述：{{ ticket_data.description or "無描述" }}
風險分數：{{ ticket_data.final_risk_score|round(2) }}
風險等級：{{ ticket_data.risk_level }}
""")

        content = report_generation_service._generate_ticket_text(
            threat=sample_threat,
            risk_assessment=sample_risk_assessment,
            affected_assets=sample_affected_assets,
        )

        assert isinstance(content, str)
        assert "CVE-2025-0001" in content
        assert "Test CVE Vulnerability" in content
        assert "8.50" in content  # 風險分數
        assert "Critical" in content

    def test_generate_ticket_text_format_fallback(
        self,
        report_generation_service: ReportGenerationService,
        sample_threat: Threat,
        sample_risk_assessment: RiskAssessment,
        sample_affected_assets: list,
    ):
        """測試回退方法生成 TEXT 格式工單內容"""
        # 移除模板渲染服務
        report_generation_service.template_renderer = None

        content = report_generation_service._generate_ticket_text(
            threat=sample_threat,
            risk_assessment=sample_risk_assessment,
            affected_assets=sample_affected_assets,
        )

        assert isinstance(content, str)
        assert "CVE-2025-0001" in content
        assert "Test CVE Vulnerability" in content
        assert "8.50" in content
        assert "Critical" in content
        assert "Test Server 1" in content
        assert "10.0.0.1" in content
        assert "admin@example.com" in content
        assert "Apache HTTP Server" in content
        assert "2.4.0" in content

    def test_generate_ticket_text_format_includes_all_technical_info(
        self,
        report_generation_service: ReportGenerationService,
        sample_threat: Threat,
        sample_risk_assessment: RiskAssessment,
        sample_affected_assets: list,
    ):
        """測試 TEXT 格式包含所有技術資訊（AC-017-2）"""
        report_generation_service.template_renderer = None

        content = report_generation_service._generate_ticket_text(
            threat=sample_threat,
            risk_assessment=sample_risk_assessment,
            affected_assets=sample_affected_assets,
        )

        # 檢查 CVE 資訊
        assert "CVE-2025-0001" in content
        assert "Test CVE Vulnerability" in content
        assert "This is a test vulnerability description" in content

        # 檢查風險分數
        assert "7.50" in content  # CVSS 基礎分數
        assert "8.50" in content  # 最終風險分數
        assert "Critical" in content

        # 檢查受影響資產
        assert "Test Server 1" in content
        assert "10.0.0.1" in content
        assert "admin@example.com" in content
        assert "Apache HTTP Server" in content
        assert "2.4.0" in content
        assert "MySQL" in content
        assert "8.0.0" in content

        # 檢查修補建議
        assert "修補程式連結" in content
        assert "https://example.com/cve-2025-0001" in content

        # 檢查優先處理順序
        assert "優先處理順序" in content
        assert "高" in content  # 風險分數 >= 8.0

    def test_generate_ticket_json_format(
        self,
        report_generation_service: ReportGenerationService,
        sample_threat: Threat,
        sample_risk_assessment: RiskAssessment,
        sample_affected_assets: list,
    ):
        """測試生成 JSON 格式工單內容（AC-017-2, AC-017-3）"""
        content = report_generation_service._generate_ticket_json(
            threat=sample_threat,
            risk_assessment=sample_risk_assessment,
            affected_assets=sample_affected_assets,
        )

        assert isinstance(content, str)
        
        # 解析 JSON
        ticket_data = json.loads(content)
        
        # 檢查結構
        assert "ticket_title" in ticket_data
        assert "cve_info" in ticket_data
        assert "risk_scores" in ticket_data
        assert "affected_assets" in ticket_data
        assert "remediation" in ticket_data
        assert "priority" in ticket_data
        assert "ticket_status" in ticket_data
        assert "generated_at" in ticket_data

    def test_generate_ticket_json_format_includes_all_technical_info(
        self,
        report_generation_service: ReportGenerationService,
        sample_threat: Threat,
        sample_risk_assessment: RiskAssessment,
        sample_affected_assets: list,
    ):
        """測試 JSON 格式包含所有技術資訊（AC-017-2）"""
        content = report_generation_service._generate_ticket_json(
            threat=sample_threat,
            risk_assessment=sample_risk_assessment,
            affected_assets=sample_affected_assets,
        )

        ticket_data = json.loads(content)

        # 檢查 CVE 資訊
        assert ticket_data["cve_info"]["cve_id"] == "CVE-2025-0001"
        assert ticket_data["cve_info"]["title"] == "Test CVE Vulnerability"
        assert ticket_data["cve_info"]["description"] == "This is a test vulnerability description"
        assert ticket_data["cve_info"]["source_url"] == "https://example.com/cve-2025-0001"

        # 檢查風險分數
        assert ticket_data["risk_scores"]["cvss_base_score"] == 7.5
        assert ticket_data["risk_scores"]["final_risk_score"] == 8.5
        assert ticket_data["risk_scores"]["risk_level"] == "Critical"

        # 檢查受影響資產
        assert len(ticket_data["affected_assets"]) == 2
        assert ticket_data["affected_assets"][0]["host_name"] == "Test Server 1"
        assert ticket_data["affected_assets"][0]["ip_address"] == "10.0.0.1"
        assert ticket_data["affected_assets"][0]["owner"] == "admin@example.com"
        assert len(ticket_data["affected_assets"][0]["products"]) == 2
        assert ticket_data["affected_assets"][0]["products"][0]["product_name"] == "Apache HTTP Server"
        assert ticket_data["affected_assets"][0]["products"][0]["version"] == "2.4.0"

        # 檢查修補建議
        assert ticket_data["remediation"]["patch_url"] == "https://example.com/cve-2025-0001"
        assert "暫時緩解措施" in ticket_data["remediation"]["temporary_mitigation"]

        # 檢查優先處理順序
        assert ticket_data["priority"]["risk_score"] == 8.5
        assert ticket_data["priority"]["risk_level"] == "Critical"
        assert ticket_data["priority"]["priority_level"] == "高"

        # 檢查工單狀態
        assert ticket_data["ticket_status"] == TicketStatus.PENDING.value

    def test_generate_ticket_json_format_valid_json(
        self,
        report_generation_service: ReportGenerationService,
        sample_threat: Threat,
        sample_risk_assessment: RiskAssessment,
        sample_affected_assets: list,
    ):
        """測試 JSON 格式為有效的 JSON（AC-017-3）"""
        content = report_generation_service._generate_ticket_json(
            threat=sample_threat,
            risk_assessment=sample_risk_assessment,
            affected_assets=sample_affected_assets,
        )

        # 驗證 JSON 格式
        ticket_data = json.loads(content)
        assert isinstance(ticket_data, dict)

        # 驗證可以重新序列化
        json_str = json.dumps(ticket_data, ensure_ascii=False)
        assert isinstance(json_str, str)

    def test_generate_ticket_text_format_empty_assets(
        self,
        report_generation_service: ReportGenerationService,
        sample_threat: Threat,
        sample_risk_assessment: RiskAssessment,
    ):
        """測試 TEXT 格式處理無受影響資產的情況"""
        report_generation_service.template_renderer = None

        content = report_generation_service._generate_ticket_text(
            threat=sample_threat,
            risk_assessment=sample_risk_assessment,
            affected_assets=[],
        )

        assert "無受影響的資產" in content

    def test_generate_ticket_json_format_empty_assets(
        self,
        report_generation_service: ReportGenerationService,
        sample_threat: Threat,
        sample_risk_assessment: RiskAssessment,
    ):
        """測試 JSON 格式處理無受影響資產的情況"""
        content = report_generation_service._generate_ticket_json(
            threat=sample_threat,
            risk_assessment=sample_risk_assessment,
            affected_assets=[],
        )

        ticket_data = json.loads(content)
        assert ticket_data["affected_assets"] == []

    @pytest.mark.asyncio
    async def test_generate_ticket_content_text_format(
        self,
        report_generation_service: ReportGenerationService,
        sample_threat: Threat,
        sample_risk_assessment: RiskAssessment,
        sample_affected_assets: list,
    ):
        """測試生成工單內容（TEXT 格式）"""
        report_generation_service.template_renderer = None

        content = await report_generation_service._generate_ticket_content(
            threat=sample_threat,
            risk_assessment=sample_risk_assessment,
            affected_assets=sample_affected_assets,
            file_format=FileFormat.TEXT,
        )

        assert isinstance(content, str)
        assert "CVE-2025-0001" in content

    @pytest.mark.asyncio
    async def test_generate_ticket_content_json_format(
        self,
        report_generation_service: ReportGenerationService,
        sample_threat: Threat,
        sample_risk_assessment: RiskAssessment,
        sample_affected_assets: list,
    ):
        """測試生成工單內容（JSON 格式）"""
        content = await report_generation_service._generate_ticket_content(
            threat=sample_threat,
            risk_assessment=sample_risk_assessment,
            affected_assets=sample_affected_assets,
            file_format=FileFormat.JSON,
        )

        assert isinstance(content, str)
        ticket_data = json.loads(content)
        assert ticket_data["cve_info"]["cve_id"] == "CVE-2025-0001"

