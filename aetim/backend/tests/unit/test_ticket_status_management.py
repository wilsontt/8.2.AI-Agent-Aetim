"""
工單狀態管理單元測試

測試工單狀態更新功能，包括狀態轉換規則驗證、領域事件發布。
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from reporting_notification.domain.aggregates.report import Report
from reporting_notification.domain.value_objects.report_type import ReportType
from reporting_notification.domain.value_objects.file_format import FileFormat
from reporting_notification.domain.value_objects.ticket_status import TicketStatus
from reporting_notification.domain.domain_events.ticket_status_updated_event import (
    TicketStatusUpdatedEvent,
)
from reporting_notification.application.services.report_service import ReportService


class TestReportTicketStatus:
    """測試 Report 聚合根的工單狀態管理"""

    def test_update_ticket_status_pending_to_in_progress(self):
        """測試從待處理轉換到處理中"""
        report = Report.create(
            report_type=ReportType.IT_TICKET,
            title="IT 工單 - CVE-2025-0001",
            file_path="reports/2025/202501/ticket.txt",
            file_format=FileFormat.TEXT,
            metadata={"ticket_status": TicketStatus.PENDING.value},
        )
        report.ticket_status = TicketStatus.PENDING

        report.update_ticket_status(TicketStatus.IN_PROGRESS)

        assert report.ticket_status == TicketStatus.IN_PROGRESS
        assert report.metadata["ticket_status"] == TicketStatus.IN_PROGRESS.value

        # 驗證領域事件
        events = report.get_domain_events()
        assert len(events) == 2  # ReportGeneratedEvent + TicketStatusUpdatedEvent
        status_event = events[1]
        assert isinstance(status_event, TicketStatusUpdatedEvent)
        assert status_event.old_status == TicketStatus.PENDING
        assert status_event.new_status == TicketStatus.IN_PROGRESS

    def test_update_ticket_status_pending_to_closed(self):
        """測試從待處理轉換到已關閉"""
        report = Report.create(
            report_type=ReportType.IT_TICKET,
            title="IT 工單 - CVE-2025-0001",
            file_path="reports/2025/202501/ticket.txt",
            file_format=FileFormat.TEXT,
        )
        report.ticket_status = TicketStatus.PENDING

        report.update_ticket_status(TicketStatus.CLOSED)

        assert report.ticket_status == TicketStatus.CLOSED

    def test_update_ticket_status_in_progress_to_completed(self):
        """測試從處理中轉換到已完成"""
        report = Report.create(
            report_type=ReportType.IT_TICKET,
            title="IT 工單 - CVE-2025-0001",
            file_path="reports/2025/202501/ticket.txt",
            file_format=FileFormat.TEXT,
        )
        report.ticket_status = TicketStatus.IN_PROGRESS

        report.update_ticket_status(TicketStatus.COMPLETED)

        assert report.ticket_status == TicketStatus.COMPLETED

    def test_update_ticket_status_completed_to_closed(self):
        """測試從已完成轉換到已關閉"""
        report = Report.create(
            report_type=ReportType.IT_TICKET,
            title="IT 工單 - CVE-2025-0001",
            file_path="reports/2025/202501/ticket.txt",
            file_format=FileFormat.TEXT,
        )
        report.ticket_status = TicketStatus.COMPLETED

        report.update_ticket_status(TicketStatus.CLOSED)

        assert report.ticket_status == TicketStatus.CLOSED

    def test_update_ticket_status_invalid_transition(self):
        """測試無效的狀態轉換"""
        report = Report.create(
            report_type=ReportType.IT_TICKET,
            title="IT 工單 - CVE-2025-0001",
            file_path="reports/2025/202501/ticket.txt",
            file_format=FileFormat.TEXT,
        )
        report.ticket_status = TicketStatus.PENDING

        # 待處理不能直接轉換到已完成
        with pytest.raises(ValueError, match="無法從狀態"):
            report.update_ticket_status(TicketStatus.COMPLETED)

    def test_update_ticket_status_closed_immutable(self):
        """測試已關閉狀態不可變更"""
        report = Report.create(
            report_type=ReportType.IT_TICKET,
            title="IT 工單 - CVE-2025-0001",
            file_path="reports/2025/202501/ticket.txt",
            file_format=FileFormat.TEXT,
        )
        report.ticket_status = TicketStatus.CLOSED

        # 已關閉不能轉換到任何狀態
        with pytest.raises(ValueError, match="無法從狀態"):
            report.update_ticket_status(TicketStatus.IN_PROGRESS)

    def test_update_ticket_status_not_it_ticket(self):
        """測試非 IT_Ticket 類型不能更新狀態"""
        report = Report.create(
            report_type=ReportType.CISO_WEEKLY,
            title="CISO Weekly Report",
            file_path="reports/2025/202501/ciso_report.html",
            file_format=FileFormat.HTML,
        )

        with pytest.raises(ValueError, match="只有 IT 工單才能更新狀態"):
            report.update_ticket_status(TicketStatus.IN_PROGRESS)

    def test_update_ticket_status_default_pending(self):
        """測試預設狀態為待處理"""
        report = Report.create(
            report_type=ReportType.IT_TICKET,
            title="IT 工單 - CVE-2025-0001",
            file_path="reports/2025/202501/ticket.txt",
            file_format=FileFormat.TEXT,
        )
        # ticket_status 為 None

        # 更新狀態時，會將 None 視為 PENDING
        report.update_ticket_status(TicketStatus.IN_PROGRESS)

        assert report.ticket_status == TicketStatus.IN_PROGRESS


class TestReportServiceTicketStatus:
    """測試 ReportService 的工單狀態管理"""

    @pytest.fixture
    def mock_report_repository(self):
        """建立模擬報告 Repository"""
        repository = MagicMock()
        repository.get_by_id = AsyncMock()
        repository._save_to_database = AsyncMock()
        return repository

    @pytest.fixture
    def mock_report_generation_service(self):
        """建立模擬報告生成服務"""
        service = MagicMock()
        return service

    @pytest.fixture
    def mock_ai_summary_service(self):
        """建立模擬 AI 摘要服務"""
        service = MagicMock()
        return service

    @pytest.fixture
    def mock_threat_asset_association_repository(self):
        """建立模擬威脅資產關聯 Repository"""
        repository = MagicMock()
        return repository

    @pytest.fixture
    def mock_asset_repository(self):
        """建立模擬資產 Repository"""
        repository = MagicMock()
        return repository

    @pytest.fixture
    def mock_audit_log_service(self):
        """建立模擬稽核日誌服務"""
        service = MagicMock()
        service.log_action = AsyncMock(return_value="audit-log-id")
        return service

    @pytest.fixture
    def report_service(
        self,
        mock_report_generation_service,
        mock_report_repository,
        mock_ai_summary_service,
        mock_threat_asset_association_repository,
        mock_asset_repository,
        mock_audit_log_service,
    ):
        """建立報告服務"""
        return ReportService(
            report_generation_service=mock_report_generation_service,
            report_repository=mock_report_repository,
            ai_summary_service=mock_ai_summary_service,
            threat_asset_association_repository=mock_threat_asset_association_repository,
            asset_repository=mock_asset_repository,
            audit_log_service=mock_audit_log_service,
        )

    @pytest.fixture
    def sample_ticket_report(self):
        """建立範例工單報告"""
        report = Report.create(
            report_type=ReportType.IT_TICKET,
            title="IT 工單 - CVE-2025-0001",
            file_path="reports/2025/202501/ticket.txt",
            file_format=FileFormat.TEXT,
        )
        report.ticket_status = TicketStatus.PENDING
        return report

    @pytest.mark.asyncio
    async def test_update_ticket_status_success(
        self,
        report_service: ReportService,
        mock_report_repository,
        sample_ticket_report: Report,
        mock_audit_log_service,
    ):
        """測試成功更新工單狀態"""
        mock_report_repository.get_by_id = AsyncMock(return_value=sample_ticket_report)

        result = await report_service.update_ticket_status(
            ticket_id=sample_ticket_report.id,
            new_status=TicketStatus.IN_PROGRESS,
            user_id="user-1",
            ip_address="10.0.0.1",
            user_agent="Test Agent",
        )

        assert result.ticket_status == TicketStatus.IN_PROGRESS
        mock_report_repository._save_to_database.assert_called_once()

        # 驗證稽核日誌
        mock_audit_log_service.log_action.assert_called_once()
        call_args = mock_audit_log_service.log_action.call_args
        assert call_args.kwargs["user_id"] == "user-1"
        assert call_args.kwargs["action"] == "UPDATE"
        assert call_args.kwargs["resource_type"] == "IT_Ticket"
        assert call_args.kwargs["details"]["old_status"] == TicketStatus.PENDING.value
        assert call_args.kwargs["details"]["new_status"] == TicketStatus.IN_PROGRESS.value

    @pytest.mark.asyncio
    async def test_update_ticket_status_not_found(
        self,
        report_service: ReportService,
        mock_report_repository,
    ):
        """測試更新不存在的工單狀態"""
        mock_report_repository.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="找不到工單"):
            await report_service.update_ticket_status(
                ticket_id="non-existent-id",
                new_status=TicketStatus.IN_PROGRESS,
            )

    @pytest.mark.asyncio
    async def test_update_ticket_status_invalid_transition(
        self,
        report_service: ReportService,
        mock_report_repository,
        sample_ticket_report: Report,
    ):
        """測試無效的狀態轉換"""
        sample_ticket_report.ticket_status = TicketStatus.PENDING
        mock_report_repository.get_by_id = AsyncMock(return_value=sample_ticket_report)

        # 待處理不能直接轉換到已完成
        with pytest.raises(ValueError, match="無法從狀態"):
            await report_service.update_ticket_status(
                ticket_id=sample_ticket_report.id,
                new_status=TicketStatus.COMPLETED,
            )

