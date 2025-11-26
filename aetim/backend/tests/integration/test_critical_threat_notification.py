"""
嚴重威脅即時通知整合測試

測試嚴重威脅即時通知功能，包括事件訂閱與處理。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from analysis_assessment.domain.domain_events.risk_assessment_completed_event import (
    RiskAssessmentCompletedEvent,
)
from reporting_notification.application.handlers.risk_assessment_event_handler import (
    RiskAssessmentEventHandler,
)
from reporting_notification.domain.aggregates.notification_rule import NotificationRule
from reporting_notification.domain.value_objects.notification_type import NotificationType
from reporting_notification.application.services.notification_service import NotificationService
from threat_intelligence.domain.aggregates.threat import Threat
from shared_kernel.infrastructure.event_bus import EventBus, reset_event_bus


class TestCriticalThreatNotification:
    """測試嚴重威脅即時通知"""

    @pytest.fixture
    def mock_notification_rule_repository(self):
        """建立模擬通知規則 Repository"""
        repository = MagicMock()
        repository.get_by_type = AsyncMock()
        return repository

    @pytest.fixture
    def mock_notification_service(self):
        """建立模擬通知服務"""
        service = MagicMock()
        service.send_notification = AsyncMock()
        return service

    @pytest.fixture
    def mock_threat_repository(self):
        """建立模擬威脅 Repository"""
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
    def notification_rule(self):
        """建立嚴重威脅通知規則"""
        return NotificationRule.create(
            notification_type=NotificationType.CRITICAL,
            recipients=["admin@example.com", "security@example.com"],
            risk_score_threshold=8.0,
            is_enabled=True,
        )

    @pytest.fixture
    def threat(self):
        """建立威脅"""
        return Threat.create(
            title="Critical Vulnerability",
            cve_id="CVE-2024-0001",
            description="Test threat",
            threat_feed_id="feed-123",
        )

    @pytest.fixture
    def event_handler(
        self,
        mock_notification_rule_repository,
        mock_notification_service,
        mock_threat_repository,
        mock_asset_repository,
    ):
        """建立事件處理器"""
        return RiskAssessmentEventHandler(
            notification_rule_repository=mock_notification_rule_repository,
            notification_service=mock_notification_service,
            threat_repository=mock_threat_repository,
            asset_repository=mock_asset_repository,
        )

    @pytest.mark.asyncio
    async def test_handle_critical_threat_notification(
        self,
        event_handler: RiskAssessmentEventHandler,
        notification_rule: NotificationRule,
        threat: Threat,
        mock_notification_rule_repository,
        mock_notification_service,
        mock_threat_repository,
    ):
        """測試處理嚴重威脅通知（AC-019-1, AC-019-2, AC-019-3, AC-019-4）"""
        # 設定模擬返回值
        mock_notification_rule_repository.get_by_type = AsyncMock(
            return_value=notification_rule
        )
        mock_threat_repository.get_by_id = AsyncMock(return_value=threat)
        
        # 建立事件
        event = RiskAssessmentCompletedEvent(
            risk_assessment_id="assessment-123",
            threat_id="threat-123",
            final_risk_score=9.0,  # ≥ 8.0
            risk_level="Critical",
            affected_asset_count=5,
            completed_at=datetime.utcnow(),
        )
        
        # 處理事件
        await event_handler.handle(event)
        
        # 驗證通知規則查詢
        mock_notification_rule_repository.get_by_type.assert_called_once_with(
            NotificationType.CRITICAL
        )
        
        # 驗證威脅查詢
        mock_threat_repository.get_by_id.assert_called_once_with("threat-123")
        
        # 驗證通知發送
        mock_notification_service.send_notification.assert_called_once()
        call_args = mock_notification_service.send_notification.call_args
        assert call_args.kwargs["notification_rule"] == notification_rule
        assert call_args.kwargs["related_threat_id"] == "threat-123"
        assert call_args.kwargs["content"]["risk_score"] == 9.0
        assert call_args.kwargs["content"]["threat_title"] == "Critical Vulnerability"
        assert call_args.kwargs["content"]["cve_id"] == "CVE-2024-0001"

    @pytest.mark.asyncio
    async def test_handle_low_risk_threat_no_notification(
        self,
        event_handler: RiskAssessmentEventHandler,
        mock_notification_rule_repository,
        mock_notification_service,
    ):
        """測試低風險威脅不發送通知（AC-019-1）"""
        # 建立事件（風險分數 < 8.0）
        event = RiskAssessmentCompletedEvent(
            risk_assessment_id="assessment-123",
            threat_id="threat-123",
            final_risk_score=7.0,  # < 8.0
            risk_level="High",
            affected_asset_count=3,
            completed_at=datetime.utcnow(),
        )
        
        # 處理事件
        await event_handler.handle(event)
        
        # 驗證不發送通知
        mock_notification_service.send_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_no_notification_rule(
        self,
        event_handler: RiskAssessmentEventHandler,
        threat: Threat,
        mock_notification_rule_repository,
        mock_notification_service,
        mock_threat_repository,
    ):
        """測試沒有通知規則時不發送通知"""
        # 設定模擬返回值（沒有通知規則）
        mock_notification_rule_repository.get_by_type = AsyncMock(return_value=None)
        mock_threat_repository.get_by_id = AsyncMock(return_value=threat)
        
        # 建立事件
        event = RiskAssessmentCompletedEvent(
            risk_assessment_id="assessment-123",
            threat_id="threat-123",
            final_risk_score=9.0,
            risk_level="Critical",
            affected_asset_count=5,
            completed_at=datetime.utcnow(),
        )
        
        # 處理事件
        await event_handler.handle(event)
        
        # 驗證不發送通知
        mock_notification_service.send_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_disabled_notification_rule(
        self,
        event_handler: RiskAssessmentEventHandler,
        mock_notification_rule_repository,
        mock_notification_service,
    ):
        """測試通知規則已停用時不發送通知"""
        # 建立停用的通知規則
        disabled_rule = NotificationRule.create(
            notification_type=NotificationType.CRITICAL,
            recipients=["admin@example.com"],
            is_enabled=False,  # 已停用
        )
        
        mock_notification_rule_repository.get_by_type = AsyncMock(
            return_value=disabled_rule
        )
        
        # 建立事件
        event = RiskAssessmentCompletedEvent(
            risk_assessment_id="assessment-123",
            threat_id="threat-123",
            final_risk_score=9.0,
            risk_level="Critical",
            affected_asset_count=5,
            completed_at=datetime.utcnow(),
        )
        
        # 處理事件
        await event_handler.handle(event)
        
        # 驗證不發送通知
        mock_notification_service.send_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_event_bus_integration(
        self,
        mock_notification_rule_repository,
        mock_notification_service,
        mock_threat_repository,
        mock_asset_repository,
        notification_rule,
        threat,
    ):
        """測試事件總線整合"""
        # 重置事件總線
        reset_event_bus()
        event_bus = EventBus()
        
        # 建立事件處理器
        event_handler = RiskAssessmentEventHandler(
            notification_rule_repository=mock_notification_rule_repository,
            notification_service=mock_notification_service,
            threat_repository=mock_threat_repository,
            asset_repository=mock_asset_repository,
        )
        
        # 訂閱事件
        event_bus.subscribe("RiskAssessmentCompletedEvent", event_handler.handle)
        
        # 設定模擬返回值
        mock_notification_rule_repository.get_by_type = AsyncMock(
            return_value=notification_rule
        )
        mock_threat_repository.get_by_id = AsyncMock(return_value=threat)
        
        # 建立並發布事件
        event = RiskAssessmentCompletedEvent(
            risk_assessment_id="assessment-123",
            threat_id="threat-123",
            final_risk_score=9.0,
            risk_level="Critical",
            affected_asset_count=5,
            completed_at=datetime.utcnow(),
        )
        
        await event_bus.publish(event)
        
        # 驗證通知發送
        mock_notification_service.send_notification.assert_called_once()

