"""
報告服務（Application Layer）

協調報告生成流程，整合 Domain Service 和 Infrastructure。
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog
from pathlib import Path

from ...domain.aggregates.report import Report
from ...domain.value_objects.report_type import ReportType
from ...domain.value_objects.file_format import FileFormat
from ...domain.value_objects.ticket_status import TicketStatus
from ...domain.domain_services.report_generation_service import (
    ReportGenerationService,
    WeeklyReportData,
)
from ...domain.interfaces.report_repository import IReportRepository
from ...infrastructure.external_services.ai_summary_service import AISummaryService
from ...infrastructure.services.template_renderer import TemplateRenderer
from threat_intelligence.domain.interfaces.threat_repository import IThreatRepository
from analysis_assessment.domain.interfaces.risk_assessment_repository import (
    IRiskAssessmentRepository,
)
from asset_management.domain.interfaces.asset_repository import IAssetRepository
from threat_intelligence.infrastructure.persistence.threat_asset_association_repository import (
    ThreatAssetAssociationRepository,
)
from asset_management.domain.aggregates.asset import Asset
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from system_management.application.services.audit_log_service import AuditLogService

logger = structlog.get_logger(__name__)


class ReportService:
    """
    報告服務（Application Layer）
    
    負責協調報告生成流程，整合：
    1. Domain Service（報告生成邏輯）
    2. Infrastructure（Repository、AI 服務）
    """
    
    def __init__(
        self,
        report_generation_service: ReportGenerationService,
        report_repository: IReportRepository,
        ai_summary_service: AISummaryService,
        threat_asset_association_repository: ThreatAssetAssociationRepository,
        asset_repository: IAssetRepository,
        template_renderer: Optional[TemplateRenderer] = None,
        audit_log_service: Optional[Any] = None,  # AuditLogService，使用 Any 避免循環導入
    ):
        """
        初始化報告服務
        
        Args:
            report_generation_service: 報告生成服務（Domain Service）
            report_repository: 報告 Repository
            ai_summary_service: AI 摘要服務
            threat_asset_association_repository: 威脅資產關聯 Repository
            asset_repository: 資產 Repository
            template_renderer: 模板渲染服務（可選）
            audit_log_service: 稽核日誌服務（可選）
        """
        self.report_generation_service = report_generation_service
        self.report_repository = report_repository
        self.ai_summary_service = ai_summary_service
        self.threat_asset_association_repository = threat_asset_association_repository
        self.asset_repository = asset_repository
        self.audit_log_service = audit_log_service
        
        # 如果提供了模板渲染服務，注入到報告生成服務
        if template_renderer is not None:
            self.report_generation_service.template_renderer = template_renderer
        
        # 注入威脅資產關聯 Repository 到報告生成服務
        self.report_generation_service.threat_asset_association_repository = (
            threat_asset_association_repository
        )
    
    async def generate_ciso_weekly_report(
        self,
        period_start: datetime,
        period_end: datetime,
        file_format: FileFormat = FileFormat.HTML,
    ) -> Report:
        """
        生成 CISO 週報（AC-015-1）
        
        Args:
            period_start: 報告期間開始時間
            period_end: 報告期間結束時間
            file_format: 檔案格式（HTML 或 PDF，AC-015-3）
        
        Returns:
            Report: 生成的報告聚合根
        """
        logger.info(
            "開始生成 CISO 週報",
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            file_format=file_format.value,
        )
        
        # 1. 收集報告資料（包含完整的資產統計）
        report_data = await self._collect_complete_weekly_data(
            period_start, period_end
        )
        
        # 2. AI 生成業務風險描述（AC-015-4）
        if report_data.critical_threat_list:
            # 建立技術描述
            technical_description = self._build_technical_description(report_data)
            
            # 呼叫 AI 服務生成業務風險描述
            business_risk_description = (
                await self.ai_summary_service.generate_business_risk_description(
                    technical_description
                )
            )
            
            # 設定摘要
            report_data.business_risk_description = business_risk_description
        
        # 3. 生成報告內容
        report_content = await self.report_generation_service._generate_report_content(
            report_data, file_format
        )
        
        # 4. 建立 Report 聚合根
        title = f"CISO Weekly Report {period_end.strftime('%Y-%m-%d')}"
        file_path = ""  # 將由 Repository 設定
        
        report = Report.create(
            report_type=ReportType.CISO_WEEKLY,
            title=title,
            file_path=file_path,
            file_format=file_format,
            period_start=period_start,
            period_end=period_end,
            summary=report_data.business_risk_description,
            metadata={
                "total_threats": report_data.total_threats,
                "critical_threats": report_data.critical_threats,
                "affected_assets_by_type": report_data.affected_assets_by_type,
                "affected_assets_by_importance": report_data.affected_assets_by_importance,
            },
        )
        
        # 5. 儲存報告（包含檔案）
        await self.report_repository.save(report, report_content)
        
            logger.info(
                "CISO 週報生成完成",
                report_id=report.id,
                file_path=report.file_path,
            )
            
            return report
    
    async def generate_it_ticket(
        self,
        risk_assessment_id: str,
        file_format: FileFormat = FileFormat.TEXT,
    ) -> Report:
        """
        生成 IT 工單（AC-017-1）
        
        Args:
            risk_assessment_id: 風險評估 ID
            file_format: 檔案格式（TEXT 或 JSON，AC-017-3）
        
        Returns:
            Report: 生成的工單報告聚合根
        """
        from analysis_assessment.domain.interfaces.risk_assessment_repository import (
            IRiskAssessmentRepository,
        )
        
        # 取得風險評估
        risk_assessment = await self.report_generation_service.risk_assessment_repository.get_by_id(
            risk_assessment_id
        )
        if not risk_assessment:
            raise ValueError(f"找不到風險評估：{risk_assessment_id}")
        
        # 檢查風險分數是否 >= 6.0（AC-017-1）
        if risk_assessment.final_risk_score < 6.0:
            raise ValueError(
                f"風險分數 {risk_assessment.final_risk_score} 低於 6.0，不符合工單生成條件"
            )
        
        # 生成工單內容
        ticket_content = await self.report_generation_service._generate_ticket_content(
            threat=await self.report_generation_service.threat_repository.get_by_id(
                risk_assessment.threat_id
            ),
            risk_assessment=risk_assessment,
            affected_assets=await self.report_generation_service._get_affected_assets_for_ticket(
                risk_assessment.threat_id
            ),
            file_format=file_format,
        )
        
        # 生成工單報告
        report = await self.report_generation_service.generate_it_ticket(
            risk_assessment=risk_assessment,
            file_format=file_format,
        )
        
        # 設定檔案路徑（將由 Repository 設定，這裡暫時為空）
        # 儲存報告（包含檔案）
        await self.report_repository.save(report, ticket_content.encode('utf-8'))
        
        logger.info(
            "IT 工單生成完成",
            report_id=report.id,
            risk_assessment_id=risk_assessment_id,
        )
        
        return report
    
    def _build_technical_description(self, report_data: WeeklyReportData) -> str:
        """
        建立技術描述
        
        Args:
            report_data: 週報資料
        
        Returns:
            str: 技術描述
        """
        description = f"本週共發現 {report_data.total_threats} 個威脅，其中 {report_data.critical_threats} 個為嚴重威脅（風險分數 ≥ 8.0）。\n\n"
        
        description += "嚴重威脅清單：\n"
        for threat in report_data.critical_threat_list[:10]:  # 限制前 10 個
            description += f"- {threat['cve_id']}: {threat['title']} (風險分數: {threat['risk_score']:.2f}, 受影響資產: {threat['affected_asset_count']})\n"
        
        if report_data.affected_assets_by_type:
            description += "\n受影響資產統計（依類型）：\n"
            for asset_type, count in report_data.affected_assets_by_type.items():
                description += f"- {asset_type}: {count} 個\n"
        
        if report_data.affected_assets_by_importance:
            description += "\n受影響資產統計（依重要性）：\n"
            for importance, count in report_data.affected_assets_by_importance.items():
                description += f"- {importance}: {count} 個\n"
        
        return description
    
    async def _collect_complete_weekly_data(
        self, period_start: datetime, period_end: datetime
    ) -> WeeklyReportData:
        """
        收集完整的週報資料（包含資產統計）
        
        Args:
            period_start: 報告期間開始時間
            period_end: 報告期間結束時間
        
        Returns:
            WeeklyReportData: 週報資料
        """
        # 使用 Domain Service 收集基本資料
        report_data = await self.report_generation_service._collect_weekly_data(
            period_start, period_end
        )
        
        # 補充受影響資產統計
        affected_assets_by_type, affected_assets_by_importance = (
            await self._get_complete_affected_assets_statistics(
                report_data.critical_threat_list
            )
        )
        
        report_data.affected_assets_by_type = affected_assets_by_type
        report_data.affected_assets_by_importance = affected_assets_by_importance
        
        return report_data
    
    async def _get_complete_affected_assets_statistics(
        self, critical_threat_list: List[Dict[str, Any]]
    ) -> tuple[Dict[str, int], Dict[str, int]]:
        """
        取得完整的受影響資產統計
        
        Args:
            critical_threat_list: 嚴重威脅清單（包含 threat_id）
        
        Returns:
            tuple[Dict[str, int], Dict[str, int]]: (依類型統計, 依重要性統計)
        """
        assets_by_type: Dict[str, int] = {}
        assets_by_importance: Dict[str, int] = {}
        processed_assets = set()
        
        # 取得所有嚴重威脅的受影響資產
        for threat_info in critical_threat_list:
            threat_id = threat_info.get("threat_id")
            if not threat_id:
                continue
            
            # 查詢威脅的關聯資產
            associations = await self.threat_asset_association_repository.get_by_threat_id(
                threat_id
            )
            
            for association in associations:
                asset_id = association.asset_id
                if asset_id in processed_assets:
                    continue
                
                processed_assets.add(asset_id)
                
                # 取得資產詳情
                asset = await self.asset_repository.get_by_id(asset_id)
                if asset:
                    # 統計資產類型
                    asset_type = asset.asset_type or "Unknown"
                    assets_by_type[asset_type] = assets_by_type.get(asset_type, 0) + 1
                    
                    # 統計資產重要性（組合敏感度和關鍵性）
                    sensitivity = asset.data_sensitivity.value if asset.data_sensitivity else "Unknown"
                    criticality = (
                        asset.business_criticality.value
                        if asset.business_criticality
                        else "Unknown"
                    )
                    importance_key = f"{sensitivity}-{criticality}"
                    assets_by_importance[importance_key] = (
                        assets_by_importance.get(importance_key, 0) + 1
                    )
        
        return assets_by_type, assets_by_importance
    
    async def export_ticket(
        self,
        ticket_id: str,
        file_format: Optional[FileFormat] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        匯出單一工單（AC-017-4）
        
        Args:
            ticket_id: 工單 ID（報告 ID）
            file_format: 檔案格式（可選，如果不提供則使用報告的原始格式）
            user_id: 使用者 ID（用於稽核日誌）
            ip_address: IP 位址（用於稽核日誌）
            user_agent: User Agent（用於稽核日誌）
        
        Returns:
            Dict[str, Any]: 包含 file_content（檔案內容）、file_name（檔案名稱）、content_type（內容類型）
        
        Raises:
            ValueError: 當工單不存在或不是 IT_Ticket 類型時
        """
        # 取得工單記錄
        report = await self.report_repository.get_by_id(ticket_id)
        if not report:
            raise ValueError(f"找不到工單：{ticket_id}")
        
        # 檢查是否為 IT_Ticket 類型
        if report.report_type != ReportType.IT_TICKET:
            raise ValueError(f"報告 {ticket_id} 不是 IT 工單類型")
        
        # 決定檔案格式
        export_format = file_format if file_format else report.file_format
        
        # 取得檔案內容
        file_content = await self.report_repository.get_file_content(ticket_id)
        if not file_content:
            raise ValueError(f"找不到工單檔案：{ticket_id}")
        
        # 如果請求的格式與原始格式不同，需要重新生成
        if file_format and file_format != report.file_format:
            # 這裡需要重新生成工單內容（簡化處理，暫時返回原始內容）
            # TODO: 實作格式轉換功能
            logger.warning(
                "請求的格式與原始格式不同，返回原始格式",
                ticket_id=ticket_id,
                requested_format=file_format.value,
                original_format=report.file_format.value,
            )
        
        # 決定檔案名稱和內容類型
        file_extension = export_format.get_file_extension()
        file_name = f"IT_Ticket_{ticket_id}{file_extension}"
        
        content_type_map = {
            FileFormat.TEXT: "text/plain; charset=utf-8",
            FileFormat.JSON: "application/json; charset=utf-8",
            FileFormat.HTML: "text/html; charset=utf-8",
            FileFormat.PDF: "application/pdf",
        }
        content_type = content_type_map.get(export_format, "application/octet-stream")
        
        # 記錄稽核日誌（AC-018-3）
        if self.audit_log_service:
            try:
                await self.audit_log_service.log_action(
                    user_id=user_id,
                    action="EXPORT",
                    resource_type="IT_Ticket",
                    resource_id=ticket_id,
                    details={
                        "file_format": export_format.value,
                        "file_name": file_name,
                    },
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            except Exception as e:
                logger.warning(
                    "記錄稽核日誌失敗",
                    ticket_id=ticket_id,
                    error=str(e),
                )
        
        logger.info(
            "工單匯出完成",
            ticket_id=ticket_id,
            file_format=export_format.value,
            file_name=file_name,
        )
        
        return {
            "file_content": file_content,
            "file_name": file_name,
            "content_type": content_type,
        }
    
    async def export_tickets_batch(
        self,
        ticket_ids: List[str],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        批次匯出工單（AC-018-1, AC-018-2）
        
        Args:
            ticket_ids: 工單 ID 清單
            user_id: 使用者 ID（用於稽核日誌）
            ip_address: IP 位址（用於稽核日誌）
            user_agent: User Agent（用於稽核日誌）
        
        Returns:
            Dict[str, Any]: 包含 file_content（檔案內容）、file_name（檔案名稱）、content_type（內容類型）
        
        Raises:
            ValueError: 當工單 ID 清單為空時
        """
        if not ticket_ids:
            raise ValueError("工單 ID 清單不能為空")
        
        logger.info(
            "開始批次匯出工單",
            ticket_count=len(ticket_ids),
        )
        
        # 取得所有工單
        tickets_data = []
        for ticket_id in ticket_ids:
            report = await self.report_repository.get_by_id(ticket_id)
            if not report:
                logger.warning(
                    "找不到工單，跳過",
                    ticket_id=ticket_id,
                )
                continue
            
            # 檢查是否為 IT_Ticket 類型
            if report.report_type != ReportType.IT_TICKET:
                logger.warning(
                    "報告不是 IT 工單類型，跳過",
                    ticket_id=ticket_id,
                    report_type=report.report_type.value,
                )
                continue
            
            # 取得檔案內容
            file_content = await self.report_repository.get_file_content(ticket_id)
            if not file_content:
                logger.warning(
                    "找不到工單檔案，跳過",
                    ticket_id=ticket_id,
                )
                continue
            
            # 解析 JSON 內容（如果是 JSON 格式）
            if report.file_format == FileFormat.JSON:
                try:
                    import json
                    ticket_json = json.loads(file_content.decode('utf-8'))
                    tickets_data.append(ticket_json)
                except Exception as e:
                    logger.warning(
                        "無法解析工單 JSON，跳過",
                        ticket_id=ticket_id,
                        error=str(e),
                    )
                    continue
            else:
                # 對於非 JSON 格式，轉換為 JSON 結構
                tickets_data.append({
                    "ticket_id": ticket_id,
                    "title": report.title,
                    "file_format": report.file_format.value,
                    "content": file_content.decode('utf-8'),
                    "generated_at": report.generated_at.isoformat(),
                })
        
        if not tickets_data:
            raise ValueError("沒有可匯出的工單")
        
        # 生成批次匯出 JSON（AC-018-2）
        batch_export_data = {
            "export_type": "batch_tickets",
            "exported_at": datetime.utcnow().isoformat(),
            "ticket_count": len(tickets_data),
            "tickets": tickets_data,
        }
        
        import json
        file_content = json.dumps(batch_export_data, ensure_ascii=False, indent=2).encode('utf-8')
        file_name = f"IT_Tickets_Batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        content_type = "application/json; charset=utf-8"
        
        # 記錄稽核日誌（AC-018-3）
        if self.audit_log_service:
            try:
                await self.audit_log_service.log_action(
                    user_id=user_id,
                    action="EXPORT",
                    resource_type="IT_Ticket",
                    resource_id=None,  # 批次匯出沒有單一資源 ID
                    details={
                        "ticket_count": len(tickets_data),
                        "ticket_ids": ticket_ids,
                        "file_name": file_name,
                    },
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            except Exception as e:
                logger.warning(
                    "記錄稽核日誌失敗",
                    ticket_count=len(tickets_data),
                    error=str(e),
                )
        
        logger.info(
            "批次工單匯出完成",
            ticket_count=len(tickets_data),
            file_name=file_name,
        )
        
        return {
            "file_content": file_content,
            "file_name": file_name,
            "content_type": content_type,
        }
    
    async def update_ticket_status(
        self,
        ticket_id: str,
        new_status: TicketStatus,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Report:
        """
        更新工單狀態（AC-017-5）
        
        Args:
            ticket_id: 工單 ID（報告 ID）
            new_status: 新狀態
            user_id: 使用者 ID（用於稽核日誌）
            ip_address: IP 位址（用於稽核日誌）
            user_agent: User Agent（用於稽核日誌）
        
        Returns:
            Report: 更新後的報告聚合根
        
        Raises:
            ValueError: 當工單不存在或不是 IT_Ticket 類型時
            ValueError: 當狀態轉換無效時
        """
        # 取得工單記錄
        report = await self.report_repository.get_by_id(ticket_id)
        if not report:
            raise ValueError(f"找不到工單：{ticket_id}")
        
        # 取得舊狀態（用於日誌）
        old_status = report.ticket_status or TicketStatus.PENDING
        
        # 更新狀態（會驗證狀態轉換規則並發布領域事件）
        report.update_ticket_status(new_status, updated_by=user_id)
        
        # 儲存到資料庫（只更新狀態，不需要重新儲存檔案）
        await self.report_repository._save_to_database(report)
        
        # 記錄稽核日誌
        if self.audit_log_service:
            try:
                await self.audit_log_service.log_action(
                    user_id=user_id,
                    action="UPDATE",
                    resource_type="IT_Ticket",
                    resource_id=ticket_id,
                    details={
                        "old_status": old_status.value,
                        "new_status": new_status.value,
                    },
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            except Exception as e:
                logger.warning(
                    "記錄稽核日誌失敗",
                    ticket_id=ticket_id,
                    error=str(e),
                )
        
        logger.info(
            "工單狀態已更新",
            ticket_id=ticket_id,
            old_status=old_status.value,
            new_status=new_status.value,
        )
        
        return report

