"""
通知排程服務（Application Layer）

提供通知發送的排程管理功能，使用 APScheduler。
"""

import asyncio
from typing import Dict, Any
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
import structlog

from ...domain.value_objects.notification_type import NotificationType
from ...domain.interfaces.notification_rule_repository import INotificationRuleRepository
from ..services.daily_high_risk_summary_service import DailyHighRiskSummaryService

logger = structlog.get_logger(__name__)


class NotificationScheduleService:
    """
    通知排程服務
    
    提供通知發送的排程管理功能，支援：
    - 設定每日高風險威脅摘要排程（AC-020-3）
    - 動態新增/移除排程任務
    - 任務狀態追蹤
    """
    
    def __init__(
        self,
        notification_rule_repository: INotificationRuleRepository,
        daily_summary_service: DailyHighRiskSummaryService,
    ):
        """
        初始化通知排程服務
        
        Args:
            notification_rule_repository: 通知規則 Repository
            daily_summary_service: 每日高風險威脅摘要服務
        """
        self.notification_rule_repository = notification_rule_repository
        self.daily_summary_service = daily_summary_service
        
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
            timezone='UTC'
        )
        
        self._job_id_prefix = "daily_summary_"
        self._running_jobs: Dict[str, bool] = {}  # 追蹤正在執行的任務
    
    async def start(self) -> None:
        """
        啟動排程服務
        
        啟動排程器並載入所有啟用的排程任務。
        """
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("通知排程服務已啟動")
            
            # 載入所有啟用的通知排程
            await self.load_schedules()
    
    async def stop(self) -> None:
        """
        停止排程服務
        
        停止排程器並清理所有排程任務。
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("通知排程服務已停止")
    
    async def load_schedules(self) -> None:
        """
        載入所有啟用的通知排程任務
        
        從資料庫載入所有啟用的通知規則，並為每個規則建立排程任務。
        """
        try:
            # 取得啟用的高風險每日摘要通知規則
            notification_rule = await self.notification_rule_repository.get_by_type(
                NotificationType.HIGH_RISK_DAILY
            )
            
            if notification_rule and notification_rule.is_enabled:
                if notification_rule.send_time:
                    await self.add_daily_summary_schedule(
                        send_time=notification_rule.send_time,
                    )
                    logger.info(
                        "已載入每日高風險威脅摘要排程",
                        send_time=notification_rule.send_time.strftime("%H:%M"),
                    )
                else:
                    # 如果沒有設定發送時間，使用預設時間（每日上午 8:00）
                    default_time = time(8, 0)
                    await self.add_daily_summary_schedule(send_time=default_time)
                    logger.info(
                        "已載入每日高風險威脅摘要排程（使用預設時間）",
                        send_time=default_time.strftime("%H:%M"),
                    )
            else:
                logger.info("沒有啟用的每日高風險威脅摘要通知規則")
                
        except Exception as e:
            logger.error(
                "載入通知排程失敗",
                error=str(e),
                exc_info=True,
            )
    
    async def add_daily_summary_schedule(
        self,
        send_time: time,
    ) -> None:
        """
        新增每日高風險威脅摘要排程（AC-020-3, AC-020-4）
        
        Args:
            send_time: 發送時間
        """
        job_id = f"{self._job_id_prefix}high_risk_daily"
        
        # 移除現有任務（如果存在）
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        # 建立 Cron 觸發器（每日指定時間執行）
        trigger = CronTrigger(
            hour=send_time.hour,
            minute=send_time.minute,
            timezone='UTC'
        )
        
        # 新增排程任務
        self.scheduler.add_job(
            func=self._execute_daily_summary,
            trigger=trigger,
            id=job_id,
            name="每日高風險威脅摘要",
            replace_existing=True,
        )
        
        logger.info(
            "已新增每日高風險威脅摘要排程",
            job_id=job_id,
            send_time=send_time.strftime("%H:%M"),
        )
    
    async def remove_daily_summary_schedule(self) -> None:
        """
        移除每日高風險威脅摘要排程
        """
        job_id = f"{self._job_id_prefix}high_risk_daily"
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info("已移除每日高風險威脅摘要排程", job_id=job_id)
    
    async def _execute_daily_summary(self) -> None:
        """
        執行每日高風險威脅摘要任務
        
        此方法由 APScheduler 調用，不應直接調用。
        """
        job_id = f"{self._job_id_prefix}high_risk_daily"
        
        # 檢查任務是否正在執行
        if self._running_jobs.get(job_id, False):
            logger.warning(
                "每日高風險威脅摘要任務正在執行中，跳過本次執行",
                job_id=job_id,
            )
            return
        
        try:
            self._running_jobs[job_id] = True
            
            logger.info(
                "開始執行每日高風險威脅摘要任務",
                job_id=job_id,
                execution_time=datetime.utcnow().isoformat(),
            )
            
            # 發送摘要
            await self.daily_summary_service.send_summary()
            
            logger.info(
                "每日高風險威脅摘要任務執行完成",
                job_id=job_id,
            )
            
        except Exception as e:
            logger.error(
                "每日高風險威脅摘要任務執行失敗",
                job_id=job_id,
                error=str(e),
                exc_info=True,
            )
        finally:
            self._running_jobs[job_id] = False

