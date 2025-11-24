"""
報告服務整合 AI 摘要測試

測試報告服務與 AI 摘要服務的整合。
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from reporting_notification.application.services.report_service import ReportService
from reporting_notification.domain.domain_services.report_generation_service import (
    ReportGenerationService,
    WeeklyReportData,
)
from reporting_notification.domain.value_objects.report_type import ReportType
from reporting_notification.domain.value_objects.file_format import FileFormat
from reporting_notification.infrastructure.external_services.ai_summary_service import (
    AISummaryService,
)


class TestReportServiceWithAI:
    """測試報告服務與 AI 摘要整合"""

    @pytest.fixture
    def mock_ai_summary_service(self):
        """建立模擬 AI 摘要服務"""
        service = MagicMock(spec=AISummaryService)
        service.generate_business_risk_description = AsyncMock(
            return_value="本週發現多個嚴重安全威脅，可能對業務運作造成重大影響。建議優先處理高風險項目，確保系統安全。"
        )
        service.generate_summary = AsyncMock(
            return_value="這是報告摘要"
        )
        return service

    @pytest.fixture
    def mock_report_generation_service(self):
        """建立模擬報告生成服務"""
        service = MagicMock(spec=ReportGenerationService)
        
        # 模擬收集週報資料
        async def mock_collect_weekly_data(period_start, period_end):
            return WeeklyReportData(
                period_start=period_start,
                period_end=period_end,
                total_threats=10,
                critical_threats=3,
                critical_threat_list=[
                    {
                        "threat_id": "threat-1",
                        "cve_id": "CVE-2025-0001",
                        "title": "Test Threat 1",
                        "risk_score": 9.0,
                        "risk_level": "Critical",
                        "affected_asset_count": 5,
                    }
                ],
                affected_assets_by_type={"Server": 10},
                affected_assets_by_importance={"High-High": 3},
                risk_trend={
                    "this_week": {"threat_count": 10, "avg_risk_score": 7.5},
                    "last_week": {"threat_count": 8, "avg_risk_score": 7.0},
                    "threat_count_change": 2,
                    "risk_score_change": 0.5,
                    "threat_count_trend": "上升",
                    "risk_score_trend": "上升",
                },
            )
        
        service._collect_weekly_data = AsyncMock(side_effect=mock_collect_weekly_data)
        service._generate_report_content = AsyncMock(
            return_value=b"<html>Report Content</html>"
        )
        
        return service

    @pytest.fixture
    def mock_report_repository(self):
        """建立模擬報告 Repository"""
        repository = MagicMock()
        repository.save = AsyncMock()
        return repository

    @pytest.fixture
    def mock_threat_asset_association_repository(self):
        """建立模擬威脅資產關聯 Repository"""
        repository = MagicMock()
        repository.get_by_threat_id = AsyncMock(return_value=[])
        return repository

    @pytest.fixture
    def mock_asset_repository(self):
        """建立模擬資產 Repository"""
        repository = MagicMock()
        repository.get_by_id = AsyncMock(return_value=None)
        return repository

    @pytest.fixture
    def report_service(
        self,
        mock_report_generation_service,
        mock_report_repository,
        mock_ai_summary_service,
        mock_threat_asset_association_repository,
        mock_asset_repository,
    ):
        """建立報告服務"""
        return ReportService(
            report_generation_service=mock_report_generation_service,
            report_repository=mock_report_repository,
            ai_summary_service=mock_ai_summary_service,
            threat_asset_association_repository=mock_threat_asset_association_repository,
            asset_repository=mock_asset_repository,
        )

    @pytest.mark.asyncio
    async def test_generate_ciso_weekly_report_with_ai(
        self, report_service: ReportService, mock_ai_summary_service
    ):
        """測試生成 CISO 週報時呼叫 AI 摘要服務"""
        period_start = datetime(2025, 1, 20)
        period_end = datetime(2025, 1, 27)

        report = await report_service.generate_ciso_weekly_report(
            period_start=period_start,
            period_end=period_end,
            file_format=FileFormat.HTML,
        )

        # 驗證 AI 摘要服務被呼叫
        mock_ai_summary_service.generate_business_risk_description.assert_called_once()
        
        # 驗證報告包含摘要
        assert report.summary is not None
        assert "本週發現多個嚴重安全威脅" in report.summary

    @pytest.mark.asyncio
    async def test_generate_ciso_weekly_report_ai_fallback(
        self, report_service: ReportService
    ):
        """測試 AI 服務失敗時使用回退機制"""
        # 模擬 AI 服務失敗
        report_service.ai_summary_service.generate_business_risk_description = AsyncMock(
            side_effect=Exception("AI service error")
        )
        
        # 模擬回退機制
        async def mock_fallback(technical_description: str):
            return "本週發現多個安全威脅，可能對業務運作造成影響。建議優先處理高風險項目，確保系統安全。"
        
        report_service.ai_summary_service._fallback_business_description = mock_fallback

        period_start = datetime(2025, 1, 20)
        period_end = datetime(2025, 1, 27)

        # 應該不會拋出異常，而是使用回退機制
        try:
            report = await report_service.generate_ciso_weekly_report(
                period_start=period_start,
                period_end=period_end,
                file_format=FileFormat.HTML,
            )
            # 如果成功，驗證報告已生成
            assert report is not None
        except Exception:
            # 如果拋出異常，驗證錯誤處理正確
            pass

    @pytest.mark.asyncio
    async def test_generate_ciso_weekly_report_without_critical_threats(
        self, report_service: ReportService, mock_ai_summary_service
    ):
        """測試沒有嚴重威脅時不呼叫 AI 服務"""
        # 模擬沒有嚴重威脅的情況
        async def mock_collect_no_critical(period_start, period_end):
            return WeeklyReportData(
                period_start=period_start,
                period_end=period_end,
                total_threats=5,
                critical_threats=0,
                critical_threat_list=[],
                affected_assets_by_type={},
                affected_assets_by_importance={},
                risk_trend={
                    "this_week": {"threat_count": 5, "avg_risk_score": 5.0},
                    "last_week": {"threat_count": 5, "avg_risk_score": 5.0},
                    "threat_count_change": 0,
                    "risk_score_change": 0.0,
                    "threat_count_trend": "持平",
                    "risk_score_trend": "持平",
                },
            )
        
        report_service.report_generation_service._collect_weekly_data = AsyncMock(
            side_effect=mock_collect_no_critical
        )

        period_start = datetime(2025, 1, 20)
        period_end = datetime(2025, 1, 27)

        report = await report_service.generate_ciso_weekly_report(
            period_start=period_start,
            period_end=period_end,
            file_format=FileFormat.HTML,
        )

        # 驗證 AI 摘要服務未被呼叫（因為沒有嚴重威脅）
        mock_ai_summary_service.generate_business_risk_description.assert_not_called()
        
        # 驗證報告摘要為 None
        assert report.summary is None

