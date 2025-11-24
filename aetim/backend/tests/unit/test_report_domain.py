"""
報告領域模型單元測試

測試報告聚合根、值物件和領域事件。
"""

import pytest
from datetime import datetime
from reporting_notification.domain.aggregates.report import Report
from reporting_notification.domain.value_objects.report_type import ReportType
from reporting_notification.domain.value_objects.file_format import FileFormat
from reporting_notification.domain.domain_events.report_generated_event import (
    ReportGeneratedEvent,
)


class TestReportType:
    """測試報告類型值物件"""

    def test_report_type_enum(self):
        """測試報告類型枚舉值"""
        assert ReportType.CISO_WEEKLY == "CISO_Weekly"
        assert ReportType.IT_TICKET == "IT_Ticket"

    def test_report_type_from_string(self):
        """測試從字串建立報告類型"""
        assert ReportType.from_string("CISO_Weekly") == ReportType.CISO_WEEKLY
        assert ReportType.from_string("IT_Ticket") == ReportType.IT_TICKET

    def test_report_type_from_string_invalid(self):
        """測試無效的報告類型"""
        with pytest.raises(ValueError, match="無效的報告類型"):
            ReportType.from_string("InvalidType")


class TestFileFormat:
    """測試檔案格式值物件"""

    def test_file_format_enum(self):
        """測試檔案格式枚舉值"""
        assert FileFormat.HTML == "HTML"
        assert FileFormat.PDF == "PDF"
        assert FileFormat.TEXT == "TEXT"
        assert FileFormat.JSON == "JSON"

    def test_file_format_get_extension(self):
        """測試取得檔案副檔名"""
        assert FileFormat.HTML.get_file_extension() == ".html"
        assert FileFormat.PDF.get_file_extension() == ".pdf"
        assert FileFormat.TEXT.get_file_extension() == ".txt"
        assert FileFormat.JSON.get_file_extension() == ".json"


class TestReport:
    """測試報告聚合根"""

    def test_create_report(self):
        """測試建立報告"""
        report = Report.create(
            report_type=ReportType.CISO_WEEKLY,
            title="CISO Weekly Report 2025-01-27",
            file_path="reports/2025/202501/CISO_Weekly_Report_2025-01-27.html",
            file_format=FileFormat.HTML,
        )

        assert report.id is not None
        assert report.report_type == ReportType.CISO_WEEKLY
        assert report.title == "CISO Weekly Report 2025-01-27"
        assert report.file_path == "reports/2025/202501/CISO_Weekly_Report_2025-01-27.html"
        assert report.file_format == FileFormat.HTML
        assert report.generated_at is not None
        assert isinstance(report.generated_at, datetime)

    def test_create_report_with_period(self):
        """測試建立帶有期間的報告"""
        period_start = datetime(2025, 1, 20)
        period_end = datetime(2025, 1, 27)

        report = Report.create(
            report_type=ReportType.CISO_WEEKLY,
            title="CISO Weekly Report 2025-01-27",
            file_path="reports/2025/202501/CISO_Weekly_Report_2025-01-27.html",
            file_format=FileFormat.HTML,
            period_start=period_start,
            period_end=period_end,
        )

        assert report.period_start == period_start
        assert report.period_end == period_end

    def test_create_report_with_summary(self):
        """測試建立帶有摘要的報告"""
        summary = "本週發現 10 個嚴重威脅，建議立即處理。"

        report = Report.create(
            report_type=ReportType.CISO_WEEKLY,
            title="CISO Weekly Report 2025-01-27",
            file_path="reports/2025/202501/CISO_Weekly_Report_2025-01-27.html",
            file_format=FileFormat.HTML,
            summary=summary,
        )

        assert report.summary == summary

    def test_create_report_publishes_event(self):
        """測試建立報告時發布領域事件"""
        report = Report.create(
            report_type=ReportType.CISO_WEEKLY,
            title="CISO Weekly Report 2025-01-27",
            file_path="reports/2025/202501/CISO_Weekly_Report_2025-01-27.html",
            file_format=FileFormat.HTML,
        )

        events = report.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], ReportGeneratedEvent)
        assert events[0].report_id == report.id
        assert events[0].report_type == ReportType.CISO_WEEKLY

    def test_create_report_invalid_title(self):
        """測試建立報告時標題為空"""
        with pytest.raises(ValueError, match="報告標題不能為空"):
            Report.create(
                report_type=ReportType.CISO_WEEKLY,
                title="",
                file_path="reports/2025/202501/CISO_Weekly_Report_2025-01-27.html",
                file_format=FileFormat.HTML,
            )

    def test_create_report_invalid_file_path(self):
        """測試建立報告時檔案路徑為空"""
        with pytest.raises(ValueError, match="檔案路徑不能為空"):
            Report.create(
                report_type=ReportType.CISO_WEEKLY,
                title="CISO Weekly Report 2025-01-27",
                file_path="",
                file_format=FileFormat.HTML,
            )

    def test_set_summary(self):
        """測試設定摘要"""
        report = Report.create(
            report_type=ReportType.CISO_WEEKLY,
            title="CISO Weekly Report 2025-01-27",
            file_path="reports/2025/202501/CISO_Weekly_Report_2025-01-27.html",
            file_format=FileFormat.HTML,
        )

        summary = "本週發現 10 個嚴重威脅，建議立即處理。"
        report.set_summary(summary)

        assert report.summary == summary

    def test_set_summary_empty(self):
        """測試設定空摘要"""
        report = Report.create(
            report_type=ReportType.CISO_WEEKLY,
            title="CISO Weekly Report 2025-01-27",
            file_path="reports/2025/202501/CISO_Weekly_Report_2025-01-27.html",
            file_format=FileFormat.HTML,
        )

        with pytest.raises(ValueError, match="摘要不能為空"):
            report.set_summary("")

    def test_update_metadata(self):
        """測試更新元資料"""
        report = Report.create(
            report_type=ReportType.CISO_WEEKLY,
            title="CISO Weekly Report 2025-01-27",
            file_path="reports/2025/202501/CISO_Weekly_Report_2025-01-27.html",
            file_format=FileFormat.HTML,
        )

        metadata = {"threat_count": 10, "critical_threats": 3}
        report.update_metadata(metadata)

        assert report.metadata == metadata

    def test_update_metadata_merge(self):
        """測試合併元資料"""
        report = Report.create(
            report_type=ReportType.CISO_WEEKLY,
            title="CISO Weekly Report 2025-01-27",
            file_path="reports/2025/202501/CISO_Weekly_Report_2025-01-27.html",
            file_format=FileFormat.HTML,
            metadata={"threat_count": 10},
        )

        report.update_metadata({"critical_threats": 3})

        assert report.metadata["threat_count"] == 10
        assert report.metadata["critical_threats"] == 3

    def test_clear_domain_events(self):
        """測試清除領域事件"""
        report = Report.create(
            report_type=ReportType.CISO_WEEKLY,
            title="CISO Weekly Report 2025-01-27",
            file_path="reports/2025/202501/CISO_Weekly_Report_2025-01-27.html",
            file_format=FileFormat.HTML,
        )

        assert len(report.get_domain_events()) == 1

        report.clear_domain_events()

        assert len(report.get_domain_events()) == 0

