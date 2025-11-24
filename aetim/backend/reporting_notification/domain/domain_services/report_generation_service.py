"""
報告生成服務

實作報告生成邏輯，符合 AC-015-1 至 AC-015-6 的要求。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..aggregates.report import Report
from ..value_objects.report_type import ReportType
from ..value_objects.file_format import FileFormat
from threat_intelligence.domain.aggregates.threat import Threat
from threat_intelligence.domain.interfaces.threat_repository import IThreatRepository
from analysis_assessment.domain.aggregates.risk_assessment import RiskAssessment
from analysis_assessment.domain.interfaces.risk_assessment_repository import (
    IRiskAssessmentRepository,
)
from asset_management.domain.aggregates.asset import Asset
from asset_management.domain.interfaces.asset_repository import IAssetRepository
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class WeeklyReportData:
    """週報資料結構"""
    
    period_start: datetime
    period_end: datetime
    total_threats: int
    critical_threats: int
    critical_threat_list: List[Dict[str, Any]]
    affected_assets_by_type: Dict[str, int]
    affected_assets_by_importance: Dict[str, int]
    risk_trend: Dict[str, Any]
    business_risk_description: Optional[str] = None


class ReportGenerationService:
    """
    報告生成服務（Domain Service）
    
    負責生成各種類型的報告，符合 AC-015-1 至 AC-015-6 的要求。
    """
    
    def __init__(
        self,
        threat_repository: IThreatRepository,
        risk_assessment_repository: IRiskAssessmentRepository,
        asset_repository: IAssetRepository,
    ):
        """
        初始化報告生成服務
        
        Args:
            threat_repository: 威脅 Repository
            risk_assessment_repository: 風險評估 Repository
            asset_repository: 資產 Repository
        """
        self.threat_repository = threat_repository
        self.risk_assessment_repository = risk_assessment_repository
        self.asset_repository = asset_repository
    
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
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        logger.info(
            "開始生成 CISO 週報",
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
        )
        
        # 1. 收集本週威脅情資與風險評估（AC-015-2）
        report_data = await self._collect_weekly_data(period_start, period_end)
        
        # 2. 生成報告內容
        report_content = await self._generate_report_content(report_data, file_format)
        
        # 3. 生成報告檔案（AC-015-5, AC-015-6）
        # 注意：實際檔案儲存將由 Application Service 處理
        # 這裡只生成檔案路徑和內容
        
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
        
        logger.info(
            "CISO 週報生成完成",
            report_id=report.id,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
        )
        
        return report
    
    async def _collect_weekly_data(
        self, period_start: datetime, period_end: datetime
    ) -> WeeklyReportData:
        """
        收集本週威脅情資與風險評估（AC-015-2）
        
        Args:
            period_start: 報告期間開始時間
            period_end: 報告期間結束時間
        
        Returns:
            WeeklyReportData: 週報資料
        """
        # 1. 取得期間內的威脅
        threats = await self._get_threats_in_period(period_start, period_end)
        
        # 2. 取得期間內的風險評估
        risk_assessments = await self._get_risk_assessments_in_period(
            period_start, period_end
        )
        
        # 3. 統計威脅數量
        total_threats = len(threats)
        
        # 4. 統計嚴重威脅（風險分數 ≥ 8.0）
        critical_threats = []
        critical_threat_count = 0
        
        for risk_assessment in risk_assessments:
            if risk_assessment.final_risk_score >= 8.0:
                critical_threat_count += 1
                # 取得對應的威脅
                threat = await self.threat_repository.get_by_id(risk_assessment.threat_id)
                if threat:
                    # 取得受影響的資產數量（從風險評估中取得）
                    affected_asset_count = risk_assessment.affected_asset_count
                    critical_threats.append({
                        "threat_id": threat.id,
                        "cve_id": threat.cve_id or "N/A",
                        "title": threat.title,
                        "risk_score": risk_assessment.final_risk_score,
                        "risk_level": risk_assessment.risk_level,
                        "affected_asset_count": affected_asset_count,
                    })
        
        # 5. 受影響資產統計（依資產類型、重要性分類）
        affected_assets_by_type, affected_assets_by_importance = (
            await self._get_affected_assets_statistics(risk_assessments)
        )
        
        # 6. 風險趨勢分析（與上週比較）
        risk_trend = await self._calculate_risk_trend(period_start, period_end)
        
        return WeeklyReportData(
            period_start=period_start,
            period_end=period_end,
            total_threats=total_threats,
            critical_threats=critical_threat_count,
            critical_threat_list=critical_threats,
            affected_assets_by_type=affected_assets_by_type,
            affected_assets_by_importance=affected_assets_by_importance,
            risk_trend=risk_trend,
        )
    
    async def _get_threats_in_period(
        self, period_start: datetime, period_end: datetime
    ) -> List[Threat]:
        """
        取得期間內的威脅
        
        Args:
            period_start: 開始時間
            period_end: 結束時間
        
        Returns:
            List[Threat]: 威脅清單
        """
        # 取得所有威脅（這裡需要擴充 Repository 以支援日期範圍查詢）
        # 暫時使用 get_all 然後過濾
        all_threats = await self.threat_repository.get_all(skip=0, limit=10000)
        
        # 過濾期間內的威脅
        threats_in_period = [
            threat
            for threat in all_threats
            if threat.collected_at
            and period_start <= threat.collected_at <= period_end
        ]
        
        return threats_in_period
    
    async def _get_risk_assessments_in_period(
        self, period_start: datetime, period_end: datetime
    ) -> List[RiskAssessment]:
        """
        取得期間內的風險評估
        
        Args:
            period_start: 開始時間
            period_end: 結束時間
        
        Returns:
            List[RiskAssessment]: 風險評估清單
        """
        # 取得所有威脅
        all_threats = await self.threat_repository.get_all(skip=0, limit=10000)
        
        # 取得每個威脅的風險評估
        risk_assessments = []
        for threat in all_threats:
            if threat.collected_at and period_start <= threat.collected_at <= period_end:
                risk_assessment = await self.risk_assessment_repository.get_by_threat_id(
                    threat.id
                )
                if risk_assessment:
                    risk_assessments.append(risk_assessment)
        
        return risk_assessments
    
    async def _get_affected_assets_for_threat(self, threat_id: str) -> List[Asset]:
        """
        取得威脅的受影響資產
        
        Args:
            threat_id: 威脅 ID
        
        Returns:
            List[Asset]: 受影響的資產清單
        """
        # 這裡需要透過 ThreatAssetAssociationRepository 查詢
        # 暫時返回空清單，將在 Application Service 中實作
        return []
    
    async def _get_affected_assets_statistics(
        self, risk_assessments: List[RiskAssessment]
    ) -> tuple[Dict[str, int], Dict[str, int]]:
        """
        取得受影響資產統計（依資產類型、重要性分類）
        
        Args:
            risk_assessments: 風險評估清單
        
        Returns:
            tuple[Dict[str, int], Dict[str, int]]: (依類型統計, 依重要性統計)
        """
        # 暫時返回空統計，將在 Application Service 中實作
        return {}, {}
    
    async def _calculate_risk_trend(
        self, period_start: datetime, period_end: datetime
    ) -> Dict[str, Any]:
        """
        計算風險趨勢（與上週比較）
        
        Args:
            period_start: 本週開始時間
            period_end: 本週結束時間
        
        Returns:
            Dict[str, Any]: 風險趨勢資料
        """
        # 計算上週期間
        week_duration = period_end - period_start
        last_period_start = period_start - week_duration
        last_period_end = period_start
        
        # 取得本週和上週的威脅數量
        this_week_threats = await self._get_threats_in_period(period_start, period_end)
        last_week_threats = await self._get_threats_in_period(
            last_period_start, last_period_end
        )
        
        # 取得本週和上週的風險評估
        this_week_assessments = await self._get_risk_assessments_in_period(
            period_start, period_end
        )
        last_week_assessments = await self._get_risk_assessments_in_period(
            last_period_start, last_period_end
        )
        
        # 計算平均風險分數
        this_week_avg_score = (
            sum(a.final_risk_score for a in this_week_assessments)
            / len(this_week_assessments)
            if this_week_assessments
            else 0.0
        )
        last_week_avg_score = (
            sum(a.final_risk_score for a in last_week_assessments)
            / len(last_week_assessments)
            if last_week_assessments
            else 0.0
        )
        
        # 計算變化
        threat_count_change = len(this_week_threats) - len(last_week_threats)
        risk_score_change = this_week_avg_score - last_week_avg_score
        
        return {
            "this_week": {
                "threat_count": len(this_week_threats),
                "avg_risk_score": this_week_avg_score,
            },
            "last_week": {
                "threat_count": len(last_week_threats),
                "avg_risk_score": last_week_avg_score,
            },
            "threat_count_change": threat_count_change,
            "risk_score_change": risk_score_change,
            "threat_count_trend": "上升" if threat_count_change > 0 else "下降" if threat_count_change < 0 else "持平",
            "risk_score_trend": "上升" if risk_score_change > 0 else "下降" if risk_score_change < 0 else "持平",
        }
    
    async def _generate_report_content(
        self, report_data: WeeklyReportData, file_format: FileFormat
    ) -> bytes:
        """
        生成報告內容（AC-015-3）
        
        Args:
            report_data: 週報資料
            file_format: 檔案格式
        
        Returns:
            bytes: 報告內容（位元組）
        """
        # 基本 HTML 模板（詳細模板將在 T-4-1-3 實作）
        if file_format == FileFormat.HTML:
            html_content = self._generate_html_content(report_data)
            return html_content.encode("utf-8")
        elif file_format == FileFormat.PDF:
            # PDF 生成將在 T-4-1-3 實作
            # 暫時返回 HTML 內容
            html_content = self._generate_html_content(report_data)
            return html_content.encode("utf-8")
        else:
            raise ValueError(f"不支援的檔案格式: {file_format}")
    
    def _generate_html_content(self, report_data: WeeklyReportData) -> str:
        """
        生成 HTML 內容（基本模板）
        
        Args:
            report_data: 週報資料
        
        Returns:
            str: HTML 內容
        """
        # 基本 HTML 模板（詳細模板將在 T-4-1-3 實作）
        html = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_data.period_end.strftime('%Y-%m-%d')} CISO 週報</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            line-height: 1.6;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #666;
            margin-top: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        .stat-box {{
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .critical {{
            color: #d32f2f;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <h1>CISO 週報 - {report_data.period_end.strftime('%Y年%m月%d日')}</h1>
    
    <div class="stat-box">
        <h2>報告期間</h2>
        <p>開始時間：{report_data.period_start.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>結束時間：{report_data.period_end.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="stat-box">
        <h2>威脅情資摘要</h2>
        <p>本週威脅總數：<strong>{report_data.total_threats}</strong></p>
        <p>嚴重威脅數量（風險分數 ≥ 8.0）：<strong class="critical">{report_data.critical_threats}</strong></p>
    </div>
    
    <h2>嚴重威脅清單</h2>
    <table>
        <thead>
            <tr>
                <th>CVE 編號</th>
                <th>標題</th>
                <th>風險分數</th>
                <th>風險等級</th>
                <th>受影響資產數量</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for threat in report_data.critical_threat_list:
            html += f"""
            <tr>
                <td>{threat['cve_id']}</td>
                <td>{threat['title']}</td>
                <td class="critical">{threat['risk_score']:.2f}</td>
                <td>{threat['risk_level']}</td>
                <td>{threat['affected_asset_count']}</td>
            </tr>
"""
        
        html += """
        </tbody>
    </table>
    
    <h2>受影響資產統計</h2>
    <div class="stat-box">
        <h3>依資產類型分類</h3>
        <ul>
"""
        
        for asset_type, count in report_data.affected_assets_by_type.items():
            html += f"            <li>{asset_type}: {count} 個</li>\n"
        
        html += """
        </ul>
        <h3>依資產重要性分類</h3>
        <ul>
"""
        
        for importance, count in report_data.affected_assets_by_importance.items():
            html += f"            <li>{importance}: {count} 個</li>\n"
        
        html += f"""
        </ul>
    </div>
    
    <h2>風險趨勢分析</h2>
    <div class="stat-box">
        <p>本週威脅數量：<strong>{report_data.risk_trend['this_week']['threat_count']}</strong></p>
        <p>上週威脅數量：{report_data.risk_trend['last_week']['threat_count']}</p>
        <p>變化：<strong>{report_data.risk_trend['threat_count_change']:+d}</strong> ({report_data.risk_trend['threat_count_trend']})</p>
        <p>本週平均風險分數：<strong>{report_data.risk_trend['this_week']['avg_risk_score']:.2f}</strong></p>
        <p>上週平均風險分數：{report_data.risk_trend['last_week']['avg_risk_score']:.2f}</p>
        <p>變化：<strong>{report_data.risk_trend['risk_score_change']:+.2f}</strong> ({report_data.risk_trend['risk_score_trend']})</p>
    </div>
"""
        
        if report_data.business_risk_description:
            html += f"""
    <h2>業務風險描述</h2>
    <div class="stat-box">
        <p>{report_data.business_risk_description}</p>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        return html

