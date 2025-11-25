"""
通知規則管理單元測試

測試通知規則管理功能，包括建立、更新、刪除、查詢。
"""

import pytest
from datetime import datetime, time
from unittest.mock import AsyncMock, MagicMock

from reporting_notification.domain.aggregates.notification_rule import NotificationRule
from reporting_notification.domain.value_objects.notification_type import NotificationType
from reporting_notification.domain.domain_events.notification_rule_updated_event import (
    NotificationRuleUpdatedEvent,
)
from reporting_notification.application.services.notification_rule_service import (
    NotificationRuleService,
)


class TestNotificationRule:
    """測試 NotificationRule 聚合根"""

    def test_create_critical_notification_rule(self):
        """測試建立嚴重威脅通知規則（AC-021-1）"""
        rule = NotificationRule.create(
            notification_type=NotificationType.CRITICAL,
            recipients=["admin@example.com", "security@example.com"],
        )
        
        assert rule.notification_type == NotificationType.CRITICAL
        assert rule.risk_score_threshold == 8.0  # 預設閾值
        assert rule.recipients == ["admin@example.com", "security@example.com"]
        assert rule.is_enabled is True

    def test_create_high_risk_daily_notification_rule(self):
        """測試建立高風險每日摘要通知規則（AC-021-1）"""
        rule = NotificationRule.create(
            notification_type=NotificationType.HIGH_RISK_DAILY,
            recipients=["security@example.com"],
            send_time=time(8, 0),
        )
        
        assert rule.notification_type == NotificationType.HIGH_RISK_DAILY
        assert rule.risk_score_threshold == 6.0  # 預設閾值
        assert rule.send_time == time(8, 0)

    def test_create_weekly_notification_rule(self):
        """測試建立週報通知規則（AC-021-1）"""
        rule = NotificationRule.create(
            notification_type=NotificationType.WEEKLY,
            recipients=["ciso@example.com"],
        )
        
        assert rule.notification_type == NotificationType.WEEKLY
        assert rule.risk_score_threshold is None  # 週報不需要風險分數閾值

    def test_should_trigger_critical(self):
        """測試嚴重威脅通知觸發條件（AC-021-1）"""
        rule = NotificationRule.create(
            notification_type=NotificationType.CRITICAL,
            recipients=["admin@example.com"],
        )
        
        # 風險分數 ≥ 8.0 應該觸發
        assert rule.should_trigger(risk_score=8.0) is True
        assert rule.should_trigger(risk_score=9.0) is True
        
        # 風險分數 < 8.0 不應該觸發
        assert rule.should_trigger(risk_score=7.9) is False
        
        # 停用時不應該觸發
        rule.is_enabled = False
        assert rule.should_trigger(risk_score=9.0) is False

    def test_should_trigger_high_risk_daily(self):
        """測試高風險每日摘要觸發條件（AC-021-1）"""
        rule = NotificationRule.create(
            notification_type=NotificationType.HIGH_RISK_DAILY,
            recipients=["security@example.com"],
        )
        
        # 風險分數 ≥ 6.0 應該觸發
        assert rule.should_trigger(risk_score=6.0) is True
        assert rule.should_trigger(risk_score=7.0) is True
        
        # 風險分數 < 6.0 不應該觸發
        assert rule.should_trigger(risk_score=5.9) is False

    def test_should_trigger_weekly(self):
        """測試週報通知觸發條件（AC-021-1）"""
        rule = NotificationRule.create(
            notification_type=NotificationType.WEEKLY,
            recipients=["ciso@example.com"],
        )
        
        # 週報通知由排程觸發，不需要風險分數
        assert rule.should_trigger() is True
        assert rule.should_trigger(risk_score=None) is True

    def test_toggle_enabled(self):
        """測試啟用/停用通知（AC-021-3）"""
        rule = NotificationRule.create(
            notification_type=NotificationType.CRITICAL,
            recipients=["admin@example.com"],
        )
        
        assert rule.is_enabled is True
        
        # 停用
        rule.toggle_enabled()
        assert rule.is_enabled is False
        
        # 啟用
        rule.toggle_enabled()
        assert rule.is_enabled is True
        
        # 驗證領域事件
        events = rule.get_domain_events()
        assert len(events) == 2
        assert all(isinstance(e, NotificationRuleUpdatedEvent) for e in events)

    def test_update_recipients(self):
        """測試更新收件人（AC-021-2）"""
        rule = NotificationRule.create(
            notification_type=NotificationType.CRITICAL,
            recipients=["admin@example.com"],
        )
        
        new_recipients = ["admin@example.com", "security@example.com", "ciso@example.com"]
        rule.update_recipients(new_recipients)
        
        assert rule.recipients == new_recipients
        
        # 驗證領域事件
        events = rule.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], NotificationRuleUpdatedEvent)

    def test_update_recipients_empty_list(self):
        """測試更新收件人為空清單（應該失敗）"""
        rule = NotificationRule.create(
            notification_type=NotificationType.CRITICAL,
            recipients=["admin@example.com"],
        )
        
        with pytest.raises(ValueError, match="收件人清單不能為空"):
            rule.update_recipients([])

    def test_create_rule_empty_recipients(self):
        """測試建立規則時收件人為空（應該失敗）"""
        with pytest.raises(ValueError, match="收件人清單不能為空"):
            NotificationRule.create(
                notification_type=NotificationType.CRITICAL,
                recipients=[],
            )


class TestNotificationRuleService:
    """測試 NotificationRuleService"""

    @pytest.fixture
    def mock_repository(self):
        """建立模擬 Repository"""
        repository = MagicMock()
        repository.save = AsyncMock()
        repository.get_by_id = AsyncMock()
        repository.get_all = AsyncMock()
        repository.get_enabled_rules = AsyncMock()
        repository.get_by_type = AsyncMock()
        repository.delete = AsyncMock()
        return repository

    @pytest.fixture
    def mock_audit_log_service(self):
        """建立模擬稽核日誌服務"""
        service = MagicMock()
        service.log_action = AsyncMock(return_value="audit-log-id")
        return service

    @pytest.fixture
    def service(self, mock_repository, mock_audit_log_service):
        """建立通知規則服務"""
        return NotificationRuleService(
            repository=mock_repository,
            audit_log_service=mock_audit_log_service,
        )

    @pytest.mark.asyncio
    async def test_create_rule_success(
        self,
        service: NotificationRuleService,
        mock_repository,
        mock_audit_log_service,
    ):
        """測試成功建立通知規則（AC-021-1）"""
        rule = await service.create_rule(
            notification_type=NotificationType.CRITICAL,
            recipients=["admin@example.com"],
            user_id="user-1",
            ip_address="10.0.0.1",
            user_agent="Test Agent",
        )
        
        assert rule.notification_type == NotificationType.CRITICAL
        assert rule.recipients == ["admin@example.com"]
        mock_repository.save.assert_called_once()
        
        # 驗證稽核日誌
        mock_audit_log_service.log_action.assert_called_once()
        call_args = mock_audit_log_service.log_action.call_args
        assert call_args.kwargs["user_id"] == "user-1"
        assert call_args.kwargs["action"] == "CREATE"
        assert call_args.kwargs["resource_type"] == "NotificationRule"

    @pytest.mark.asyncio
    async def test_update_rule_recipients(
        self,
        service: NotificationRuleService,
        mock_repository,
        mock_audit_log_service,
    ):
        """測試更新收件人（AC-021-2）"""
        existing_rule = NotificationRule.create(
            notification_type=NotificationType.CRITICAL,
            recipients=["admin@example.com"],
        )
        mock_repository.get_by_id = AsyncMock(return_value=existing_rule)
        
        rule = await service.update_rule(
            rule_id=existing_rule.id,
            recipients=["admin@example.com", "security@example.com"],
            user_id="user-1",
        )
        
        assert len(rule.recipients) == 2
        mock_repository.save.assert_called_once()
        
        # 驗證稽核日誌
        mock_audit_log_service.log_action.assert_called_once()
        call_args = mock_audit_log_service.log_action.call_args
        assert call_args.kwargs["action"] == "UPDATE"
        assert "recipients" in call_args.kwargs["details"]

    @pytest.mark.asyncio
    async def test_update_rule_toggle_enabled(
        self,
        service: NotificationRuleService,
        mock_repository,
        mock_audit_log_service,
    ):
        """測試啟用/停用通知（AC-021-3）"""
        existing_rule = NotificationRule.create(
            notification_type=NotificationType.CRITICAL,
            recipients=["admin@example.com"],
        )
        mock_repository.get_by_id = AsyncMock(return_value=existing_rule)
        
        rule = await service.update_rule(
            rule_id=existing_rule.id,
            is_enabled=False,
            user_id="user-1",
        )
        
        assert rule.is_enabled is False
        mock_repository.save.assert_called_once()
        
        # 驗證稽核日誌
        mock_audit_log_service.log_action.assert_called_once()
        call_args = mock_audit_log_service.log_action.call_args
        assert call_args.kwargs["action"] == "UPDATE"
        assert "is_enabled" in call_args.kwargs["details"]

    @pytest.mark.asyncio
    async def test_delete_rule_success(
        self,
        service: NotificationRuleService,
        mock_repository,
        mock_audit_log_service,
    ):
        """測試成功刪除通知規則"""
        existing_rule = NotificationRule.create(
            notification_type=NotificationType.CRITICAL,
            recipients=["admin@example.com"],
        )
        mock_repository.get_by_id = AsyncMock(return_value=existing_rule)
        
        await service.delete_rule(
            rule_id=existing_rule.id,
            user_id="user-1",
        )
        
        mock_repository.delete.assert_called_once_with(existing_rule.id)
        
        # 驗證稽核日誌
        mock_audit_log_service.log_action.assert_called_once()
        call_args = mock_audit_log_service.log_action.call_args
        assert call_args.kwargs["action"] == "DELETE"

    @pytest.mark.asyncio
    async def test_get_rules(
        self,
        service: NotificationRuleService,
        mock_repository,
    ):
        """測試查詢通知規則清單"""
        rule1 = NotificationRule.create(
            notification_type=NotificationType.CRITICAL,
            recipients=["admin@example.com"],
        )
        rule2 = NotificationRule.create(
            notification_type=NotificationType.HIGH_RISK_DAILY,
            recipients=["security@example.com"],
        )
        mock_repository.get_all = AsyncMock(return_value=[rule1, rule2])
        
        rules = await service.get_rules()
        
        assert len(rules) == 2
        assert rules[0].notification_type == NotificationType.CRITICAL
        assert rules[1].notification_type == NotificationType.HIGH_RISK_DAILY

    @pytest.mark.asyncio
    async def test_get_enabled_rules(
        self,
        service: NotificationRuleService,
        mock_repository,
    ):
        """測試查詢啟用的通知規則"""
        rule1 = NotificationRule.create(
            notification_type=NotificationType.CRITICAL,
            recipients=["admin@example.com"],
            is_enabled=True,
        )
        rule2 = NotificationRule.create(
            notification_type=NotificationType.HIGH_RISK_DAILY,
            recipients=["security@example.com"],
            is_enabled=False,
        )
        mock_repository.get_enabled_rules = AsyncMock(return_value=[rule1])
        
        rules = await service.get_enabled_rules()
        
        assert len(rules) == 1
        assert rules[0].notification_type == NotificationType.CRITICAL
        assert rules[0].is_enabled is True

