"""
通知排程整合測試

測試通知排程功能，包括排程管理、任務執行、狀態追蹤。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, time

from reporting_notification.application.services.notification_schedule_service import (
    NotificationScheduleService,
)
from reporting_notification.domain.aggregates.notification_rule import NotificationRule
from reporting_notification.domain.value_objects.notification_type import NotificationType
from reporting_notification.application.services.daily_high_risk_summary_service import (
    DailyHighRiskSummaryService,
)


class TestNotificationScheduleService:
    """測試通知排程服務"""

    @pytest.fixture
    def mock_notification_rule_repository(self):
        """建立模擬通知規則 Repository"""
        repository = MagicMock()
        repository.get_by_type = AsyncMock()
        return repository

    @pytest.fixture
    def mock_daily_summary_service(self):
        """建立模擬每日高風險威脅摘要服務"""
        service = MagicMock()
        service.send_summary = AsyncMock()
        return service

    @pytest.fixture
    def notification_rule(self):
        """建立高風險每日摘要通知規則"""
        return NotificationRule.create(
            notification_type=NotificationType.HIGH_RISK_DAILY,
            recipients=["security@example.com"],
            risk_score_threshold=6.0,
            send_time=time(8, 0),
            is_enabled=True,
        )

    @pytest.fixture
    def schedule_service(
        self,
        mock_notification_rule_repository,
        mock_daily_summary_service,
    ):
        """建立通知排程服務"""
        return NotificationScheduleService(
            notification_rule_repository=mock_notification_rule_repository,
            daily_summary_service=mock_daily_summary_service,
        )

    @pytest.mark.asyncio
    async def test_add_daily_summary_schedule(
        self,
        schedule_service: NotificationScheduleService,
    ):
        """測試新增每日高風險威脅摘要排程（AC-020-3, AC-020-4）"""
        send_time = time(8, 0)
        
        await schedule_service.add_daily_summary_schedule(send_time)
        
        # 驗證排程已新增
        job = schedule_service.scheduler.get_job("daily_summary_high_risk_daily")
        assert job is not None
        assert job.name == "每日高風險威脅摘要"

    @pytest.mark.asyncio
    async def test_remove_daily_summary_schedule(
        self,
        schedule_service: NotificationScheduleService,
    ):
        """測試移除每日高風險威脅摘要排程"""
        # 先新增排程
        await schedule_service.add_daily_summary_schedule(time(8, 0))
        
        # 驗證排程存在
        job = schedule_service.scheduler.get_job("daily_summary_high_risk_daily")
        assert job is not None
        
        # 移除排程
        await schedule_service.remove_daily_summary_schedule()
        
        # 驗證排程已移除
        job = schedule_service.scheduler.get_job("daily_summary_high_risk_daily")
        assert job is None

    @pytest.mark.asyncio
    async def test_update_daily_summary_schedule(
        self,
        schedule_service: NotificationScheduleService,
    ):
        """測試更新每日高風險威脅摘要排程（AC-020-4）"""
        # 先新增排程
        await schedule_service.add_daily_summary_schedule(time(8, 0))
        
        # 更新排程時間
        new_time = time(9, 30)
        await schedule_service.update_daily_summary_schedule(new_time)
        
        # 驗證排程已更新
        job = schedule_service.scheduler.get_job("daily_summary_high_risk_daily")
        assert job is not None

    @pytest.mark.asyncio
    async def test_get_schedule_status(
        self,
        schedule_service: NotificationScheduleService,
    ):
        """測試取得排程任務狀態"""
        # 先新增排程
        await schedule_service.add_daily_summary_schedule(time(8, 0))
        
        # 取得狀態
        status = schedule_service.get_schedule_status()
        
        assert status["job_id"] == "daily_summary_high_risk_daily"
        assert status["status"] in ["Active", "Inactive"]
        assert status["is_running"] is False

    @pytest.mark.asyncio
    async def test_get_execution_history(
        self,
        schedule_service: NotificationScheduleService,
        mock_daily_summary_service,
    ):
        """測試取得排程執行歷史記錄"""
        job_id = "daily_summary_high_risk_daily"
        
        # 執行任務（成功）
        mock_daily_summary_service.send_summary = AsyncMock()
        await schedule_service._execute_daily_summary()
        
        # 取得歷史記錄
        history = schedule_service.get_execution_history(job_id)
        
        assert len(history) > 0
        assert history[0]["job_id"] == job_id
        assert history[0]["status"] == "Success"
        assert history[0]["execution_duration"] is not None

    @pytest.mark.asyncio
    async def test_execution_history_failed(
        self,
        schedule_service: NotificationScheduleService,
        mock_daily_summary_service,
    ):
        """測試執行失敗時的歷史記錄"""
        job_id = "daily_summary_high_risk_daily"
        
        # 執行任務（失敗）
        mock_daily_summary_service.send_summary = AsyncMock(
            side_effect=Exception("Test error")
        )
        await schedule_service._execute_daily_summary()
        
        # 取得歷史記錄
        history = schedule_service.get_execution_history(job_id)
        
        assert len(history) > 0
        assert history[0]["status"] == "Failed"
        assert history[0]["error_message"] == "Test error"

    @pytest.mark.asyncio
    async def test_load_schedules(
        self,
        schedule_service: NotificationScheduleService,
        notification_rule: NotificationRule,
        mock_notification_rule_repository,
    ):
        """測試載入排程任務"""
        # 設定模擬返回值
        mock_notification_rule_repository.get_by_type = AsyncMock(
            return_value=notification_rule
        )
        
        # 啟動排程服務
        await schedule_service.start()
        
        # 驗證排程已載入
        job = schedule_service.scheduler.get_job("daily_summary_high_risk_daily")
        assert job is not None
        
        # 停止排程服務
        await schedule_service.stop()

    @pytest.mark.asyncio
    async def test_execute_daily_summary_success(
        self,
        schedule_service: NotificationScheduleService,
        mock_daily_summary_service,
    ):
        """測試執行每日高風險威脅摘要任務（成功）"""
        mock_daily_summary_service.send_summary = AsyncMock()
        
        await schedule_service._execute_daily_summary()
        
        # 驗證任務已執行
        mock_daily_summary_service.send_summary.assert_called_once()
        
        # 驗證歷史記錄
        history = schedule_service.get_execution_history()
        assert len(history) > 0
        assert history[0]["status"] == "Success"

    @pytest.mark.asyncio
    async def test_execute_daily_summary_concurrent(
        self,
        schedule_service: NotificationScheduleService,
        mock_daily_summary_service,
    ):
        """測試並發執行保護"""
        # 模擬長時間執行的任務
        async def slow_send_summary():
            import asyncio
            await asyncio.sleep(0.1)
        
        mock_daily_summary_service.send_summary = AsyncMock(
            side_effect=slow_send_summary
        )
        
        # 同時執行兩次任務
        import asyncio
        await asyncio.gather(
            schedule_service._execute_daily_summary(),
            schedule_service._execute_daily_summary(),
        )
        
        # 驗證只執行了一次（第二次被跳過）
        assert mock_daily_summary_service.send_summary.call_count == 1

