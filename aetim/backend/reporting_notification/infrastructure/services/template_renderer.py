"""
報告模板渲染服務

負責渲染報告模板，支援 HTML 和 PDF 格式。
"""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
import structlog

logger = structlog.get_logger(__name__)


class TemplateRenderer:
    """
    模板渲染服務
    
    負責渲染報告模板，支援 HTML 和 PDF 格式。
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        初始化模板渲染服務
        
        Args:
            templates_dir: 模板目錄路徑（可選，預設為當前模組的 templates 目錄）
        """
        if templates_dir is None:
            # 預設使用當前模組的 templates 目錄
            current_dir = Path(__file__).parent.parent
            templates_dir = current_dir / "templates"
        
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化 Jinja2 環境
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # 添加自訂過濾器
        self.env.filters["format"] = lambda value, fmt: fmt % value
    
    def render_html(
        self,
        template_name: str,
        context: Dict[str, Any],
    ) -> str:
        """
        渲染 HTML 模板
        
        Args:
            template_name: 模板檔案名稱（例如：ciso_weekly_report.html）
            context: 模板上下文變數
        
        Returns:
            str: 渲染後的 HTML 內容
        
        Raises:
            FileNotFoundError: 當模板檔案不存在時
            TemplateError: 當模板渲染失敗時
        """
        try:
            template = self.env.get_template(template_name)
            html_content = template.render(**context)
            
            logger.debug(
                "HTML 模板渲染成功",
                template_name=template_name,
            )
            
            return html_content
            
        except Exception as e:
            logger.error(
                "HTML 模板渲染失敗",
                template_name=template_name,
                error=str(e),
                exc_info=True,
            )
            raise
    
    def render_pdf(
        self,
        template_name: str,
        context: Dict[str, Any],
    ) -> bytes:
        """
        渲染 PDF 模板（透過 HTML 轉換）
        
        Args:
            template_name: 模板檔案名稱（例如：ciso_weekly_report.html）
            context: 模板上下文變數
        
        Returns:
            bytes: PDF 檔案的二進位內容
        
        Raises:
            FileNotFoundError: 當模板檔案不存在時
            TemplateError: 當模板渲染失敗時
            ImportError: 當 WeasyPrint 未安裝時
        """
        try:
            # 先渲染 HTML
            html_content = self.render_html(template_name, context)
            
            # 使用 WeasyPrint 轉換為 PDF
            try:
                from weasyprint import HTML, CSS
                from weasyprint.text.fonts import FontConfiguration
            except ImportError:
                logger.error(
                    "WeasyPrint 未安裝，無法生成 PDF",
                    hint="請執行: pip install weasyprint",
                )
                raise ImportError(
                    "WeasyPrint 未安裝。請執行: pip install weasyprint"
                )
            
            # 生成 PDF
            font_config = FontConfiguration()
            html_doc = HTML(string=html_content)
            
            # 添加 CSS 樣式（用於 PDF 優化）
            pdf_css = CSS(
                string="""
                @page {
                    size: A4;
                    margin: 2cm;
                }
                body {
                    font-family: "Microsoft JhengHei", "Arial", sans-serif;
                }
                """,
                font_config=font_config,
            )
            
            pdf_bytes = html_doc.write_pdf(stylesheets=[pdf_css], font_config=font_config)
            
            logger.info(
                "PDF 生成成功",
                template_name=template_name,
                pdf_size=len(pdf_bytes),
            )
            
            return pdf_bytes
            
        except ImportError:
            raise
        except Exception as e:
            logger.error(
                "PDF 生成失敗",
                template_name=template_name,
                error=str(e),
                exc_info=True,
            )
            raise
    
    def render_text(
        self,
        template_name: str,
        context: Dict[str, Any],
    ) -> str:
        """
        渲染 TEXT 模板
        
        Args:
            template_name: 模板檔案名稱（例如：it_ticket.txt）
            context: 模板上下文變數
        
        Returns:
            str: 渲染後的 TEXT 內容
        
        Raises:
            FileNotFoundError: 當模板檔案不存在時
            TemplateError: 當模板渲染失敗時
        """
        try:
            template = self.env.get_template(template_name)
            text_content = template.render(**context)
            
            logger.debug(
                "TEXT 模板渲染成功",
                template_name=template_name,
            )
            
            return text_content
            
        except Exception as e:
            logger.error(
                "TEXT 模板渲染失敗",
                template_name=template_name,
                error=str(e),
                exc_info=True,
            )
            raise

