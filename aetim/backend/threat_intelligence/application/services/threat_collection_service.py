"""
威脅收集服務

提供威脅情資的自動收集功能。
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domain.interfaces.threat_feed_repository import IThreatFeedRepository
from ...domain.interfaces.threat_repository import IThreatRepository
from ...domain.aggregates.threat_feed import ThreatFeed
from ...domain.aggregates.threat import Threat
from ...infrastructure.external_services.collector_factory import CollectorFactory
from ...infrastructure.external_services.collector_interface import ICollector
from ...infrastructure.external_services.ai_service_client import AIServiceClient
from .threat_extraction_service import ThreatExtractionService
from ...infrastructure.external_services.retry_handler import RetryHandler
from ...infrastructure.external_services.error_handler import ErrorHandler, ErrorType
from .failure_tracker import FailureTracker
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class ThreatCollectionService:
    """
    威脅收集服務
    
    提供威脅情資的自動收集功能，支援：
    - 從單一來源收集
    - 並行收集多個來源（至少 3 個）
    - 錯誤處理與重試機制（指數退避）
    - AI 服務整合（處理非結構化資料）
    - 標準化為統一資料模型
    """
    
    def __init__(
        self,
        feed_repository: IThreatFeedRepository,
        threat_repository: IThreatRepository,
        collector_factory: CollectorFactory,
        ai_service_client: Optional[AIServiceClient] = None,
        max_concurrent_collections: int = 3,
    ):
        """
        初始化威脅收集服務
        
        Args:
            feed_repository: 威脅情資來源 Repository
            threat_repository: 威脅 Repository
            collector_factory: 收集器工廠
            ai_service_client: AI 服務客戶端（可選）
            max_concurrent_collections: 最大並行收集數（預設 3，符合 AC-008-2）
        """
        self.feed_repository = feed_repository
        self.threat_repository = threat_repository
        self.collector_factory = collector_factory
        self.ai_service_client = ai_service_client
        self.max_concurrent_collections = max_concurrent_collections
        self.retry_handler = RetryHandler(
            max_retries=3,
            initial_delay=1.0,
            max_delay=60.0,
        )
        # 建立威脅提取服務
        self.threat_extraction_service = ThreatExtractionService(
            ai_service_client=ai_service_client,
            use_fallback=True,
        )
        # 建立錯誤處理器和失敗追蹤器
        self.error_handler = ErrorHandler()
        self.failure_tracker = FailureTracker(
            failure_threshold=3,  # 連續失敗 3 次時發送告警
            alert_cooldown_hours=24,  # 24 小時內不重複告警
        )
    
    async def collect_from_feed(
        self,
        feed_id: str,
        use_ai: bool = True,
    ) -> Dict[str, any]:
        """
        從單一來源收集威脅情資（AC-008-1）
        
        Args:
            feed_id: 威脅情資來源 ID
            use_ai: 是否使用 AI 服務處理非結構化資料（AC-008-7）
        
        Returns:
            Dict: 收集結果，包含：
                - success: bool - 是否成功
                - feed_id: str - 來源 ID
                - threats_collected: int - 收集到的威脅數量
                - errors: List[str] - 錯誤訊息列表
        """
        try:
            # 1. 取得威脅來源設定
            feed = await self.feed_repository.get_by_id(feed_id)
            if not feed:
                return {
                    "success": False,
                    "feed_id": feed_id,
                    "threats_collected": 0,
                    "errors": [f"找不到威脅情資來源：{feed_id}"],
                }
            
            if not feed.is_enabled:
                return {
                    "success": False,
                    "feed_id": feed_id,
                    "threats_collected": 0,
                    "errors": [f"威脅情資來源已停用：{feed.name}"],
                }
            
            logger.info(
                f"開始收集威脅情資：{feed.name}",
                extra={"feed_id": feed_id, "feed_name": feed.name}
            )
            
            # 2. 取得對應的收集器
            collector = self.collector_factory.get_collector(feed)
            if not collector:
                error_msg = f"找不到對應的收集器：{feed.name}"
                logger.error(error_msg, extra={"feed_id": feed_id, "feed_name": feed.name})
                
                # 更新收集狀態為失敗
                await self._update_collection_status(
                    feed,
                    "Failed",
                    error_message=error_msg,
                )
                
                return {
                    "success": False,
                    "feed_id": feed_id,
                    "threats_collected": 0,
                    "errors": [error_msg],
                }
            
            # 3. 使用重試機制收集威脅（AC-008-3）
            threats: List[Threat] = []
            errors: List[str] = []
            
            try:
                threats = await self.retry_handler.execute_with_retry(
                    lambda: collector.collect(feed),
                    retryable_exceptions=(Exception,),
                    on_retry=lambda attempt, e: logger.warning(
                        f"收集威脅失敗，正在重試（第 {attempt} 次）",
                        extra={
                            "feed_id": feed_id,
                            "feed_name": feed.name,
                            "attempt": attempt,
                            "error": str(e),
                        }
                    ),
                    context={
                        "feed_id": feed_id,
                        "feed_name": feed.name,
                    },
                )
            except Exception as e:
                # 分類錯誤並記錄（AC-008-4）
                error_type = self.error_handler.classify_error(e)
                error_details = self.error_handler.log_error(
                    e,
                    context={
                        "feed_id": feed_id,
                        "feed_name": feed.name,
                    },
                    error_type=error_type,
                )
                
                error_msg = f"收集威脅失敗：{str(e)}"
                errors.append(error_msg)
                
                # 記錄失敗（AC-008-4）
                should_alert = self.failure_tracker.record_failure(
                    feed_id=feed_id,
                    feed_name=feed.name,
                    error_message=error_msg,
                    error_type=error_type.value,
                )
                
                # 如果達到告警閾值，發送告警
                if should_alert:
                    await self._send_failure_alert(feed, error_details)
                
                # 更新收集狀態為失敗
                await self._update_collection_status(
                    feed,
                    "Failed",
                    error_message=error_msg,
                )
                
                return {
                    "success": False,
                    "feed_id": feed_id,
                    "threats_collected": 0,
                    "errors": errors,
                }
            
            # 4. 處理收集結果
            processed_threats = []
            
            for threat in threats:
                try:
                    # 4.1 標準化為統一資料模型（AC-008-5）
                    standardized_threat = await self._standardize_threat(threat, feed)
                    
                    # 4.2 使用威脅提取服務處理非結構化資料（AC-008-7）
                    if use_ai:
                        await self._enhance_with_extraction_service(standardized_threat)
                    
                    # 4.3 儲存威脅
                    await self.threat_repository.save(standardized_threat)
                    processed_threats.append(standardized_threat)
                    
                except Exception as e:
                    error_msg = f"處理威脅失敗：{str(e)}"
                    logger.error(
                        error_msg,
                        extra={
                            "feed_id": feed_id,
                            "threat_id": threat.id if threat else None,
                            "error": str(e),
                        }
                    )
                    errors.append(error_msg)
            
            # 5. 記錄成功（重置失敗計數，AC-008-4）
            self.failure_tracker.record_success(feed.id)
            
            # 6. 更新收集狀態與時間
            await self._update_collection_status(
                feed,
                "Success",
                error_message=None,
            )
            
            logger.info(
                f"完成收集威脅情資：{feed.name}",
                extra={
                    "feed_id": feed_id,
                    "feed_name": feed.name,
                    "threats_collected": len(processed_threats),
                }
            )
            
            return {
                "success": True,
                "feed_id": feed_id,
                "threats_collected": len(processed_threats),
                "errors": errors,
            }
            
        except Exception as e:
            error_msg = f"收集威脅情資時發生未預期錯誤：{str(e)}"
            logger.error(error_msg, extra={"feed_id": feed_id, "error": str(e)})
            
            return {
                "success": False,
                "feed_id": feed_id,
                "threats_collected": 0,
                "errors": [error_msg],
            }
    
    async def collect_all_feeds(
        self,
        use_ai: bool = True,
    ) -> Dict[str, any]:
        """
        收集所有啟用的來源（AC-008-2：支援並行收集，至少 3 個來源）
        
        Args:
            use_ai: 是否使用 AI 服務處理非結構化資料
        
        Returns:
            Dict: 收集結果，包含：
                - total_feeds: int - 總來源數
                - successful_feeds: int - 成功收集的來源數
                - failed_feeds: int - 失敗的來源數
                - total_threats: int - 總收集到的威脅數
                - results: List[Dict] - 各來源的收集結果
        """
        # 1. 取得啟用的威脅情資來源
        feeds = await self.feed_repository.get_enabled_feeds()
        
        if not feeds:
            logger.warning("沒有啟用的威脅情資來源")
            return {
                "total_feeds": 0,
                "successful_feeds": 0,
                "failed_feeds": 0,
                "total_threats": 0,
                "results": [],
            }
        
        logger.info(
            f"開始收集所有啟用的威脅情資來源（共 {len(feeds)} 個）",
            extra={"total_feeds": len(feeds)}
        )
        
        # 2. 使用 Semaphore 限制並行收集數（AC-008-2）
        semaphore = asyncio.Semaphore(self.max_concurrent_collections)
        
        async def collect_feed_with_semaphore(feed: ThreatFeed) -> Dict[str, any]:
            """使用 Semaphore 控制並行收集"""
            async with semaphore:
                return await self.collect_from_feed(feed.id, use_ai=use_ai)
        
        # 3. 並行執行收集（AC-008-2）
        tasks = [collect_feed_with_semaphore(feed) for feed in feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 4. 處理結果
        successful_feeds = 0
        failed_feeds = 0
        total_threats = 0
        processed_results = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_msg = f"收集威脅情資時發生異常：{str(result)}"
                logger.error(error_msg, extra={"feed_id": feeds[i].id, "error": str(result)})
                processed_results.append({
                    "success": False,
                    "feed_id": feeds[i].id,
                    "threats_collected": 0,
                    "errors": [error_msg],
                })
                failed_feeds += 1
            else:
                processed_results.append(result)
                if result["success"]:
                    successful_feeds += 1
                    total_threats += result["threats_collected"]
                else:
                    failed_feeds += 1
        
        logger.info(
            f"完成收集所有威脅情資來源",
            extra={
                "total_feeds": len(feeds),
                "successful_feeds": successful_feeds,
                "failed_feeds": failed_feeds,
                "total_threats": total_threats,
            }
        )
        
        return {
            "total_feeds": len(feeds),
            "successful_feeds": successful_feeds,
            "failed_feeds": failed_feeds,
            "total_threats": total_threats,
            "results": processed_results,
        }
    
    async def _standardize_threat(
        self,
        threat: Threat,
        feed: ThreatFeed,
    ) -> Threat:
        """
        標準化威脅為統一資料模型（AC-008-5）
        
        Args:
            threat: 威脅聚合根
            feed: 威脅情資來源聚合根
        
        Returns:
            Threat: 標準化後的威脅
        """
        # 確保威脅有正確的 threat_feed_id
        if threat.threat_feed_id != feed.id:
            threat.threat_feed_id = feed.id
        
        # 確保有 collected_at 時間
        if not threat.collected_at:
            threat.collected_at = datetime.utcnow()
        
        return threat
    
    async def _enhance_with_extraction_service(self, threat: Threat) -> None:
        """
        使用威脅提取服務增強威脅資訊（AC-008-7）
        
        Args:
            threat: 威脅聚合根
        """
        # 組合文字內容用於提取
        text_parts = []
        
        if threat.title:
            text_parts.append(threat.title)
        if threat.description:
            text_parts.append(threat.description)
        
        if not text_parts:
            return
        
        text = "\n".join(text_parts)
        
        try:
            # 使用威脅提取服務提取威脅資訊（包含回退機制）
            extracted_info = await self.threat_extraction_service.extract_threat_info(text)
            
            logger.info(
                f"威脅資訊提取完成（來源：{extracted_info.source}，信心分數：{extracted_info.confidence:.2f}）",
                extra={
                    "threat_id": threat.id,
                    "source": extracted_info.source,
                    "confidence": extracted_info.confidence,
                }
            )
            
            # 更新威脅資訊
            # CVE
            if extracted_info.cves and not threat.cve_id:
                # 如果威脅還沒有 CVE，使用提取的結果
                threat.cve_id = extracted_info.cves[0]  # 使用第一個 CVE
            
            # 產品
            if extracted_info.products:
                for product_info in extracted_info.products:
                    threat.add_product(
                        product_name=product_info.get("product_name", ""),
                        product_version=product_info.get("product_version"),
                        product_type=product_info.get("product_type"),
                        original_text=product_info.get("original_text"),
                    )
            
            # TTPs
            if extracted_info.ttps:
                for ttp in extracted_info.ttps:
                    threat.add_ttp(ttp)
            
            # IOCs
            if extracted_info.iocs:
                for ioc_type, ioc_values in extracted_info.iocs.items():
                    if isinstance(ioc_values, list):
                        for ioc_value in ioc_values:
                            threat.add_ioc(ioc_type, ioc_value)
        
        except Exception as e:
            logger.warning(
                f"威脅資訊提取失敗：{str(e)}",
                extra={
                    "threat_id": threat.id,
                    "error": str(e),
                }
            )
            # 提取失敗不影響威脅儲存，繼續處理
    
    async def _send_failure_alert(
        self,
        feed: ThreatFeed,
        error_details: Dict[str, Any],
    ) -> None:
        """
        發送失敗告警（AC-008-4）
        
        Args:
            feed: 威脅情資來源聚合根
            error_details: 錯誤詳情
        """
        failure_record = self.failure_tracker.get_failure_record(feed.id)
        if not failure_record:
            return
        
        # 建立告警訊息
        alert_message = (
            f"威脅情資來源「{feed.name}」連續失敗 {failure_record.failure_count} 次。\n"
            f"最後錯誤：{failure_record.last_error_message}\n"
            f"錯誤類型：{failure_record.last_error_type}\n"
            f"首次失敗時間：{failure_record.first_failure_time.isoformat() if failure_record.first_failure_time else 'N/A'}\n"
            f"最後失敗時間：{failure_record.last_failure_time.isoformat() if failure_record.last_failure_time else 'N/A'}"
        )
        
        logger.error(
            f"威脅收集連續失敗告警：{feed.name}",
            extra={
                "feed_id": feed.id,
                "feed_name": feed.name,
                "failure_count": failure_record.failure_count,
                "error_details": error_details,
                "alert_message": alert_message,
            }
        )
        
        # TODO: 實作實際的告警機制（Email 或系統通知）
        # 目前僅記錄日誌，後續可以整合到通知系統
        # 例如：
        # - 發送 Email
        # - 發送系統通知
        # - 發送到監控系統
    
    async def _update_collection_status(
        self,
        feed: ThreatFeed,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """
        更新收集狀態（AC-008-4）
        
        Args:
            feed: 威脅情資來源聚合根
            status: 收集狀態（Success/Failed）
            error_message: 錯誤訊息（如果有）
        """
        try:
            feed.update_collection_status(
                status=status,
                error_message=error_message,
            )
            await self.feed_repository.save(feed)
        except Exception as e:
            logger.error(
                f"更新收集狀態失敗：{str(e)}",
                extra={
                    "feed_id": feed.id,
                    "status": status,
                    "error": str(e),
                }
            )

