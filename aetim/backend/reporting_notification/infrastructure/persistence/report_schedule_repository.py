"""
報告排程 Repository 實作

實作報告排程的資料持久化邏輯。
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import structlog

from ...domain.interfaces.report_schedule_repository import IReportScheduleRepository
from ...domain.aggregates.report_schedule import ReportSchedule
from ...domain.value_objects.report_type import ReportType
from .models import ReportSchedule as ReportScheduleModel

logger = structlog.get_logger(__name__)


class ReportScheduleRepository(IReportScheduleRepository):
    """
    報告排程 Repository 實作
    
    負責報告排程的資料存取，使用 SQLAlchemy。
    """
    
    def __init__(self, session: AsyncSession):
        """
        初始化 Repository
        
        Args:
            session: 資料庫會話
        """
        self.session = session
    
    async def save(self, schedule: ReportSchedule) -> None:
        """
        儲存報告排程（新增或更新）
        
        Args:
            schedule: 報告排程聚合根
        """
        try:
            stmt = select(ReportScheduleModel).where(
                ReportScheduleModel.id == schedule.id
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # 更新現有記錄
                existing.report_type = schedule.report_type.value
                existing.cron_expression = schedule.cron_expression
                existing.is_enabled = schedule.is_enabled
                existing.recipients = json.dumps(schedule.recipients, ensure_ascii=False)
                existing.file_format = schedule.file_format
                existing.last_run_at = schedule.last_run_at
                existing.next_run_at = schedule.next_run_at
                existing.updated_at = schedule.updated_at
            else:
                # 新增新記錄
                schedule_model = ReportScheduleModel(
                    id=schedule.id,
                    report_type=schedule.report_type.value,
                    cron_expression=schedule.cron_expression,
                    is_enabled=schedule.is_enabled,
                    recipients=json.dumps(schedule.recipients, ensure_ascii=False),
                    file_format=schedule.file_format,
                    last_run_at=schedule.last_run_at,
                    next_run_at=schedule.next_run_at,
                    created_at=schedule.created_at,
                    updated_at=schedule.updated_at,
                )
                self.session.add(schedule_model)
            
            await self.session.flush()
            
            logger.info(
                "報告排程已儲存",
                schedule_id=schedule.id,
                report_type=schedule.report_type.value,
            )
        except Exception as e:
            logger.error(
                "儲存報告排程失敗",
                schedule_id=schedule.id,
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def get_by_id(self, schedule_id: str) -> Optional[ReportSchedule]:
        """
        依 ID 查詢報告排程
        
        Args:
            schedule_id: 排程 ID
        
        Returns:
            Optional[ReportSchedule]: 報告排程聚合根，如果不存在則返回 None
        """
        try:
            stmt = select(ReportScheduleModel).where(
                ReportScheduleModel.id == schedule_id
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model is None:
                return None
            
            return self._to_domain(model)
        except Exception as e:
            logger.error(
                "查詢報告排程失敗",
                schedule_id=schedule_id,
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def get_by_report_type(
        self, report_type: ReportType
    ) -> Optional[ReportSchedule]:
        """
        依報告類型查詢報告排程
        
        Args:
            report_type: 報告類型
        
        Returns:
            Optional[ReportSchedule]: 報告排程聚合根，如果不存在則返回 None
        """
        try:
            stmt = select(ReportScheduleModel).where(
                ReportScheduleModel.report_type == report_type.value
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model is None:
                return None
            
            return self._to_domain(model)
        except Exception as e:
            logger.error(
                "查詢報告排程失敗",
                report_type=report_type.value,
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def get_all_enabled(self) -> List[ReportSchedule]:
        """
        查詢所有啟用的報告排程
        
        Returns:
            List[ReportSchedule]: 報告排程聚合根清單
        """
        try:
            stmt = select(ReportScheduleModel).where(
                ReportScheduleModel.is_enabled == True
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._to_domain(model) for model in models]
        except Exception as e:
            logger.error(
                "查詢啟用的報告排程失敗",
                error=str(e),
                exc_info=True,
            )
            raise
    
    async def delete(self, schedule_id: str) -> None:
        """
        刪除報告排程
        
        Args:
            schedule_id: 排程 ID
        """
        try:
            stmt = select(ReportScheduleModel).where(
                ReportScheduleModel.id == schedule_id
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if model:
                await self.session.delete(model)
                await self.session.flush()
                
                logger.info(
                    "報告排程已刪除",
                    schedule_id=schedule_id,
                )
        except Exception as e:
            logger.error(
                "刪除報告排程失敗",
                schedule_id=schedule_id,
                error=str(e),
                exc_info=True,
            )
            raise
    
    def _to_domain(self, model: ReportScheduleModel) -> ReportSchedule:
        """將 ORM 模型轉換為領域聚合根"""
        recipients = []
        if model.recipients:
            try:
                recipients = json.loads(model.recipients)
            except json.JSONDecodeError:
                logger.warning(
                    f"無法解析收件人清單 JSON (ID: {model.id})"
                )
        
        return ReportSchedule(
            id=model.id,
            report_type=ReportType.from_string(model.report_type),
            cron_expression=model.cron_expression,
            is_enabled=model.is_enabled,
            recipients=recipients,
            file_format=model.file_format,
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_run_at=model.last_run_at,
            next_run_at=model.next_run_at,
        )

