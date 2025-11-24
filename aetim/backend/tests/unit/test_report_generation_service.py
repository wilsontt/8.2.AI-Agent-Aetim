"""
報告生成服務單元測試

測試報告生成服務的功能。
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from reporting_notification.domain.domain_services.report_generation_service import (
    ReportGenerationService,
    WeeklyReportData,
)
from reporting_notification.domain.value_objects.report_type import ReportType
from reporting_notification.domain.value_objects.file_format import FileFormat
from threat_intelligence.domain.aggregates.threat import Threat, ThreatProduct
from threat_intelligence.domain.value_objects.threat_severity import ThreatSeverity
from threat_intelligence.domain.value_objects.threat_status import ThreatStatus
from analysis_assessment.domain.aggregates.risk_assessment import RiskAssessment


class TestReportGenerationService:
    """測試報告生成服務"""

    @pytest.fixture
    def mock_threat_repository(self):
        """建立模擬威脅 Repository"""
        repository = AsyncMock()
        return repository

    @pytest.fixture
    def mock_risk_assessment_repository(self):
        """建立模擬風險評估 Repository"""
        repository = AsyncMock()
        return repository

    @pytest.fixture
    def mock_asset_repository(self):
        """建立模擬資產 Repository"""
        repository = AsyncMock()
        return repository

    @pytest.fixture
    def report_generation_service(
        self,
        mock_threat_repository,
        mock_risk_assessment_repository,
        mock_asset_repository,
    ):
        """建立報告生成服務"""
        return ReportGenerationService(
            threat_repository=mock_threat_repository,
            risk_assessment_repository=mock_risk_assessment_repository,
            asset_repository=mock_asset_repository,
        )

    @pytest.fixture
    def sample_threats(self):
        """建立範例威脅"""
        threats = []
        for i in range(5):
            threat = Threat.create(
                id=f"threat-{i}",
                threat_feed_id="feed-1",
                title=f"Threat {i}",
                cve_id=f"CVE-2025-{i:04d}",
                cvss_base_score=7.5 + i * 0.3,
                collected_at=datetime(2025, 1, 20 + i),
                products=[
                    ThreatProduct(
                        id=f"product-{i}",
                        product_name="Apache HTTP Server",
                        product_version="2.4.41",
                    )
                ],
            )
            threats.append(threat)
        return threats

    @pytest.fixture
    def sample_risk_assessments(self):
        """建立範例風險評估"""
        assessments = []
        for i in range(5):
            assessment = RiskAssessment.create(
                threat_id=f"threat-{i}",
                threat_asset_association_id=f"association-{i}",
                base_cvss_score=7.5 + i * 0.3,
                asset_importance_weight=1.0,
                affected_asset_count=i + 1,
                asset_count_weight=0.1 * (i + 1),
                final_risk_score=7.5 + i * 0.3 + 0.1 * (i + 1),
                risk_level="High" if i < 2 else "Critical",
            )
            assessments.append(assessment)
        return assessments

    @pytest.mark.asyncio
    async def test_generate_ciso_weekly_report(
        self,
        report_generation_service: ReportGenerationService,
        mock_threat_repository,
        mock_risk_assessment_repository,
        sample_threats,
        sample_risk_assessments,
    ):
        """測試生成 CISO 週報"""
        # 設定模擬行為
        period_start = datetime(2025, 1, 20)
        period_end = datetime(2025, 1, 27)

        mock_threat_repository.get_all.return_value = sample_threats

        # 模擬風險評估查詢
        async def mock_get_by_threat_id(threat_id: str):
            threat_index = int(threat_id.split("-")[1])
            if threat_index < len(sample_risk_assessments):
                return sample_risk_assessments[threat_index]
            return None

        mock_risk_assessment_repository.get_by_threat_id = AsyncMock(
            side_effect=mock_get_by_threat_id
        )

        # 生成報告
        report = await report_generation_service.generate_ciso_weekly_report(
            period_start=period_start,
            period_end=period_end,
            file_format=FileFormat.HTML,
        )

        # 驗證結果
        assert report is not None
        assert report.report_type == ReportType.CISO_WEEKLY
        assert report.file_format == FileFormat.HTML
        assert report.period_start == period_start
        assert report.period_end == period_end
        assert "CISO Weekly Report" in report.title

    @pytest.mark.asyncio
    async def test_collect_weekly_data(
        self,
        report_generation_service: ReportGenerationService,
        mock_threat_repository,
        mock_risk_assessment_repository,
        sample_threats,
        sample_risk_assessments,
    ):
        """測試收集週報資料"""
        period_start = datetime(2025, 1, 20)
        period_end = datetime(2025, 1, 27)

        mock_threat_repository.get_all.return_value = sample_threats

        # 模擬風險評估查詢
        async def mock_get_by_threat_id(threat_id: str):
            threat_index = int(threat_id.split("-")[1])
            if threat_index < len(sample_risk_assessments):
                return sample_risk_assessments[threat_index]
            return None

        mock_risk_assessment_repository.get_by_threat_id = AsyncMock(
            side_effect=mock_get_by_threat_id
        )

        # 收集資料
        report_data = await report_generation_service._collect_weekly_data(
            period_start, period_end
        )

        # 驗證結果
        assert report_data.total_threats == 5
        assert report_data.period_start == period_start
        assert report_data.period_end == period_end

    @pytest.mark.asyncio
    async def test_calculate_risk_trend(
        self,
        report_generation_service: ReportGenerationService,
        mock_threat_repository,
        mock_risk_assessment_repository,
    ):
        """測試計算風險趨勢"""
        period_start = datetime(2025, 1, 20)
        period_end = datetime(2025, 1, 27)

        # 本週威脅
        this_week_threats = [
            Threat.create(
                id=f"threat-{i}",
                threat_feed_id="feed-1",
                title=f"Threat {i}",
                collected_at=datetime(2025, 1, 20 + i),
            )
            for i in range(3)
        ]

        # 上週威脅
        last_week_threats = [
            Threat.create(
                id=f"last-threat-{i}",
                threat_feed_id="feed-1",
                title=f"Last Threat {i}",
                collected_at=datetime(2025, 1, 13 + i),
            )
            for i in range(2)
        ]

        # 模擬威脅查詢
        async def mock_get_all(*args, **kwargs):
            # 根據時間過濾
            all_threats = this_week_threats + last_week_threats
            return all_threats

        mock_threat_repository.get_all = AsyncMock(side_effect=mock_get_all)

        # 計算趨勢
        trend = await report_generation_service._calculate_risk_trend(
            period_start, period_end
        )

        # 驗證結果
        assert "this_week" in trend
        assert "last_week" in trend
        assert "threat_count_change" in trend
        assert "risk_score_change" in trend

    @pytest.mark.asyncio
    async def test_generate_html_content(
        self, report_generation_service: ReportGenerationService
    ):
        """測試生成 HTML 內容"""
        report_data = WeeklyReportData(
            period_start=datetime(2025, 1, 20),
            period_end=datetime(2025, 1, 27),
            total_threats=10,
            critical_threats=3,
            critical_threat_list=[
                {
                    "threat_id": "threat-1",
                    "cve_id": "CVE-2025-0001",
                    "title": "Test Threat",
                    "risk_score": 9.0,
                    "risk_level": "Critical",
                    "affected_asset_count": 5,
                }
            ],
            affected_assets_by_type={"Server": 10, "Workstation": 5},
            affected_assets_by_importance={"High-High": 3, "Medium-Medium": 7},
            risk_trend={
                "this_week": {"threat_count": 10, "avg_risk_score": 7.5},
                "last_week": {"threat_count": 8, "avg_risk_score": 7.0},
                "threat_count_change": 2,
                "risk_score_change": 0.5,
                "threat_count_trend": "上升",
                "risk_score_trend": "上升",
            },
        )

        html_content = report_generation_service._generate_html_content(report_data)

        # 驗證 HTML 內容
        assert "<html" in html_content
        assert "CISO 週報" in html_content
        assert "10" in html_content  # 總威脅數
        assert "3" in html_content  # 嚴重威脅數
        assert "CVE-2025-0001" in html_content

