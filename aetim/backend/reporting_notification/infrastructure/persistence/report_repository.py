"""
報告 Repository 實作

實作報告的資料存取邏輯，包含資料庫和檔案系統操作。
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
import structlog

from ...domain.interfaces.report_repository import IReportRepository
from ...domain.aggregates.report import Report
from ...domain.value_objects.report_type import ReportType
from ...domain.value_objects.file_format import FileFormat
from .models import Report as ReportModel

logger = structlog.get_logger(__name__)


class ReportRepository(IReportRepository):
    """
    報告 Repository 實作
    
    負責報告的資料存取，包含：
    1. 資料庫操作（報告元資料）
    2. 檔案系統操作（報告檔案）
    """
    
    def __init__(self, session: AsyncSession, reports_base_path: str = "reports"):
        """
        初始化 Repository
        
        Args:
            session: 資料庫會話
            reports_base_path: 報告檔案基礎路徑（預設：reports）
        """
        self.session = session
        self.reports_base_path = Path(reports_base_path)
        # 確保基礎目錄存在
        self.reports_base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_directory_path(self, generated_at: datetime) -> Path:
        """
        取得報告目錄路徑（AC-015-5）
        
        格式：reports/yyyy/yyyymm/
        
        Args:
            generated_at: 生成時間
        
        Returns:
            Path: 目錄路徑
        """
        year = generated_at.strftime("%Y")
        year_month = generated_at.strftime("%Y%m")
        return self.reports_base_path / year / year_month
    
    def _get_file_path(
        self,
        report_type: ReportType,
        file_format: FileFormat,
        generated_at: datetime,
    ) -> Path:
        """
        取得報告檔案路徑（AC-015-6）
        
        格式：reports/yyyy/yyyymm/{ReportType}_Report_yyyy-mm-dd.{extension}
        
        Args:
            report_type: 報告類型
            file_format: 檔案格式
            generated_at: 生成時間
        
        Returns:
            Path: 檔案路徑
        """
        directory = self._get_directory_path(generated_at)
        date_str = generated_at.strftime("%Y-%m-%d")
        extension = file_format.get_file_extension()
        
        # 檔案命名格式：CISO_Weekly_Report_2025-01-27.html
        filename = f"{report_type.value}_Report_{date_str}{extension}"
        
        return directory / filename
    
    async def save(self, report: Report, file_content: bytes) -> None:
        """
        儲存報告記錄和檔案
        
        Args:
            report: 報告聚合根
            file_content: 報告檔案內容（位元組）
        """
        try:
            # 1. 建立目錄結構（AC-015-5）
            file_path = self._get_file_path(
                report.report_type,
                report.file_format,
                report.generated_at,
            )
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 2. 儲存報告檔案
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            logger.info(
                "報告檔案已儲存",
                report_id=report.id,
                file_path=str(file_path),
            )
            
            # 3. 更新報告的檔案路徑（使用相對於 reports_base_path 的相對路徑）
            try:
                relative_path = str(file_path.relative_to(self.reports_base_path))
            except ValueError:
                # 如果無法計算相對路徑，使用絕對路徑
                relative_path = str(file_path)
            report.file_path = relative_path
            
            # 4. 儲存報告元資料到資料庫
            await self._save_to_database(report)
            
            logger.info(
                "報告已儲存",
                report_id=report.id,
                report_type=report.report_type.value,
            )
            
        except Exception as e:
            logger.error(
                "儲存報告失敗",
                report_id=report.id,
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def _save_to_database(self, report: Report) -> None:
        """
        儲存報告元資料到資料庫
        
        Args:
            report: 報告聚合根
        """
        # 檢查報告是否存在
        stmt = select(ReportModel).where(ReportModel.id == report.id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        
        # 準備元資料 JSON
        metadata_json = None
        if report.metadata:
            metadata_json = json.dumps(report.metadata, ensure_ascii=False, indent=2)
        
        if existing:
            # 更新現有報告
            existing.report_type = report.report_type.value
            existing.title = report.title
            existing.file_path = report.file_path
            existing.file_format = report.file_format.value
            existing.generated_at = report.generated_at
            existing.period_start = report.period_start
            existing.period_end = report.period_end
            existing.summary = report.summary
            existing.metadata = metadata_json
        else:
            # 新增報告
            new_report = ReportModel(
                id=report.id,
                report_type=report.report_type.value,
                title=report.title,
                file_path=report.file_path,
                file_format=report.file_format.value,
                generated_at=report.generated_at,
                period_start=report.period_start,
                period_end=report.period_end,
                summary=report.summary,
                metadata=metadata_json,
            )
            self.session.add(new_report)
        
        await self.session.flush()
    
    async def get_by_id(self, report_id: str) -> Optional[Report]:
        """
        依 ID 查詢報告
        
        Args:
            report_id: 報告 ID
        
        Returns:
            Optional[Report]: 報告聚合根，如果不存在則返回 None
        """
        try:
            stmt = select(ReportModel).where(ReportModel.id == report_id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return None
            
            return self._to_domain(model)
            
        except Exception as e:
            logger.error(
                "查詢報告失敗",
                report_id=report_id,
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def get_all(
        self,
        report_type: Optional[ReportType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "generated_at",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """
        查詢所有報告（支援分頁、排序、篩選）
        
        Args:
            report_type: 報告類型篩選（可選）
            start_date: 開始日期篩選（可選）
            end_date: 結束日期篩選（可選）
            page: 頁碼（從 1 開始）
            page_size: 每頁數量
            sort_by: 排序欄位（預設：generated_at）
            sort_order: 排序順序（asc/desc，預設：desc）
        
        Returns:
            Dict[str, Any]: 包含 items（報告清單）、total（總數）、page、page_size、total_pages
        """
        try:
            # 建立查詢
            stmt = select(ReportModel)
            count_stmt = select(func.count(ReportModel.id))
            
            # 建立篩選條件
            conditions = []
            
            if report_type:
                conditions.append(ReportModel.report_type == report_type.value)
            
            if start_date:
                conditions.append(ReportModel.generated_at >= start_date)
            
            if end_date:
                conditions.append(ReportModel.generated_at <= end_date)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
                count_stmt = count_stmt.where(and_(*conditions))
            
            # 排序
            sort_column = getattr(ReportModel, sort_by, ReportModel.generated_at)
            if sort_order.lower() == "desc":
                stmt = stmt.order_by(sort_column.desc())
            else:
                stmt = stmt.order_by(sort_column.asc())
            
            # 分頁
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)
            
            # 執行查詢
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            # 計算總數
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar()
            
            # 轉換為領域模型
            items = [self._to_domain(model) for model in models]
            
            # 計算總頁數
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
            
        except Exception as e:
            logger.error(
                "查詢報告清單失敗",
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def get_file_path(self, report_id: str) -> Optional[str]:
        """
        取得報告檔案路徑
        
        Args:
            report_id: 報告 ID
        
        Returns:
            Optional[str]: 檔案路徑，如果不存在則返回 None
        """
        try:
            report = await self.get_by_id(report_id)
            if not report:
                return None
            
            # 返回完整路徑
            # 如果 file_path 是相對路徑，則相對於 reports_base_path
            if os.path.isabs(report.file_path):
                full_path = Path(report.file_path)
            else:
                full_path = self.reports_base_path / report.file_path
            return str(full_path) if full_path.exists() else None
            
        except Exception as e:
            logger.error(
                "取得報告檔案路徑失敗",
                report_id=report_id,
                error=str(e),
                exc_info=True,
            )
            return None
    
    async def get_file_content(self, report_id: str) -> Optional[bytes]:
        """
        取得報告檔案內容
        
        Args:
            report_id: 報告 ID
        
        Returns:
            Optional[bytes]: 檔案內容（位元組），如果不存在則返回 None
        """
        try:
            file_path = await self.get_file_path(report_id)
            if not file_path or not os.path.exists(file_path):
                return None
            
            with open(file_path, "rb") as f:
                return f.read()
            
        except Exception as e:
            logger.error(
                "取得報告檔案內容失敗",
                report_id=report_id,
                error=str(e),
                exc_info=True,
            )
            return None
    
    def _to_domain(self, model: ReportModel) -> Report:
        """
        將資料庫模型轉換為領域模型
        
        Args:
            model: 資料庫模型
        
        Returns:
            Report: 領域模型
        """
        # 解析元資料 JSON
        metadata = None
        if model.metadata:
            try:
                metadata = json.loads(model.metadata)
            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    "無法解析報告元資料 JSON",
                    report_id=model.id,
                )
        
        # 建立領域模型
        report = Report(
            id=model.id,
            report_type=ReportType.from_string(model.report_type),
            title=model.title,
            file_path=model.file_path,
            file_format=FileFormat.from_string(model.file_format),
            generated_at=model.generated_at,
            period_start=model.period_start,
            period_end=model.period_end,
            summary=model.summary,
            metadata=metadata,
            created_at=model.created_at,
        )
        
        return report

