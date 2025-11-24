"""
報告排程服務整合測試

測試報告排程服務的整合功能，包括排程管理、任務執行、狀態追蹤。
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from reporting_notification.application.services.report_schedule_service import (
    ReportScheduleService,
)
from reporting_notification.domain.aggregates.report_schedule import ReportSchedule
from reporting_notification.domain.value_objects.report_type import ReportType
from reporting_notification.domain.value_objects.file_format import FileFormat
from reporting_notification.application.services.report_service import ReportService


class TestReportScheduleService:
    """測試報告排程服務"""

    @pytest.fixture
    def mock_schedule_repository(self):
        """建立模擬排程 Repository"""
        repository = MagicMock()
        repository.get_all_enabled = AsyncMock(return_value=[])
        repository.get_by_id = AsyncMock(return_value=None)
        repository.save = AsyncMock()
        repository.delete = AsyncMock()
        return repository

    @pytest.fixture
    def mock_report_service(self):
        """建立模擬報告服務"""
        service = MagicMock(spec=ReportService)
        service.generate_ciso_weekly_report = AsyncMock()
        return service

    @pytest.fixture
    def report_schedule_service(
        self, mock_schedule_repository, mock_report_service
    ):
        """建立報告排程服務"""
        return ReportScheduleService(
            schedule_repository=mock_schedule_repository,
            report_service=mock_report_service,
        )

    @pytest.mark.asyncio
    async def test_create_schedule(
        self, report_schedule_service: ReportScheduleService, mock_schedule_repository
    ):
        """測試建立報告排程（AC-016-1）"""
        schedule = await report_schedule_service.create_schedule(
            report_type=ReportType.CISO_WEEKLY,
            cron_expression="0 9 * * 1",  # 每週一上午 9:00
            recipients=["ciso@example.com"],
            file_format="HTML",
            is_enabled=True,
        )

        assert schedule is not None
        assert schedule.report_type == ReportType.CISO_WEEKLY
        assert schedule.cron_expression == "0 9 * * 1"
        assert schedule.recipients == ["ciso@example.com"]
        assert schedule.is_enabled is True

        # 驗證 Repository 被呼叫
        mock_schedule_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_schedule(
        self, report_schedule_service: ReportScheduleService, mock_schedule_repository
    ):
        """測試新增排程任務"""
        schedule = ReportSchedule.create(
            report_type=ReportType.CISO_WEEKLY,
            cron_expression="0 9 * * 1",
            recipients=["ciso@example.com"],
            is_enabled=True,
        )

        await report_schedule_service.add_schedule(schedule)

        # 驗證排程器中有任務
        job_id = f"report_generation_{schedule.id}"
        job = report_schedule_service.scheduler.get_job(job_id)
        assert job is not None
        assert job.name == f"生成報告：{schedule.report_type.value}"

    @pytest.mark.asyncio
    async def test_remove_schedule(
        self, report_schedule_service: ReportScheduleService
    ):
        """測試移除排程任務"""
        schedule = ReportSchedule.create(
            report_type=ReportType.CISO_WEEKLY,
            cron_expression="0 9 * * 1",
            recipients=["ciso@example.com"],
            is_enabled=True,
        )

        # 先新增
        await report_schedule_service.add_schedule(schedule)

        # 再移除
        await report_schedule_service.remove_schedule(schedule.id)

        # 驗證排程器中沒有任務
        job_id = f"report_generation_{schedule.id}"
        job = report_schedule_service.scheduler.get_job(job_id)
        assert job is None

    @pytest.mark.asyncio
    async def test_update_schedule(
        self,
        report_schedule_service: ReportScheduleService,
        mock_schedule_repository,
    ):
        """測試更新排程任務"""
        schedule = ReportSchedule.create(
            report_type=ReportType.CISO_WEEKLY,
            cron_expression="0 9 * * 1",
            recipients=["ciso@example.com"],
            is_enabled=True,
        )

        mock_schedule_repository.get_by_id = AsyncMock(return_value=schedule)

        # 更新排程
        updated_schedule = await report_schedule_service.update_schedule(
            schedule_id=schedule.id,
            cron_expression="0 10 * * 1",  # 改為上午 10:00
            recipients=["ciso@example.com", "admin@example.com"],
        )

        assert updated_schedule.cron_expression == "0 10 * * 1"
        assert len(updated_schedule.recipients) == 2

    @pytest.mark.asyncio
    async def test_execute_report_generation(
        self,
        report_schedule_service: ReportScheduleService,
        mock_schedule_repository,
        mock_report_service,
    ):
        """測試執行報告生成任務（AC-016-4）"""
        schedule = ReportSchedule.create(
            report_type=ReportType.CISO_WEEKLY,
            cron_expression="0 9 * * 1",
            recipients=["ciso@example.com"],
            is_enabled=True,
        )

        mock_schedule_repository.get_by_id = AsyncMock(return_value=schedule)

        # 模擬報告生成
        mock_report = MagicMock()
        mock_report.id = "report-123"
        mock_report_service.generate_ciso_weekly_report = AsyncMock(
            return_value=mock_report
        )

        # 執行任務
        result = await report_schedule_service._execute_report_generation(schedule.id)

        assert result["success"] is True
        assert result["report_id"] == "report-123"

        # 驗證報告服務被呼叫
        mock_report_service.generate_ciso_weekly_report.assert_called_once()

        # 驗證排程的最後執行時間被更新
        mock_schedule_repository.save.assert_called()

    @pytest.mark.asyncio
    async def test_execute_schedule_now(
        self,
        report_schedule_service: ReportScheduleService,
        mock_schedule_repository,
    ):
        """測試立即執行排程任務（手動觸發）"""
        schedule = ReportSchedule.create(
            report_type=ReportType.CISO_WEEKLY,
            cron_expression="0 9 * * 1",
            recipients=["ciso@example.com"],
            is_enabled=True,
        )

        mock_schedule_repository.get_by_id = AsyncMock(return_value=schedule)

        # 模擬報告生成
        with patch.object(
            report_schedule_service, "_execute_report_generation", new_callable=AsyncMock
        ) as mock_execute:
            mock_execute.return_value = {"success": True, "report_id": "report-123"}

            result = await report_schedule_service.execute_schedule_now(schedule.id)

            assert result["success"] is True
            mock_execute.assert_called_once_with(schedule.id)

    @pytest.mark.asyncio
    async def test_get_schedule_status(
        self, report_schedule_service: ReportScheduleService
    ):
        """測試取得排程狀態"""
        schedule = ReportSchedule.create(
            report_type=ReportType.CISO_WEEKLY,
            cron_expression="0 9 * * 1",
            recipients=["ciso@example.com"],
            is_enabled=True,
        )

        # 新增排程
        await report_schedule_service.add_schedule(schedule)

        # 取得狀態
        status = report_schedule_service.get_schedule_status(schedule.id)

        assert status["exists"] is True
        assert status["enabled"] is True
        assert status["next_run_time"] is not None

    @pytest.mark.asyncio
    async def test_get_all_schedules(
        self, report_schedule_service: ReportScheduleService
    ):
        """測試取得所有排程狀態"""
        schedule1 = ReportSchedule.create(
            report_type=ReportType.CISO_WEEKLY,
            cron_expression="0 9 * * 1",
            recipients=["ciso@example.com"],
            is_enabled=True,
        )

        schedule2 = ReportSchedule.create(
            report_type=ReportType.IT_TICKET,
            cron_expression="0 8 * * *",
            recipients=["admin@example.com"],
            is_enabled=True,
        )

        # 新增排程
        await report_schedule_service.add_schedule(schedule1)
        await report_schedule_service.add_schedule(schedule2)

        # 取得所有排程
        schedules = report_schedule_service.get_all_schedules()

        assert len(schedules) == 2

    @pytest.mark.asyncio
    async def test_start_and_load_schedules(
        self,
        report_schedule_service: ReportScheduleService,
        mock_schedule_repository,
    ):
        """測試啟動服務並載入排程"""
        schedule = ReportSchedule.create(
            report_type=ReportType.CISO_WEEKLY,
            cron_expression="0 9 * * 1",
            recipients=["ciso@example.com"],
            is_enabled=True,
        )

        mock_schedule_repository.get_all_enabled = AsyncMock(return_value=[schedule])

        # 啟動服務
        await report_schedule_service.start()

        # 驗證排程器已啟動
        assert report_schedule_service.scheduler.running is True

        # 驗證排程已載入
        job_id = f"report_generation_{schedule.id}"
        job = report_schedule_service.scheduler.get_job(job_id)
        assert job is not None

        # 停止服務
        await report_schedule_service.stop()
        assert report_schedule_service.scheduler.running is False

    @pytest.mark.asyncio
    async def test_schedule_disabled_not_added(
        self, report_schedule_service: ReportScheduleService
    ):
        """測試停用的排程不會被新增到排程器"""
        schedule = ReportSchedule.create(
            report_type=ReportType.CISO_WEEKLY,
            cron_expression="0 9 * * 1",
            recipients=["ciso@example.com"],
            is_enabled=False,  # 停用
        )

        await report_schedule_service.add_schedule(schedule)

        # 驗證排程器中沒有任務
        job_id = f"report_generation_{schedule.id}"
        job = report_schedule_service.scheduler.get_job(job_id)
        assert job is None

