"""
工單匯出功能整合測試

測試工單匯出功能，包括單一工單匯出、批次匯出、稽核日誌記錄。
"""

import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from reporting_notification.application.services.report_service import ReportService
from reporting_notification.domain.aggregates.report import Report
from reporting_notification.domain.value_objects.report_type import ReportType
from reporting_notification.domain.value_objects.file_format import FileFormat
from reporting_notification.domain.value_objects.ticket_status import TicketStatus


class TestTicketExport:
    """測試工單匯出功能"""

    @pytest.fixture
    def mock_report_repository(self):
        """建立模擬報告 Repository"""
        repository = MagicMock()
        repository.get_by_id = AsyncMock()
        repository.get_file_content = AsyncMock()
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
        return Report.create(
            report_type=ReportType.IT_TICKET,
            title="IT 工單 - CVE-2025-0001",
            file_path="reports/2025/202501/IT_Ticket_report-123.txt",
            file_format=FileFormat.TEXT,
            metadata={
                "ticket_status": TicketStatus.PENDING.value,
                "risk_score": 8.5,
            },
        )

    @pytest.mark.asyncio
    async def test_export_ticket_success(
        self,
        report_service: ReportService,
        mock_report_repository,
        sample_ticket_report: Report,
        mock_audit_log_service,
    ):
        """測試成功匯出單一工單（AC-017-4）"""
        # 設定模擬
        mock_report_repository.get_by_id = AsyncMock(return_value=sample_ticket_report)
        mock_report_repository.get_file_content = AsyncMock(
            return_value=b"IT Ticket Content"
        )

        # 匯出工單
        result = await report_service.export_ticket(
            ticket_id=sample_ticket_report.id,
            user_id="user-1",
            ip_address="10.0.0.1",
            user_agent="Test Agent",
        )

        # 驗證結果
        assert result["file_content"] == b"IT Ticket Content"
        assert result["file_name"] == f"IT_Ticket_{sample_ticket_report.id}.txt"
        assert result["content_type"] == "text/plain; charset=utf-8"

        # 驗證稽核日誌被記錄（AC-018-3）
        mock_audit_log_service.log_action.assert_called_once()
        call_args = mock_audit_log_service.log_action.call_args
        assert call_args.kwargs["user_id"] == "user-1"
        assert call_args.kwargs["action"] == "EXPORT"
        assert call_args.kwargs["resource_type"] == "IT_Ticket"
        assert call_args.kwargs["resource_id"] == sample_ticket_report.id

    @pytest.mark.asyncio
    async def test_export_ticket_not_found(
        self,
        report_service: ReportService,
        mock_report_repository,
    ):
        """測試匯出不存在的工單"""
        mock_report_repository.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="找不到工單"):
            await report_service.export_ticket(ticket_id="non-existent-id")

    @pytest.mark.asyncio
    async def test_export_ticket_not_it_ticket_type(
        self,
        report_service: ReportService,
        mock_report_repository,
    ):
        """測試匯出非 IT_Ticket 類型的報告"""
        ciso_report = Report.create(
            report_type=ReportType.CISO_WEEKLY,
            title="CISO Weekly Report",
            file_path="reports/2025/202501/ciso_report.html",
            file_format=FileFormat.HTML,
        )

        mock_report_repository.get_by_id = AsyncMock(return_value=ciso_report)

        with pytest.raises(ValueError, match="不是 IT 工單類型"):
            await report_service.export_ticket(ticket_id=ciso_report.id)

    @pytest.mark.asyncio
    async def test_export_ticket_json_format(
        self,
        report_service: ReportService,
        mock_report_repository,
        sample_ticket_report: Report,
    ):
        """測試匯出 JSON 格式工單"""
        sample_ticket_report.file_format = FileFormat.JSON
        mock_report_repository.get_by_id = AsyncMock(return_value=sample_ticket_report)
        mock_report_repository.get_file_content = AsyncMock(
            return_value=b'{"ticket_title": "Test"}'
        )

        result = await report_service.export_ticket(
            ticket_id=sample_ticket_report.id,
            file_format=FileFormat.JSON,
        )

        assert result["file_name"] == f"IT_Ticket_{sample_ticket_report.id}.json"
        assert result["content_type"] == "application/json; charset=utf-8"

    @pytest.mark.asyncio
    async def test_export_tickets_batch_success(
        self,
        report_service: ReportService,
        mock_report_repository,
        mock_audit_log_service,
    ):
        """測試成功批次匯出工單（AC-018-1, AC-018-2）"""
        # 建立多個工單報告
        ticket1 = Report.create(
            report_type=ReportType.IT_TICKET,
            title="IT 工單 - CVE-2025-0001",
            file_path="reports/2025/202501/ticket1.json",
            file_format=FileFormat.JSON,
        )
        ticket2 = Report.create(
            report_type=ReportType.IT_TICKET,
            title="IT 工單 - CVE-2025-0002",
            file_path="reports/2025/202501/ticket2.json",
            file_format=FileFormat.JSON,
        )

        # 設定模擬
        def mock_get_by_id(report_id: str):
            if report_id == ticket1.id:
                return ticket1
            elif report_id == ticket2.id:
                return ticket2
            return None

        mock_report_repository.get_by_id = AsyncMock(side_effect=mock_get_by_id)
        mock_report_repository.get_file_content = AsyncMock(
            side_effect=lambda report_id: (
                b'{"ticket_title": "Ticket 1"}' if report_id == ticket1.id
                else b'{"ticket_title": "Ticket 2"}'
            )
        )

        # 批次匯出工單
        result = await report_service.export_tickets_batch(
            ticket_ids=[ticket1.id, ticket2.id],
            user_id="user-1",
            ip_address="10.0.0.1",
            user_agent="Test Agent",
        )

        # 驗證結果
        assert result["file_name"].startswith("IT_Tickets_Batch_")
        assert result["file_name"].endswith(".json")
        assert result["content_type"] == "application/json; charset=utf-8"

        # 驗證 JSON 內容
        batch_data = json.loads(result["file_content"].decode('utf-8'))
        assert batch_data["export_type"] == "batch_tickets"
        assert batch_data["ticket_count"] == 2
        assert len(batch_data["tickets"]) == 2

        # 驗證稽核日誌被記錄（AC-018-3）
        mock_audit_log_service.log_action.assert_called_once()
        call_args = mock_audit_log_service.log_action.call_args
        assert call_args.kwargs["user_id"] == "user-1"
        assert call_args.kwargs["action"] == "EXPORT"
        assert call_args.kwargs["resource_type"] == "IT_Ticket"
        assert call_args.kwargs["resource_id"] is None  # 批次匯出沒有單一資源 ID
        assert call_args.kwargs["details"]["ticket_count"] == 2

    @pytest.mark.asyncio
    async def test_export_tickets_batch_empty_list(
        self,
        report_service: ReportService,
    ):
        """測試批次匯出空清單"""
        with pytest.raises(ValueError, match="工單 ID 清單不能為空"):
            await report_service.export_tickets_batch(ticket_ids=[])

    @pytest.mark.asyncio
    async def test_export_tickets_batch_no_valid_tickets(
        self,
        report_service: ReportService,
        mock_report_repository,
    ):
        """測試批次匯出沒有有效工單"""
        mock_report_repository.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="沒有可匯出的工單"):
            await report_service.export_tickets_batch(ticket_ids=["non-existent-1"])

    @pytest.mark.asyncio
    async def test_export_tickets_batch_mixed_formats(
        self,
        report_service: ReportService,
        mock_report_repository,
    ):
        """測試批次匯出混合格式的工單"""
        ticket_json = Report.create(
            report_type=ReportType.IT_TICKET,
            title="IT 工單 - JSON",
            file_path="reports/2025/202501/ticket_json.json",
            file_format=FileFormat.JSON,
        )
        ticket_text = Report.create(
            report_type=ReportType.IT_TICKET,
            title="IT 工單 - TEXT",
            file_path="reports/2025/202501/ticket_text.txt",
            file_format=FileFormat.TEXT,
        )

        def mock_get_by_id(report_id: str):
            if report_id == ticket_json.id:
                return ticket_json
            elif report_id == ticket_text.id:
                return ticket_text
            return None

        mock_report_repository.get_by_id = AsyncMock(side_effect=mock_get_by_id)
        mock_report_repository.get_file_content = AsyncMock(
            side_effect=lambda report_id: (
                b'{"ticket_title": "JSON Ticket"}' if report_id == ticket_json.id
                else b"TEXT Ticket Content"
            )
        )

        result = await report_service.export_tickets_batch(
            ticket_ids=[ticket_json.id, ticket_text.id]
        )

        # 驗證批次匯出 JSON 包含兩種格式的工單
        batch_data = json.loads(result["file_content"].decode('utf-8'))
        assert batch_data["ticket_count"] == 2
        assert len(batch_data["tickets"]) == 2

    @pytest.mark.asyncio
    async def test_export_ticket_audit_log_failure_handling(
        self,
        report_service: ReportService,
        mock_report_repository,
        sample_ticket_report: Report,
        mock_audit_log_service,
    ):
        """測試稽核日誌記錄失敗時的處理"""
        mock_report_repository.get_by_id = AsyncMock(return_value=sample_ticket_report)
        mock_report_repository.get_file_content = AsyncMock(
            return_value=b"IT Ticket Content"
        )
        mock_audit_log_service.log_action = AsyncMock(side_effect=Exception("Audit log error"))

        # 應該不會拋出異常，而是記錄警告
        result = await report_service.export_ticket(
            ticket_id=sample_ticket_report.id,
        )

        assert result["file_content"] == b"IT Ticket Content"

