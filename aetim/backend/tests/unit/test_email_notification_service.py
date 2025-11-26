"""
Email 通知服務單元測試

測試 Email 通知服務功能，包括發送通知、生成通知內容。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from reporting_notification.domain.aggregates.notification import Notification
from reporting_notification.domain.aggregates.notification_rule import NotificationRule
from reporting_notification.domain.value_objects.notification_type import NotificationType
from reporting_notification.application.services.notification_service import NotificationService
from reporting_notification.infrastructure.external_services.email_service import (
    EmailService,
    EmailConfig,
)


class TestEmailService:
    """測試 EmailService"""

    @pytest.fixture
    def email_config(self):
        """建立 Email 設定"""
        return EmailConfig(
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_username="test@example.com",
            smtp_password="password",
            smtp_use_tls=True,
            from_email="noreply@example.com",
            from_name="Test System",
        )

    @pytest.fixture
    def email_service(self, email_config):
        """建立 Email 服務"""
        return EmailService(config=email_config)

    @pytest.mark.asyncio
    async def test_send_email_success(self, email_service):
        """測試成功發送 Email"""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server
            
            success = await email_service.send(
                recipients=["test@example.com"],
                subject="Test Subject",
                body="Test Body",
            )
            
            assert success is True
            mock_server.starttls.assert_called_once()
            mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_html(self, email_service):
        """測試發送包含 HTML 的 Email"""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server
            
            success = await email_service.send(
                recipients=["test@example.com"],
                subject="Test Subject",
                body="Test Body",
                html_body="<html><body>Test HTML</body></html>",
            )
            
            assert success is True
            mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_empty_recipients(self, email_service):
        """測試發送 Email 時收件人為空（應該失敗）"""
        with pytest.raises(ValueError, match="收件人清單不能為空"):
            await email_service.send(
                recipients=[],
                subject="Test Subject",
                body="Test Body",
            )

    @pytest.mark.asyncio
    async def test_send_email_invalid_address(self, email_service):
        """測試發送 Email 時地址無效（應該失敗）"""
        with pytest.raises(ValueError, match="無效的 Email 地址"):
            await email_service.send(
                recipients=["invalid-email"],
                subject="Test Subject",
                body="Test Body",
            )

    @pytest.mark.asyncio
    async def test_send_batch(self, email_service):
        """測試批次發送 Email"""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server
            
            emails = [
                {
                    "recipients": ["test1@example.com"],
                    "subject": "Test 1",
                    "body": "Body 1",
                },
                {
                    "recipients": ["test2@example.com"],
                    "subject": "Test 2",
                    "body": "Body 2",
                },
            ]
            
            results = await email_service.send_batch(emails)
            
            assert len(results) == 2
            assert all(r["success"] for r in results)
            assert mock_server.send_message.call_count == 2


class TestNotificationService:
    """測試 NotificationService"""

    @pytest.fixture
    def mock_notification_repository(self):
        """建立模擬通知 Repository"""
        repository = MagicMock()
        repository.save = AsyncMock()
        repository.get_by_id = AsyncMock()
        repository.get_by_threat_id = AsyncMock(return_value=[])
        repository.get_by_report_id = AsyncMock(return_value=[])
        return repository

    @pytest.fixture
    def mock_email_service(self):
        """建立模擬 Email 服務"""
        service = MagicMock()
        service.send = AsyncMock(return_value=True)
        return service

    @pytest.fixture
    def mock_template_renderer(self):
        """建立模擬模板渲染服務"""
        renderer = MagicMock()
        renderer.render_html = MagicMock(return_value="<html>Test</html>")
        return renderer

    @pytest.fixture
    def notification_service(
        self,
        mock_notification_repository,
        mock_email_service,
        mock_template_renderer,
    ):
        """建立通知服務"""
        return NotificationService(
            notification_repository=mock_notification_repository,
            email_service=mock_email_service,
            template_renderer=mock_template_renderer,
            base_url="http://localhost:8000",
        )

    @pytest.fixture
    def notification_rule(self):
        """建立通知規則"""
        return NotificationRule.create(
            notification_type=NotificationType.CRITICAL,
            recipients=["admin@example.com"],
        )

    @pytest.mark.asyncio
    async def test_send_critical_threat_notification(
        self,
        notification_service: NotificationService,
        notification_rule: NotificationRule,
        mock_email_service,
        mock_notification_repository,
    ):
        """測試發送嚴重威脅通知（AC-019-1, AC-019-2, AC-019-3）"""
        content = {
            "threat_title": "Test Threat",
            "cve_id": "CVE-2024-0001",
            "risk_score": 8.5,
            "affected_assets_count": 5,
            "threat_id": "threat-123",
        }
        
        notification = await notification_service.send_notification(
            notification_rule=notification_rule,
            content=content,
            related_threat_id="threat-123",
        )
        
        assert notification.notification_type == NotificationType.CRITICAL
        assert notification.status == "Sent"
        assert "Test Threat" in notification.subject
        assert "CVE-2024-0001" in notification.subject
        
        # 驗證 Email 發送
        mock_email_service.send.assert_called_once()
        call_args = mock_email_service.send.call_args
        assert call_args.kwargs["recipients"] == ["admin@example.com"]
        assert "Test Threat" in call_args.kwargs["subject"]
        
        # 驗證通知記錄儲存
        mock_notification_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_high_risk_daily_summary(
        self,
        notification_service: NotificationService,
        mock_email_service,
        mock_notification_repository,
    ):
        """測試發送高風險每日摘要（AC-020-1, AC-020-2）"""
        notification_rule = NotificationRule.create(
            notification_type=NotificationType.HIGH_RISK_DAILY,
            recipients=["security@example.com"],
        )
        
        content = {
            "threat_count": 3,
            "threats": [
                {
                    "title": "Threat 1",
                    "cve_id": "CVE-2024-0001",
                    "risk_score": 7.5,
                },
                {
                    "title": "Threat 2",
                    "cve_id": "CVE-2024-0002",
                    "risk_score": 6.5,
                },
            ],
            "total_affected_assets": 10,
            "average_risk_score": 7.0,
        }
        
        notification = await notification_service.send_notification(
            notification_rule=notification_rule,
            content=content,
        )
        
        assert notification.notification_type == NotificationType.HIGH_RISK_DAILY
        assert notification.status == "Sent"
        assert "高風險威脅每日摘要" in notification.subject
        
        # 驗證 Email 發送
        mock_email_service.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_weekly_report_notification(
        self,
        notification_service: NotificationService,
        mock_email_service,
        mock_notification_repository,
    ):
        """測試發送週報通知（AC-016-3）"""
        notification_rule = NotificationRule.create(
            notification_type=NotificationType.WEEKLY,
            recipients=["ciso@example.com"],
        )
        
        content = {
            "report_id": "report-123",
            "summary": "本週發現 5 個高風險威脅",
        }
        
        notification = await notification_service.send_notification(
            notification_rule=notification_rule,
            content=content,
            related_report_id="report-123",
        )
        
        assert notification.notification_type == NotificationType.WEEKLY
        assert notification.status == "Sent"
        assert "CISO 週報" in notification.subject
        
        # 驗證 Email 發送
        mock_email_service.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_email_failure(
        self,
        notification_service: NotificationService,
        notification_rule: NotificationRule,
        mock_email_service,
        mock_notification_repository,
    ):
        """測試 Email 發送失敗的情況"""
        mock_email_service.send = AsyncMock(side_effect=Exception("SMTP Error"))
        
        content = {
            "threat_title": "Test Threat",
            "cve_id": "CVE-2024-0001",
            "risk_score": 8.5,
            "affected_assets_count": 5,
            "threat_id": "threat-123",
        }
        
        notification = await notification_service.send_notification(
            notification_rule=notification_rule,
            content=content,
        )
        
        assert notification.status == "Failed"
        assert notification.error_message is not None
        assert "SMTP Error" in notification.error_message
        
        # 驗證通知記錄仍被儲存（即使發送失敗）
        mock_notification_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_critical_threat_content(
        self,
        notification_service: NotificationService,
    ):
        """測試生成嚴重威脅通知內容（AC-019-2）"""
        content = {
            "threat_title": "Critical Vulnerability",
            "cve_id": "CVE-2024-0001",
            "risk_score": 9.0,
            "affected_assets_count": 10,
            "threat_id": "threat-123",
        }
        
        subject, body, html_body = await notification_service._generate_notification_content(
            NotificationType.CRITICAL,
            content,
        )
        
        assert "Critical Vulnerability" in subject
        assert "CVE-2024-0001" in subject
        assert "Critical Vulnerability" in body
        assert "9.0" in body
        assert html_body is not None

    @pytest.mark.asyncio
    async def test_generate_high_risk_daily_content(
        self,
        notification_service: NotificationService,
    ):
        """測試生成高風險每日摘要內容（AC-020-2）"""
        content = {
            "threat_count": 5,
            "threats": [
                {"title": "Threat 1", "cve_id": "CVE-2024-0001", "risk_score": 7.0},
            ],
            "total_affected_assets": 20,
            "average_risk_score": 7.5,
        }
        
        subject, body, html_body = await notification_service._generate_notification_content(
            NotificationType.HIGH_RISK_DAILY,
            content,
        )
        
        assert "高風險威脅每日摘要" in subject
        assert "5" in body
        assert "20" in body
        assert html_body is not None

