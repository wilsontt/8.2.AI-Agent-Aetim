"""
通知服務（Application Layer）

協調通知發送流程，整合 Domain Service 和 Infrastructure。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from ...domain.aggregates.notification import Notification
from ...domain.aggregates.notification_rule import NotificationRule
from ...domain.value_objects.notification_type import NotificationType
from ...domain.interfaces.notification_repository import INotificationRepository
from ...infrastructure.external_services.email_service import EmailService
from ...infrastructure.services.template_renderer import TemplateRenderer

logger = structlog.get_logger(__name__)


class NotificationService:
    """
    通知服務（Application Layer）
    
    負責協調通知發送流程，整合：
    1. Domain Service（通知業務邏輯）
    2. Infrastructure（Email 服務、模板渲染、Repository）
    """
    
    def __init__(
        self,
        notification_repository: INotificationRepository,
        email_service: EmailService,
        template_renderer: TemplateRenderer,
        base_url: str = "http://localhost:8000",
    ):
        """
        初始化通知服務
        
        Args:
            notification_repository: 通知 Repository
            email_service: Email 服務
            template_renderer: 模板渲染服務
            base_url: 基礎 URL（用於生成詳細資訊連結）
        """
        self.notification_repository = notification_repository
        self.email_service = email_service
        self.template_renderer = template_renderer
        self.base_url = base_url
    
    async def send_notification(
        self,
        notification_rule: NotificationRule,
        content: Dict[str, Any],
        related_threat_id: Optional[str] = None,
        related_report_id: Optional[str] = None,
    ) -> Notification:
        """
        發送通知（AC-016-3, AC-019-3）
        
        Args:
            notification_rule: 通知規則
            content: 通知內容（字典格式）
            related_threat_id: 相關威脅 ID（可選）
            related_report_id: 相關報告 ID（可選）
        
        Returns:
            Notification: 通知聚合根
        
        Raises:
            ValueError: 當輸入參數無效時
            Exception: 當發送失敗時
        """
        try:
            # 生成通知內容
            subject, body, html_body = await self._generate_notification_content(
                notification_rule.notification_type,
                content,
            )
            
            # 建立通知記錄（AC-019-4, AC-020-4）
            notification = Notification.create(
                notification_type=notification_rule.notification_type,
                recipients=notification_rule.recipients,
                subject=subject,
                body=body,
                notification_rule_id=notification_rule.id,
                related_threat_id=related_threat_id,
                related_report_id=related_report_id,
            )
            
            # 發送 Email 通知（AC-016-3, AC-019-3）
            try:
                success = await self.email_service.send(
                    recipients=notification.recipients,
                    subject=notification.subject,
                    body=notification.body,
                    html_body=html_body,
                )
                
                if success:
                    notification.mark_as_sent()
                    logger.info(
                        "通知發送成功",
                        notification_id=notification.id,
                        notification_type=notification.notification_type.value,
                        recipients=notification.recipients,
                    )
                else:
                    notification.mark_as_failed("Email 發送失敗")
                    logger.error(
                        "通知發送失敗",
                        notification_id=notification.id,
                        notification_type=notification.notification_type.value,
                    )
                    
            except Exception as e:
                error_message = f"Email 發送失敗：{str(e)}"
                notification.mark_as_failed(error_message)
                logger.error(
                    "通知發送失敗",
                    notification_id=notification.id,
                    notification_type=notification.notification_type.value,
                    error=str(e),
                    exc_info=True,
                )
            
            # 儲存通知記錄（AC-019-4）
            await self.notification_repository.save(notification)
            
            return notification
            
        except Exception as e:
            logger.error(
                "發送通知失敗",
                notification_rule_id=notification_rule.id if notification_rule else None,
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def _generate_notification_content(
        self,
        notification_type: NotificationType,
        content: Dict[str, Any],
    ) -> tuple[str, str, Optional[str]]:
        """
        生成通知內容（AC-019-2, AC-020-2）
        
        Args:
            notification_type: 通知類型
            content: 通知內容（字典格式）
        
        Returns:
            tuple[str, str, Optional[str]]: (主旨, 純文字內容, HTML 內容)
        """
        if notification_type == NotificationType.CRITICAL:
            return await self._generate_critical_threat_content(content)
        elif notification_type == NotificationType.HIGH_RISK_DAILY:
            return await self._generate_high_risk_daily_content(content)
        elif notification_type == NotificationType.WEEKLY:
            return await self._generate_weekly_report_content(content)
        else:
            raise ValueError(f"不支援的通知類型：{notification_type}")
    
    async def _generate_critical_threat_content(
        self,
        content: Dict[str, Any],
    ) -> tuple[str, str, Optional[str]]:
        """
        生成嚴重威脅通知內容（AC-019-2）
        
        Args:
            content: 威脅內容，應包含：
                - threat_title: 威脅標題
                - cve_id: CVE 編號
                - risk_score: 風險分數
                - affected_assets_count: 受影響資產數量
                - affected_assets: 受影響資產清單（可選）
                - threat_id: 威脅 ID（用於生成詳細資訊連結）
        
        Returns:
            tuple[str, str, Optional[str]]: (主旨, 純文字內容, HTML 內容)
        """
        threat_title = content.get("threat_title", "未知威脅")
        cve_id = content.get("cve_id", "N/A")
        risk_score = content.get("risk_score", 0.0)
        affected_assets_count = content.get("affected_assets_count", 0)
        affected_assets = content.get("affected_assets", [])
        threat_id = content.get("threat_id", "")
        
        # 生成主旨
        subject = f"⚠️ 嚴重威脅通知：{threat_title} (CVE: {cve_id})"
        
        # 生成純文字內容
        body = f"""
嚴重威脅通知

威脅標題：{threat_title}
CVE 編號：{cve_id}
風險分數：{risk_score}/10.0
受影響資產數量：{affected_assets_count}

詳細資訊：{self.base_url}/threats/{threat_id}

此通知由 AETIM 安全系統自動發送。
"""
        
        # 生成 HTML 內容
        html_body = self.template_renderer.render_html(
            template_name="critical_threat_notification.html",
            context={
                "threat_title": threat_title,
                "cve_id": cve_id,
                "risk_score": risk_score,
                "affected_assets_count": affected_assets_count,
                "affected_assets": affected_assets,
                "detail_url": f"{self.base_url}/threats/{threat_id}",
            },
        )
        
        return subject, body.strip(), html_body
    
    async def _generate_high_risk_daily_content(
        self,
        content: Dict[str, Any],
    ) -> tuple[str, str, Optional[str]]:
        """
        生成高風險每日摘要內容（AC-020-2）
        
        Args:
            content: 摘要內容，應包含：
                - threat_count: 威脅數量
                - threats: 威脅清單
                - total_affected_assets: 受影響資產總數
                - average_risk_score: 平均風險分數
                - asset_statistics: 受影響資產統計（可選）
        
        Returns:
            tuple[str, str, Optional[str]]: (主旨, 純文字內容, HTML 內容)
        """
        threat_count = content.get("threat_count", 0)
        threats = content.get("threats", [])
        total_affected_assets = content.get("total_affected_assets", 0)
        average_risk_score = content.get("average_risk_score", 0.0)
        asset_statistics = content.get("asset_statistics", [])
        report_date = datetime.now().strftime("%Y-%m-%d")
        
        # 生成主旨
        subject = f"📊 高風險威脅每日摘要 - {report_date}"
        
        # 生成純文字內容
        body = f"""
高風險威脅每日摘要

報告日期：{report_date}

統計資訊：
- 威脅數量：{threat_count}
- 受影響資產總數：{total_affected_assets}
- 平均風險分數：{average_risk_score}/10.0

威脅清單：
"""
        
        for threat in threats:
            body += f"\n- {threat.get('title', '未知威脅')} (CVE: {threat.get('cve_id', 'N/A')}, 風險分數: {threat.get('risk_score', 0.0)}/10.0)"
        
        body += f"\n\n詳細資訊：{self.base_url}/reports/daily-summary\n\n此摘要由 AETIM 安全系統自動發送。"
        
        # 生成 HTML 內容
        html_body = self.template_renderer.render_html(
            template_name="high_risk_daily_summary.html",
            context={
                "report_date": report_date,
                "threat_count": threat_count,
                "threats": threats,
                "total_affected_assets": total_affected_assets,
                "average_risk_score": average_risk_score,
                "asset_statistics": asset_statistics,
            },
        )
        
        return subject, body.strip(), html_body
    
    async def _generate_weekly_report_content(
        self,
        content: Dict[str, Any],
    ) -> tuple[str, str, Optional[str]]:
        """
        生成週報通知內容
        
        Args:
            content: 週報內容，應包含：
                - report_id: 報告 ID
                - summary: 報告摘要（可選）
        
        Returns:
            tuple[str, str, Optional[str]]: (主旨, 純文字內容, HTML 內容)
        """
        report_id = content.get("report_id", "")
        summary = content.get("summary", "CISO 週報已生成，請查看詳細內容。")
        report_date = datetime.now().strftime("%Y-%m-%d")
        
        # 生成主旨
        subject = f"📄 CISO 週報已生成 - {report_date}"
        
        # 生成純文字內容
        body = f"""
CISO 週報通知

報告日期：{report_date}

報告摘要：
{summary}

詳細資訊：{self.base_url}/reports/{report_id}

此通知由 AETIM 安全系統自動發送。
"""
        
        # 生成 HTML 內容
        html_body = self.template_renderer.render_html(
            template_name="weekly_report_notification.html",
            context={
                "report_date": report_date,
                "summary": summary,
                "report_url": f"{self.base_url}/reports/{report_id}",
            },
        )
        
        return subject, body.strip(), html_body

