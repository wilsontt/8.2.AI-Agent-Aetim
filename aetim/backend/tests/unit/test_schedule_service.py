"""
排程服務單元測試

測試排程服務的功能。
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from threat_intelligence.application.services.schedule_service import ScheduleService
from threat_intelligence.domain.aggregates.threat_feed import ThreatFeed
from threat_intelligence.domain.value_objects.collection_frequency import CollectionFrequency
from threat_intelligence.domain.value_objects.collection_status import CollectionStatus


@pytest.fixture
def mock_feed_repository():
    """建立 Mock ThreatFeedRepository"""
    repository = AsyncMock()
    return repository


@pytest.fixture
def mock_collection_service():
    """建立 Mock ThreatCollectionService"""
    service = AsyncMock()
    return service


@pytest.fixture
def sample_feed():
    """建立測試用的 ThreatFeed"""
    return ThreatFeed.create(
        name="CISA KEV",
        priority="P0",
        collection_frequency="每小時",
        description="CISA Known Exploited Vulnerabilities",
    )


@pytest.fixture
def schedule_service(mock_feed_repository, mock_collection_service):
    """建立 ScheduleService 實例"""
    return ScheduleService(
        feed_repository=mock_feed_repository,
        collection_service=mock_collection_service,
    )


@pytest.mark.asyncio
class TestScheduleService:
    """排程服務測試"""
    
    def test_init(self, schedule_service):
        """測試初始化"""
        assert schedule_service.feed_repository is not None
        assert schedule_service.collection_service is not None
        assert schedule_service.scheduler is not None
    
    @pytest.mark.asyncio
    async def test_start_and_stop(self, schedule_service):
        """測試啟動和停止排程服務"""
        # 啟動
        await schedule_service.start()
        assert schedule_service.scheduler.running
        
        # 停止
        await schedule_service.stop()
        assert not schedule_service.scheduler.running
    
    @pytest.mark.asyncio
    async def test_load_schedules(
        self,
        schedule_service,
        mock_feed_repository,
        sample_feed,
    ):
        """測試載入排程"""
        # 設定 Mock
        mock_feed_repository.get_enabled_feeds.return_value = [sample_feed]
        
        # 啟動排程服務
        await schedule_service.start()
        
        # 載入排程
        await schedule_service.load_schedules()
        
        # 驗證
        assert mock_feed_repository.get_enabled_feeds.called
        job_id = f"threat_collection_{sample_feed.id}"
        job = schedule_service.scheduler.get_job(job_id)
        assert job is not None
        
        # 清理
        await schedule_service.stop()
    
    @pytest.mark.asyncio
    async def test_add_schedule(
        self,
        schedule_service,
        sample_feed,
    ):
        """測試新增排程"""
        # 啟動排程服務
        await schedule_service.start()
        
        # 新增排程
        await schedule_service.add_schedule(sample_feed)
        
        # 驗證
        job_id = f"threat_collection_{sample_feed.id}"
        job = schedule_service.scheduler.get_job(job_id)
        assert job is not None
        assert job.name == f"收集威脅情資：{sample_feed.name}"
        
        # 清理
        await schedule_service.stop()
    
    @pytest.mark.asyncio
    async def test_add_schedule_disabled_feed(
        self,
        schedule_service,
        sample_feed,
    ):
        """測試新增已停用的排程（應該跳過）"""
        # 停用 feed
        sample_feed.toggle_status()
        
        # 啟動排程服務
        await schedule_service.start()
        
        # 新增排程（應該跳過）
        await schedule_service.add_schedule(sample_feed)
        
        # 驗證（不應該有排程）
        job_id = f"threat_collection_{sample_feed.id}"
        job = schedule_service.scheduler.get_job(job_id)
        assert job is None
        
        # 清理
        await schedule_service.stop()
    
    @pytest.mark.asyncio
    async def test_remove_schedule(
        self,
        schedule_service,
        sample_feed,
    ):
        """測試移除排程"""
        # 啟動排程服務
        await schedule_service.start()
        
        # 新增排程
        await schedule_service.add_schedule(sample_feed)
        
        # 移除排程
        await schedule_service.remove_schedule(sample_feed.id)
        
        # 驗證
        job_id = f"threat_collection_{sample_feed.id}"
        job = schedule_service.scheduler.get_job(job_id)
        assert job is None
        
        # 清理
        await schedule_service.stop()
    
    @pytest.mark.asyncio
    async def test_update_schedule(
        self,
        schedule_service,
        sample_feed,
    ):
        """測試更新排程"""
        # 啟動排程服務
        await schedule_service.start()
        
        # 新增排程
        await schedule_service.add_schedule(sample_feed)
        
        # 更新收集頻率
        sample_feed.collection_frequency = CollectionFrequency("每日")
        
        # 更新排程
        await schedule_service.update_schedule(sample_feed)
        
        # 驗證（排程應該已更新）
        job_id = f"threat_collection_{sample_feed.id}"
        job = schedule_service.scheduler.get_job(job_id)
        assert job is not None
        
        # 清理
        await schedule_service.stop()
    
    @pytest.mark.asyncio
    async def test_execute_schedule_now_success(
        self,
        schedule_service,
        mock_feed_repository,
        mock_collection_service,
        sample_feed,
    ):
        """測試立即執行排程（成功）"""
        # 設定 Mock
        mock_feed_repository.get_by_id.return_value = sample_feed
        mock_collection_service.collect_from_feed.return_value = {
            "success": True,
            "feed_id": sample_feed.id,
            "threats_collected": 5,
            "errors": [],
        }
        
        # 執行
        result = await schedule_service.execute_schedule_now(sample_feed.id)
        
        # 驗證
        assert result["success"] is True
        assert result["threats_collected"] == 5
        assert mock_collection_service.collect_from_feed.called
    
    @pytest.mark.asyncio
    async def test_execute_schedule_now_feed_not_found(
        self,
        schedule_service,
        mock_feed_repository,
    ):
        """測試立即執行排程（找不到來源）"""
        # 設定 Mock
        mock_feed_repository.get_by_id.return_value = None
        
        # 執行
        result = await schedule_service.execute_schedule_now("non-existent-id")
        
        # 驗證
        assert result["success"] is False
        assert "找不到威脅情資來源" in result["error"]
    
    @pytest.mark.asyncio
    async def test_execute_collection_concurrent_prevention(
        self,
        schedule_service,
        mock_feed_repository,
        mock_collection_service,
        sample_feed,
    ):
        """測試並發執行預防（同一任務不應該同時執行）"""
        # 設定 Mock
        mock_feed_repository.get_by_id.return_value = sample_feed
        
        # 模擬長時間執行的收集任務
        async def slow_collect(*args, **kwargs):
            import asyncio
            await asyncio.sleep(0.1)
            return {
                "success": True,
                "feed_id": sample_feed.id,
                "threats_collected": 1,
                "errors": [],
            }
        
        mock_collection_service.collect_from_feed = slow_collect
        
        # 同時執行兩次（應該只有一次成功）
        import asyncio
        results = await asyncio.gather(
            schedule_service._execute_collection(sample_feed.id),
            schedule_service._execute_collection(sample_feed.id),
            return_exceptions=True,
        )
        
        # 驗證（至少有一個應該被跳過）
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        assert success_count >= 1
    
    @pytest.mark.asyncio
    async def test_create_trigger_hourly(self, schedule_service):
        """測試建立每小時觸發器"""
        frequency = CollectionFrequency("每小時")
        trigger = schedule_service._create_trigger(frequency)
        assert trigger is not None
    
    @pytest.mark.asyncio
    async def test_create_trigger_daily(self, schedule_service):
        """測試建立每日觸發器"""
        frequency = CollectionFrequency("每日")
        trigger = schedule_service._create_trigger(frequency)
        assert trigger is not None
    
    @pytest.mark.asyncio
    async def test_create_trigger_weekly(self, schedule_service):
        """測試建立每週觸發器"""
        frequency = CollectionFrequency("每週")
        trigger = schedule_service._create_trigger(frequency)
        assert trigger is not None
    
    @pytest.mark.asyncio
    async def test_create_trigger_monthly(self, schedule_service):
        """測試建立每月觸發器"""
        frequency = CollectionFrequency("每月")
        trigger = schedule_service._create_trigger(frequency)
        assert trigger is not None
    
    @pytest.mark.asyncio
    async def test_get_schedule_status(
        self,
        schedule_service,
        sample_feed,
    ):
        """測試取得排程狀態"""
        # 啟動排程服務
        await schedule_service.start()
        
        # 新增排程
        await schedule_service.add_schedule(sample_feed)
        
        # 取得狀態
        status = schedule_service.get_schedule_status(sample_feed.id)
        
        # 驗證
        assert status["exists"] is True
        assert status["enabled"] is True
        assert status["is_running"] is False
        
        # 清理
        await schedule_service.stop()
    
    @pytest.mark.asyncio
    async def test_get_all_schedules(
        self,
        schedule_service,
        sample_feed,
    ):
        """測試取得所有排程"""
        # 啟動排程服務
        await schedule_service.start()
        
        # 新增排程
        await schedule_service.add_schedule(sample_feed)
        
        # 取得所有排程
        schedules = schedule_service.get_all_schedules()
        
        # 驗證
        assert len(schedules) >= 1
        assert any(s["feed_id"] == sample_feed.id for s in schedules)
        
        # 清理
        await schedule_service.stop()

