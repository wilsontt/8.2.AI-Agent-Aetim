"""
報告排程服務（Application Layer）

提供報告生成的排程管理功能，使用 APScheduler。
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
import structlog
import os

from ...domain.aggregates.report_schedule import ReportSchedule
from ...domain.value_objects.report_type import ReportType
from ...domain.value_objects.file_format import FileFormat
from ...domain.interfaces.report_schedule_repository import IReportScheduleRepository
from ..services.report_service import ReportService

logger = structlog.get_logger(__name__)


class ReportScheduleService:
    """
    報告排程服務
    
    提供報告生成的排程管理功能，支援：
    - 設定 CISO 週報排程（AC-016-1）
    - 動態新增/移除排程任務
    - 任務狀態追蹤
    - 任務執行歷史記錄（AC-016-4）
    """
    
    def __init__(
        self,
        schedule_repository: IReportScheduleRepository,
        report_service: ReportService,
    ):
        """
        初始化排程服務
        
        Args:
            schedule_repository: 報告排程 Repository
            report_service: 報告服務
        """
        self.schedule_repository = schedule_repository
        self.report_service = report_service
        
        # 從環境變數讀取預設時區
        self._default_timezone = os.getenv('TZ', 'Asia/Taipei')
        
        # 初始化 APScheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 1,  # 同一時間只允許一個實例執行
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=self._default_timezone  # 使用從環境變數讀取的時區
        )
        
        self._job_id_prefix = "report_generation_"
        self._running_jobs: Dict[str, bool] = {}  # 追蹤正在執行的任務
    
    async def start(self) -> None:
        """
        啟動排程服務
        
        啟動排程器並載入所有啟用的排程任務。
        """
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("報告排程服務已啟動")
            
            # 載入所有啟用的報告排程
            await self.load_schedules()
    
    async def stop(self) -> None:
        """
        停止排程服務
        
        停止排程器並清理所有排程任務。
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("報告排程服務已停止")
    
    async def load_schedules(self) -> None:
        """
        載入所有啟用的排程任務
        
        從資料庫載入所有啟用的報告排程，並為每個排程建立任務。
        """
        try:
            schedules = await self.schedule_repository.get_all_enabled()
            
            logger.info(
                f"載入 {len(schedules)} 個報告排程",
                extra={"schedule_count": len(schedules)}
            )
            
            for schedule in schedules:
                await self.add_schedule(schedule)
                
        except Exception as e:
            logger.error(
                f"載入排程失敗：{str(e)}",
                extra={"error": str(e)},
                exc_info=True,
            )
    
    async def create_schedule(
        self,
        report_type: ReportType,
        cron_expression: str,
        recipients: List[str],
        file_format: str = "HTML",
        timezone: Optional[str] = None,
        is_enabled: bool = True,
    ) -> ReportSchedule:
        """
        建立報告排程（AC-016-1）
        
        Args:
            report_type: 報告類型
            cron_expression: Cron 表達式（例如："0 9 * * 1" 表示每週一上午 9:00）
            recipients: 收件人清單（Email 地址）
            file_format: 檔案格式（預設：HTML）
            timezone: 時區設定（預設：使用環境變數 TZ）
            is_enabled: 是否啟用（預設：True）
        
        Returns:
            ReportSchedule: 報告排程聚合根
        """
        # 如果未指定時區，使用預設時區
        if timezone is None:
            timezone = self._default_timezone
        
        schedule = ReportSchedule.create(
            report_type=report_type,
            cron_expression=cron_expression,
            recipients=recipients,
            file_format=file_format,
            timezone=timezone,
            is_enabled=is_enabled,
        )
        
        await self.schedule_repository.save(schedule)
        
        # 如果啟用，立即新增到排程器
        if schedule.is_enabled:
            await self.add_schedule(schedule)
        
        logger.info(
            "報告排程已建立",
            schedule_id=schedule.id,
            report_type=schedule.report_type.value,
            cron_expression=cron_expression,
        )
        
        return schedule
    
    async def add_schedule(self, schedule: ReportSchedule) -> None:
        """
        新增排程任務
        
        Args:
            schedule: 報告排程聚合根
        """
        if not schedule.is_enabled:
            logger.warning(
                f"報告排程已停用，跳過：{schedule.report_type.value}",
                extra={"schedule_id": schedule.id}
            )
            return
        
        job_id = f"{self._job_id_prefix}{schedule.id}"
        
        # 如果排程已存在，先移除
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        # 建立 Cron 觸發器
        # Cron 表達式格式：分 時 日 月 週
        # 例如："0 9 * * 1" 表示每週一上午 9:00
        try:
            cron_parts = schedule.cron_expression.split()
            if len(cron_parts) != 5:
                raise ValueError(f"無效的 Cron 表達式：{schedule.cron_expression}")
            
            trigger = CronTrigger(
                minute=cron_parts[0],
                hour=cron_parts[1],
                day=cron_parts[2],
                month=cron_parts[3],
                day_of_week=cron_parts[4],
                timezone=schedule.timezone  # 使用排程的時區設定
            )
        except Exception as e:
            logger.error(
                f"無法建立 Cron 觸發器：{str(e)}",
                extra={
                    "schedule_id": schedule.id,
                    "cron_expression": schedule.cron_expression,
                    "error": str(e),
                }
            )
            return
        
        # 新增排程任務
        self.scheduler.add_job(
            func=self._execute_report_generation,
            trigger=trigger,
            id=job_id,
            name=f"生成報告：{schedule.report_type.value}",
            args=[schedule.id],
            replace_existing=True,
        )
        
        # 更新下次執行時間
        job = self.scheduler.get_job(job_id)
        if job and job.next_run_time:
            schedule.update_run_times(next_run_at=job.next_run_time)
            await self.schedule_repository.save(schedule)
        
        logger.info(
            f"已新增報告排程任務：{schedule.report_type.value}",
            extra={
                "schedule_id": schedule.id,
                "report_type": schedule.report_type.value,
                "cron_expression": schedule.cron_expression,
                "job_id": job_id,
            }
        )
    
    async def remove_schedule(self, schedule_id: str) -> None:
        """
        移除排程任務
        
        Args:
            schedule_id: 排程 ID
        """
        job_id = f"{self._job_id_prefix}{schedule_id}"
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(
                "已移除報告排程任務",
                extra={"schedule_id": schedule_id, "job_id": job_id}
            )
        else:
            logger.warning(
                "報告排程任務不存在",
                extra={"schedule_id": schedule_id, "job_id": job_id}
            )
    
    async def update_schedule(
        self,
        schedule_id: str,
        cron_expression: Optional[str] = None,
        recipients: Optional[List[str]] = None,
        file_format: Optional[str] = None,
        timezone: Optional[str] = None,
        is_enabled: Optional[bool] = None,
    ) -> ReportSchedule:
        """
        更新排程任務
        
        Args:
            schedule_id: 排程 ID
            cron_expression: 新的 Cron 表達式（可選）
            recipients: 新的收件人清單（可選）
            file_format: 新的檔案格式（可選）
            timezone: 新的時區設定（可選）
            is_enabled: 是否啟用（可選）
        
        Returns:
            ReportSchedule: 更新後的報告排程聚合根
        """
        schedule = await self.schedule_repository.get_by_id(schedule_id)
        if not schedule:
            raise ValueError(f"找不到報告排程：{schedule_id}")
        
        # 先移除舊的排程
        await self.remove_schedule(schedule_id)
        
        # 更新排程設定
        schedule.update_schedule(
            cron_expression=cron_expression,
            recipients=recipients,
            file_format=file_format,
            timezone=timezone,
            is_enabled=is_enabled,
        )
        
        await self.schedule_repository.save(schedule)
        
        # 如果啟用，新增新的排程
        if schedule.is_enabled:
            await self.add_schedule(schedule)
        
        logger.info(
            "報告排程已更新",
            schedule_id=schedule_id,
        )
        
        return schedule
    
    async def execute_schedule_now(self, schedule_id: str) -> Dict[str, Any]:
        """
        立即執行排程任務（手動觸發）
        
        Args:
            schedule_id: 排程 ID
        
        Returns:
            Dict: 執行結果
        """
        schedule = await self.schedule_repository.get_by_id(schedule_id)
        if not schedule:
            return {
                "success": False,
                "error": f"找不到報告排程：{schedule_id}",
            }
        
        return await self._execute_report_generation(schedule_id)
    
    async def _execute_report_generation(self, schedule_id: str) -> Dict[str, Any]:
        """
        執行報告生成任務（AC-016-4）
        
        Args:
            schedule_id: 排程 ID
        
        Returns:
            Dict: 執行結果
        """
        job_id = f"{self._job_id_prefix}{schedule_id}"
        
        # 檢查任務是否正在執行
        if self._running_jobs.get(job_id, False):
            logger.warning(
                "任務正在執行中，跳過本次執行",
                extra={"schedule_id": schedule_id, "job_id": job_id}
            )
            return {
                "success": False,
                "error": "任務正在執行中",
            }
        
        # 標記任務為執行中
        self._running_jobs[job_id] = True
        
        try:
            logger.info(
                "開始執行報告生成任務",
                extra={"schedule_id": schedule_id, "job_id": job_id}
            )
            
            # 取得排程設定
            schedule = await self.schedule_repository.get_by_id(schedule_id)
            if not schedule:
                raise ValueError(f"找不到報告排程：{schedule_id}")
            
            # 計算報告期間（上週一到上週日）
            now = datetime.utcnow()
            # 找到上週一
            days_since_monday = (now.weekday() + 1) % 7
            if days_since_monday == 0:
                days_since_monday = 7
            period_end = now - timedelta(days=days_since_monday)
            period_end = period_end.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_start = period_end - timedelta(days=6)
            period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # 生成報告
            file_format = FileFormat.from_string(schedule.file_format)
            report = await self.report_service.generate_ciso_weekly_report(
                period_start=period_start,
                period_end=period_end,
                file_format=file_format,
            )
            
            # 更新排程的最後執行時間
            schedule.update_run_times(last_run_at=datetime.utcnow())
            
            # 更新下次執行時間
            job = self.scheduler.get_job(job_id)
            if job and job.next_run_time:
                schedule.update_run_times(next_run_at=job.next_run_time)
            
            await self.schedule_repository.save(schedule)
            
            # TODO: 發送 Email 通知（AC-016-3）
            # 這裡應該呼叫 Email 服務發送報告給收件人
            # 目前僅記錄日誌
            logger.info(
                "報告生成完成，應發送 Email 通知",
                extra={
                    "schedule_id": schedule_id,
                    "report_id": report.id,
                    "recipients": schedule.recipients,
                }
            )
            
            logger.info(
                "報告生成任務執行完成",
                extra={
                    "schedule_id": schedule_id,
                    "job_id": job_id,
                    "report_id": report.id,
                    "success": True,
                }
            )
            
            return {
                "success": True,
                "report_id": report.id,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
            }
            
        except Exception as e:
            error_msg = f"執行報告生成任務時發生錯誤：{str(e)}"
            logger.error(
                error_msg,
                extra={"schedule_id": schedule_id, "job_id": job_id, "error": str(e)},
                exc_info=True,
            )
            
            return {
                "success": False,
                "error": error_msg,
            }
        finally:
            # 標記任務為已完成
            self._running_jobs[job_id] = False
    
    def get_schedule_status(self, schedule_id: str) -> Dict[str, Any]:
        """
        取得排程狀態
        
        Args:
            schedule_id: 排程 ID
        
        Returns:
            Dict: 排程狀態資訊
        """
        job_id = f"{self._job_id_prefix}{schedule_id}"
        job = self.scheduler.get_job(job_id)
        
        if not job:
            return {
                "exists": False,
                "enabled": False,
            }
        
        return {
            "exists": True,
            "enabled": True,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "is_running": self._running_jobs.get(job_id, False),
        }
    
    def get_all_schedules(self) -> List[Dict[str, Any]]:
        """
        取得所有排程狀態
        
        Returns:
            List[Dict]: 所有排程的狀態資訊
        """
        jobs = self.scheduler.get_jobs()
        schedules = []
        
        for job in jobs:
            if job.id.startswith(self._job_id_prefix):
                schedule_id = job.id.replace(self._job_id_prefix, "")
                schedules.append({
                    "schedule_id": schedule_id,
                    "job_id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "is_running": self._running_jobs.get(job.id, False),
                })
        
        return schedules

