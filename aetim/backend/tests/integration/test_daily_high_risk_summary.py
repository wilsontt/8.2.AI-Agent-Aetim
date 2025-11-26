"""
每日高風險威脅摘要整合測試

測試每日高風險威脅摘要功能，包括摘要生成和通知發送。
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, time

from reporting_notification.application.services.daily_high_risk_summary_service import (
    DailyHighRiskSummaryService,
)
from reporting_notification.domain.aggregates.notification_rule import NotificationRule
from reporting_notification.domain.value_objects.notification_type import NotificationType
from reporting_notification.application.services.notification_service import NotificationService
from analysis_assessment.domain.aggregates.risk_assessment import RiskAssessment
from threat_intelligence.domain.aggregates.threat import Threat


class TestDailyHighRiskSummaryService:
    """測試每日高風險威脅摘要服務"""

    @pytest.fixture
    def mock_risk_assessment_repository(self):
        """建立模擬風險評估 Repository"""
        repository = MagicMock()
        repository.get_by_risk_score_range = AsyncMock()
        return repository

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
    def risk_assessments(self):
        """建立風險評估清單"""
        assessments = []
        
        # 建立第一個風險評估
        assessment1 = RiskAssessment.create(
            threat_id="threat-1",
            threat_asset_association_id="assoc-1",
            base_cvss_score=7.0,
            asset_importance_weight=1.5,
            affected_asset_count=5,
            asset_count_weight=0.1,
            final_risk_score=7.5,
            risk_level="High",
        )
        assessment1.id = "assessment-1"
        assessments.append(assessment1)
        
        # 建立第二個風險評估
        assessment2 = RiskAssessment.create(
            threat_id="threat-2",
            threat_asset_association_id="assoc-2",
            base_cvss_score=6.5,
            asset_importance_weight=1.0,
            affected_asset_count=3,
            asset_count_weight=0.05,
            final_risk_score=6.8,
            risk_level="High",
        )
        assessment2.id = "assessment-2"
        assessments.append(assessment2)
        
        return assessments

    @pytest.fixture
    def threats(self):
        """建立威脅清單"""
        threat1 = Threat.create(
            title="High Risk Vulnerability 1",
            cve_id="CVE-2024-0001",
            description="Test threat 1",
            threat_feed_id="feed-123",
        )
        threat1.id = "threat-1"
        
        threat2 = Threat.create(
            title="High Risk Vulnerability 2",
            cve_id="CVE-2024-0002",
            description="Test threat 2",
            threat_feed_id="feed-123",
        )
        threat2.id = "threat-2"
        
        return [threat1, threat2]

    @pytest.fixture
    def summary_service(
        self,
        mock_risk_assessment_repository,
        mock_threat_repository,
        mock_asset_repository,
        mock_notification_rule_repository,
        mock_notification_service,
    ):
        """建立每日高風險威脅摘要服務"""
        return DailyHighRiskSummaryService(
            risk_assessment_repository=mock_risk_assessment_repository,
            threat_repository=mock_threat_repository,
            asset_repository=mock_asset_repository,
            notification_rule_repository=mock_notification_rule_repository,
            notification_service=mock_notification_service,
        )

    @pytest.mark.asyncio
    async def test_generate_summary(
        self,
        summary_service: DailyHighRiskSummaryService,
        risk_assessments: list[RiskAssessment],
        threats: list[Threat],
        mock_risk_assessment_repository,
        mock_threat_repository,
    ):
        """測試生成每日高風險威脅摘要（AC-020-1, AC-020-2）"""
        # 設定模擬返回值
        mock_risk_assessment_repository.get_by_risk_score_range = AsyncMock(
            return_value=risk_assessments
        )
        mock_threat_repository.get_by_id = AsyncMock(side_effect=threats)
        
        # 生成摘要
        summary = await summary_service.generate_summary()
        
        # 驗證摘要內容
        assert summary["threat_count"] == 2
        assert len(summary["threats"]) == 2
        assert summary["total_affected_assets"] == 8  # 5 + 3
        assert summary["average_risk_score"] == pytest.approx(7.15, abs=0.01)  # (7.5 + 6.8) / 2
        
        # 驗證威脅清單
        assert summary["threats"][0]["threat_id"] == "threat-1"
        assert summary["threats"][0]["title"] == "High Risk Vulnerability 1"
        assert summary["threats"][0]["cve_id"] == "CVE-2024-0001"
        assert summary["threats"][0]["risk_score"] == 7.5
        
        # 驗證查詢參數
        call_args = mock_risk_assessment_repository.get_by_risk_score_range.call_args
        assert call_args.kwargs["min_risk_score"] == 6.0
        assert call_args.kwargs["max_risk_score"] is None

    @pytest.mark.asyncio
    async def test_generate_summary_no_threats(
        self,
        summary_service: DailyHighRiskSummaryService,
        mock_risk_assessment_repository,
    ):
        """測試沒有高風險威脅時的摘要生成"""
        # 設定模擬返回值（空清單）
        mock_risk_assessment_repository.get_by_risk_score_range = AsyncMock(
            return_value=[]
        )
        
        # 生成摘要
        summary = await summary_service.generate_summary()
        
        # 驗證摘要內容
        assert summary["threat_count"] == 0
        assert len(summary["threats"]) == 0
        assert summary["total_affected_assets"] == 0
        assert summary["average_risk_score"] == 0.0

    @pytest.mark.asyncio
    async def test_send_summary(
        self,
        summary_service: DailyHighRiskSummaryService,
        notification_rule: NotificationRule,
        risk_assessments: list[RiskAssessment],
        threats: list[Threat],
        mock_notification_rule_repository,
        mock_notification_service,
        mock_risk_assessment_repository,
        mock_threat_repository,
    ):
        """測試發送每日高風險威脅摘要（AC-020-3）"""
        # 設定模擬返回值
        mock_notification_rule_repository.get_by_type = AsyncMock(
            return_value=notification_rule
        )
        mock_risk_assessment_repository.get_by_risk_score_range = AsyncMock(
            return_value=risk_assessments
        )
        mock_threat_repository.get_by_id = AsyncMock(side_effect=threats)
        
        # 發送摘要
        await summary_service.send_summary()
        
        # 驗證通知發送
        mock_notification_service.send_notification.assert_called_once()
        call_args = mock_notification_service.send_notification.call_args
        assert call_args.kwargs["notification_rule"] == notification_rule
        assert call_args.kwargs["content"]["threat_count"] == 2

    @pytest.mark.asyncio
    async def test_send_summary_no_notification_rule(
        self,
        summary_service: DailyHighRiskSummaryService,
        mock_notification_rule_repository,
        mock_notification_service,
    ):
        """測試沒有通知規則時不發送摘要"""
        # 設定模擬返回值（沒有通知規則）
        mock_notification_rule_repository.get_by_type = AsyncMock(return_value=None)
        
        # 發送摘要
        await summary_service.send_summary()
        
        # 驗證不發送通知
        mock_notification_service.send_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_summary_disabled_rule(
        self,
        summary_service: DailyHighRiskSummaryService,
        mock_notification_rule_repository,
        mock_notification_service,
    ):
        """測試通知規則已停用時不發送摘要"""
        # 建立停用的通知規則
        disabled_rule = NotificationRule.create(
            notification_type=NotificationType.HIGH_RISK_DAILY,
            recipients=["security@example.com"],
            is_enabled=False,  # 已停用
        )
        
        mock_notification_rule_repository.get_by_type = AsyncMock(
            return_value=disabled_rule
        )
        
        # 發送摘要
        await summary_service.send_summary()
        
        # 驗證不發送通知
        mock_notification_service.send_notification.assert_not_called()

