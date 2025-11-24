"""
模板渲染服務單元測試

測試模板渲染服務的功能。
"""

import pytest
from pathlib import Path
from datetime import datetime
from tempfile import TemporaryDirectory

from reporting_notification.infrastructure.services.template_renderer import (
    TemplateRenderer,
)
from reporting_notification.domain.domain_services.report_generation_service import (
    WeeklyReportData,
)


class TestTemplateRenderer:
    """測試模板渲染服務"""

    @pytest.fixture
    def temp_template_dir(self):
        """建立臨時模板目錄"""
        with TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir) / "templates"
            template_dir.mkdir(parents=True)
            
            # 建立測試模板
            template_file = template_dir / "test_template.html"
            template_file.write_text(
                """
<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
    <h1>{{ title }}</h1>
    <p>日期：{{ date.strftime('%Y-%m-%d') }}</p>
    {% if items %}
    <ul>
        {% for item in items %}
        <li>{{ item }}</li>
        {% endfor %}
    </ul>
    {% endif %}
</body>
</html>
"""
            )
            
            yield template_dir

    @pytest.fixture
    def template_renderer(self, temp_template_dir):
        """建立模板渲染服務"""
        return TemplateRenderer(templates_dir=temp_template_dir)

    def test_render_html_simple(self, template_renderer: TemplateRenderer):
        """測試渲染簡單 HTML 模板"""
        context = {
            "title": "測試報告",
            "date": datetime(2025, 1, 27),
            "items": ["項目1", "項目2", "項目3"],
        }
        
        html = template_renderer.render_html("test_template.html", context)
        
        assert "測試報告" in html
        assert "2025-01-27" in html
        assert "項目1" in html
        assert "項目2" in html
        assert "項目3" in html

    def test_render_html_with_condition(self, template_renderer: TemplateRenderer):
        """測試渲染帶有條件判斷的 HTML 模板"""
        context = {
            "title": "測試報告",
            "date": datetime(2025, 1, 27),
            "items": None,  # 測試條件判斷
        }
        
        html = template_renderer.render_html("test_template.html", context)
        
        assert "測試報告" in html
        assert "2025-01-27" in html
        assert "<ul>" not in html  # items 為 None，不應該渲染 ul

    def test_render_html_template_not_found(self, template_renderer: TemplateRenderer):
        """測試模板檔案不存在的情況"""
        with pytest.raises(Exception):  # Jinja2 會拋出 TemplateNotFound
            template_renderer.render_html("non_existent.html", {})

    @pytest.mark.skipif(
        True, reason="需要安裝 WeasyPrint，且需要系統字體支援"
    )
    def test_render_pdf(self, template_renderer: TemplateRenderer):
        """測試渲染 PDF（需要 WeasyPrint）"""
        context = {
            "title": "測試報告",
            "date": datetime(2025, 1, 27),
            "items": ["項目1", "項目2"],
        }
        
        pdf_bytes = template_renderer.render_pdf("test_template.html", context)
        
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        # PDF 檔案應該以 PDF 標頭開始
        assert pdf_bytes.startswith(b"%PDF")

    def test_render_pdf_without_weasyprint(self, temp_template_dir):
        """測試 PDF 渲染時 WeasyPrint 未安裝的情況"""
        # 建立一個不導入 WeasyPrint 的環境
        import sys
        original_modules = sys.modules.copy()
        
        # 模擬 WeasyPrint 未安裝
        if "weasyprint" in sys.modules:
            del sys.modules["weasyprint"]
        
        try:
            template_renderer = TemplateRenderer(templates_dir=temp_template_dir)
            context = {"title": "測試", "date": datetime.now(), "items": []}
            
            with pytest.raises(ImportError, match="WeasyPrint 未安裝"):
                template_renderer.render_pdf("test_template.html", context)
        finally:
            # 恢復原始模組
            sys.modules.clear()
            sys.modules.update(original_modules)


class TestCISOWeeklyReportTemplate:
    """測試 CISO 週報模板"""

    @pytest.fixture
    def template_renderer(self):
        """建立模板渲染服務（使用專案模板目錄）"""
        # 使用專案的模板目錄
        current_dir = Path(__file__).parent.parent.parent
        templates_dir = current_dir / "reporting_notification" / "infrastructure" / "templates"
        return TemplateRenderer(templates_dir=templates_dir)

    @pytest.fixture
    def sample_report_data(self):
        """建立範例週報資料"""
        return WeeklyReportData(
            period_start=datetime(2025, 1, 20),
            period_end=datetime(2025, 1, 27),
            total_threats=10,
            critical_threats=3,
            critical_threat_list=[
                {
                    "cve_id": "CVE-2025-0001",
                    "title": "測試威脅 1",
                    "risk_score": 9.0,
                    "risk_level": "Critical",
                    "affected_asset_count": 5,
                },
                {
                    "cve_id": "CVE-2025-0002",
                    "title": "測試威脅 2",
                    "risk_score": 8.5,
                    "risk_level": "High",
                    "affected_asset_count": 3,
                },
            ],
            affected_assets_by_type={"Server": 10, "Workstation": 5},
            affected_assets_by_importance={"High-High": 3, "Medium-Medium": 7},
            risk_trend={
                "this_week": {"threat_count": 10, "avg_risk_score": 7.5},
                "last_week": {"threat_count": 8, "avg_risk_score": 7.0},
                "threat_count_change": 2,
                "risk_score_change": 0.5,
                "threat_count_trend": "上升",
                "risk_score_trend": "上升",
            },
            business_risk_description="本週發現多個嚴重威脅，建議優先處理。",
        )

    def test_render_ciso_weekly_report_html(
        self, template_renderer: TemplateRenderer, sample_report_data: WeeklyReportData
    ):
        """測試渲染 CISO 週報 HTML"""
        context = {
            "report_title": f"CISO 週報 - {sample_report_data.period_end.strftime('%Y年%m月%d日')}",
            "period_start": sample_report_data.period_start,
            "period_end": sample_report_data.period_end,
            "total_threats": sample_report_data.total_threats,
            "critical_threats": sample_report_data.critical_threats,
            "critical_threat_list": sample_report_data.critical_threat_list,
            "affected_assets_by_type": sample_report_data.affected_assets_by_type,
            "affected_assets_by_importance": sample_report_data.affected_assets_by_importance,
            "risk_trend": sample_report_data.risk_trend,
            "business_risk_description": sample_report_data.business_risk_description,
            "generated_at": datetime.utcnow(),
        }
        
        html = template_renderer.render_html("ciso_weekly_report.html", context)
        
        # 驗證關鍵內容
        assert "CISO 週報" in html
        assert "10" in html  # 威脅總數
        assert "3" in html  # 嚴重威脅數量
        assert "CVE-2025-0001" in html
        assert "CVE-2025-0002" in html
        assert "測試威脅 1" in html
        assert "測試威脅 2" in html
        assert "Server" in html
        assert "Workstation" in html
        assert "本週發現多個嚴重威脅" in html

    def test_render_ciso_weekly_report_without_business_description(
        self, template_renderer: TemplateRenderer, sample_report_data: WeeklyReportData
    ):
        """測試渲染沒有業務風險描述的 CISO 週報"""
        sample_report_data.business_risk_description = None
        
        context = {
            "report_title": f"CISO 週報 - {sample_report_data.period_end.strftime('%Y年%m月%d日')}",
            "period_start": sample_report_data.period_start,
            "period_end": sample_report_data.period_end,
            "total_threats": sample_report_data.total_threats,
            "critical_threats": sample_report_data.critical_threats,
            "critical_threat_list": sample_report_data.critical_threat_list,
            "affected_assets_by_type": sample_report_data.affected_assets_by_type,
            "affected_assets_by_importance": sample_report_data.affected_assets_by_importance,
            "risk_trend": sample_report_data.risk_trend,
            "business_risk_description": None,
            "generated_at": datetime.utcnow(),
        }
        
        html = template_renderer.render_html("ciso_weekly_report.html", context)
        
        # 驗證業務風險描述區塊不存在
        assert "業務風險描述" not in html or "business_risk_description" not in html

