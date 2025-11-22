"""
排程服務

提供威脅情資收集的排程管理功能。
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from ...domain.interfaces.threat_feed_repository import IThreatFeedRepository
from ...domain.aggregates.threat_feed import ThreatFeed
from ...domain.value_objects.collection_frequency import CollectionFrequency
from ...domain.value_objects.collection_status import CollectionStatus
from ..services.threat_collection_service import ThreatCollectionService
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class ScheduleService:
    """
    排程服務
    
    提供威脅情資收集的排程管理功能，支援：
    - 根據威脅來源的收集頻率設定排程
    - 動態新增/移除排程任務
    - 任務狀態追蹤
    - 任務執行歷史記錄
    """
    
    def __init__(
        self,
        feed_repository: IThreatFeedRepository,
        collection_service: ThreatCollectionService,
    ):
        """
        初始化排程服務
        
        Args:
            feed_repository: 威脅情資來源 Repository
            collection_service: 威脅收集服務
        """
        self.feed_repository = feed_repository
        self.collection_service = collection_service
        
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
        
        self._job_id_prefix = "threat_collection_"
        self._running_jobs: Dict[str, bool] = {}  # 追蹤正在執行的任務
    
    async def start(self) -> None:
        """
        啟動排程服務
        
        啟動排程器並載入所有啟用的排程任務。
        """
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("排程服務已啟動")
            
            # 載入所有啟用的威脅情資來源並建立排程
            await self.load_schedules()
    
    async def stop(self) -> None:
        """
        停止排程服務
        
        停止排程器並清理所有排程任務。
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("排程服務已停止")
    
    async def load_schedules(self) -> None:
        """
        載入所有啟用的排程任務
        
        從資料庫載入所有啟用的威脅情資來源，並為每個來源建立排程任務。
        """
        try:
            feeds = await self.feed_repository.get_enabled_feeds()
            
            logger.info(
                f"載入 {len(feeds)} 個威脅情資來源的排程",
                extra={"feed_count": len(feeds)}
            )
            
            for feed in feeds:
                await self.add_schedule(feed)
                
        except Exception as e:
            logger.error(
                f"載入排程失敗：{str(e)}",
                extra={"error": str(e)}
            )
    
    async def add_schedule(self, feed: ThreatFeed) -> None:
        """
        新增排程任務
        
        Args:
            feed: 威脅情資來源聚合根
        """
        if not feed.is_enabled:
            logger.warning(
                f"威脅情資來源已停用，跳過排程：{feed.name}",
                extra={"feed_id": feed.id, "feed_name": feed.name}
            )
            return
        
        if not feed.collection_frequency:
            logger.warning(
                f"威脅情資來源未設定收集頻率，跳過排程：{feed.name}",
                extra={"feed_id": feed.id, "feed_name": feed.name}
            )
            return
        
        job_id = f"{self._job_id_prefix}{feed.id}"
        
        # 如果排程已存在，先移除
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        
        # 根據收集頻率建立觸發器
        trigger = self._create_trigger(feed.collection_frequency)
        
        if not trigger:
            logger.warning(
                f"無法建立觸發器，跳過排程：{feed.name}",
                extra={"feed_id": feed.id, "feed_name": feed.name, "frequency": feed.collection_frequency.value}
            )
            return
        
        # 新增排程任務
        self.scheduler.add_job(
            func=self._execute_collection,
            trigger=trigger,
            id=job_id,
            name=f"收集威脅情資：{feed.name}",
            args=[feed.id],
            replace_existing=True,
        )
        
        logger.info(
            f"已新增排程任務：{feed.name}",
            extra={
                "feed_id": feed.id,
                "feed_name": feed.name,
                "frequency": feed.collection_frequency.value,
                "job_id": job_id,
            }
        )
    
    async def remove_schedule(self, feed_id: str) -> None:
        """
        移除排程任務
        
        Args:
            feed_id: 威脅情資來源 ID
        """
        job_id = f"{self._job_id_prefix}{feed_id}"
        
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(
                f"已移除排程任務",
                extra={"feed_id": feed_id, "job_id": job_id}
            )
        else:
            logger.warning(
                f"排程任務不存在",
                extra={"feed_id": feed_id, "job_id": job_id}
            )
    
    async def update_schedule(self, feed: ThreatFeed) -> None:
        """
        更新排程任務
        
        Args:
            feed: 威脅情資來源聚合根
        """
        # 先移除舊的排程
        await self.remove_schedule(feed.id)
        
        # 如果啟用，新增新的排程
        if feed.is_enabled:
            await self.add_schedule(feed)
    
    async def execute_schedule_now(self, feed_id: str) -> Dict[str, Any]:
        """
        立即執行排程任務（手動觸發）
        
        Args:
            feed_id: 威脅情資來源 ID
        
        Returns:
            Dict: 執行結果
        """
        feed = await self.feed_repository.get_by_id(feed_id)
        if not feed:
            return {
                "success": False,
                "error": f"找不到威脅情資來源：{feed_id}",
            }
        
        return await self._execute_collection(feed_id)
    
    async def _execute_collection(self, feed_id: str) -> Dict[str, Any]:
        """
        執行收集任務
        
        Args:
            feed_id: 威脅情資來源 ID
        
        Returns:
            Dict: 執行結果
        """
        job_id = f"{self._job_id_prefix}{feed_id}"
        
        # 檢查任務是否正在執行
        if self._running_jobs.get(job_id, False):
            logger.warning(
                f"任務正在執行中，跳過本次執行",
                extra={"feed_id": feed_id, "job_id": job_id}
            )
            return {
                "success": False,
                "error": "任務正在執行中",
            }
        
        # 標記任務為執行中
        self._running_jobs[job_id] = True
        
        try:
            logger.info(
                f"開始執行收集任務",
                extra={"feed_id": feed_id, "job_id": job_id}
            )
            
            # 執行收集（ThreatCollectionService 會自動更新收集狀態）
            result = await self.collection_service.collect_from_feed(feed_id, use_ai=True)
            
            logger.info(
                f"收集任務執行完成",
                extra={
                    "feed_id": feed_id,
                    "job_id": job_id,
                    "success": result["success"],
                    "threats_collected": result.get("threats_collected", 0),
                }
            )
            
            return result
            
        except Exception as e:
            error_msg = f"執行收集任務時發生錯誤：{str(e)}"
            logger.error(
                error_msg,
                extra={"feed_id": feed_id, "job_id": job_id, "error": str(e)}
            )
            
            # 更新錯誤狀態（ThreatCollectionService 會處理，這裡只是備用）
            feed = await self.feed_repository.get_by_id(feed_id)
            if feed:
                # 使用 ThreatFeed 的 update_collection_status 方法
                feed.update_collection_status(
                    CollectionStatus("failed"),
                    error_message=error_msg,
                )
                await self.feed_repository.save(feed)
            
            return {
                "success": False,
                "error": error_msg,
            }
        finally:
            # 標記任務為已完成
            self._running_jobs[job_id] = False
    
    def _create_trigger(self, frequency: CollectionFrequency) -> Optional[Any]:
        """
        根據收集頻率建立觸發器
        
        Args:
            frequency: 收集頻率值物件
        
        Returns:
            Trigger: APScheduler 觸發器，如果無法建立則返回 None
        """
        frequency_value = frequency.value
        
        if frequency_value == "每小時":
            return IntervalTrigger(hours=1)
        elif frequency_value == "每日":
            return IntervalTrigger(days=1)
        elif frequency_value == "每週":
            return IntervalTrigger(weeks=1)
        elif frequency_value == "每月":
            return IntervalTrigger(weeks=4)  # 簡化處理，使用 4 週作為一個月
        else:
            logger.warning(
                f"不支援的收集頻率：{frequency_value}",
                extra={"frequency": frequency_value}
            )
            return None
    
    def get_schedule_status(self, feed_id: str) -> Dict[str, Any]:
        """
        取得排程狀態
        
        Args:
            feed_id: 威脅情資來源 ID
        
        Returns:
            Dict: 排程狀態資訊
        """
        job_id = f"{self._job_id_prefix}{feed_id}"
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
                feed_id = job.id.replace(self._job_id_prefix, "")
                schedules.append({
                    "feed_id": feed_id,
                    "job_id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "is_running": self._running_jobs.get(job.id, False),
                })
        
        return schedules

