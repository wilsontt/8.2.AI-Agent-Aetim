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
        """
        self.report_generation_service = report_generation_service
        self.report_repository = report_repository
        self.ai_summary_service = ai_summary_service
        self.threat_asset_association_repository = threat_asset_association_repository
        self.asset_repository = asset_repository
        
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

