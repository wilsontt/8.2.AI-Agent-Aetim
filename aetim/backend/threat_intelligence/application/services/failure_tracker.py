"""
失敗追蹤器

追蹤威脅收集的連續失敗次數，並在達到閾值時發送告警。
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


@dataclass
class FailureRecord:
    """失敗記錄"""
    
    feed_id: str
    feed_name: str
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_error_message: Optional[str] = None
    last_error_type: Optional[str] = None
    first_failure_time: Optional[datetime] = None
    alert_sent: bool = False
    alert_sent_at: Optional[datetime] = None


class FailureTracker:
    """
    失敗追蹤器
    
    追蹤威脅收集的連續失敗次數，並在達到閾值時發送告警（AC-008-4）。
    """
    
    def __init__(
        self,
        failure_threshold: int = 3,
        alert_cooldown_hours: int = 24,
    ):
        """
        初始化失敗追蹤器
        
        Args:
            failure_threshold: 連續失敗閾值（達到此值時發送告警）
            alert_cooldown_hours: 告警冷卻時間（小時，避免重複告警）
        """
        self.failure_threshold = failure_threshold
        self.alert_cooldown_hours = alert_cooldown_hours
        self._failure_records: Dict[str, FailureRecord] = {}
    
    def record_failure(
        self,
        feed_id: str,
        feed_name: str,
        error_message: str,
        error_type: Optional[str] = None,
    ) -> bool:
        """
        記錄失敗（AC-008-4）
        
        Args:
            feed_id: 威脅情資來源 ID
            feed_name: 威脅情資來源名稱
            error_message: 錯誤訊息
            error_type: 錯誤類型
        
        Returns:
            bool: 是否應該發送告警
        """
        now = datetime.utcnow()
        
        if feed_id not in self._failure_records:
            self._failure_records[feed_id] = FailureRecord(
                feed_id=feed_id,
                feed_name=feed_name,
            )
        
        record = self._failure_records[feed_id]
        
        # 更新失敗記錄
        record.failure_count += 1
        record.last_failure_time = now
        record.last_error_message = error_message
        record.last_error_type = error_type
        
        if record.first_failure_time is None:
            record.first_failure_time = now
        
        logger.warning(
            f"記錄威脅收集失敗：{feed_name}（連續失敗 {record.failure_count} 次）",
            extra={
                "feed_id": feed_id,
                "feed_name": feed_name,
                "failure_count": record.failure_count,
                "error_message": error_message,
                "error_type": error_type,
            }
        )
        
        # 檢查是否應該發送告警
        should_alert = (
            record.failure_count >= self.failure_threshold
            and not self._is_in_cooldown(record)
        )
        
        if should_alert:
            record.alert_sent = True
            record.alert_sent_at = now
            return True
        
        return False
    
    def record_success(self, feed_id: str) -> None:
        """
        記錄成功（重置失敗計數）
        
        Args:
            feed_id: 威脅情資來源 ID
        """
        if feed_id in self._failure_records:
            record = self._failure_records[feed_id]
            
            if record.failure_count > 0:
                logger.info(
                    f"威脅收集成功，重置失敗計數：{record.feed_name}",
                    extra={
                        "feed_id": feed_id,
                        "feed_name": record.feed_name,
                        "previous_failure_count": record.failure_count,
                    }
                )
            
            # 重置失敗記錄
            record.failure_count = 0
            record.first_failure_time = None
            record.alert_sent = False
            record.alert_sent_at = None
    
    def get_failure_record(self, feed_id: str) -> Optional[FailureRecord]:
        """
        取得失敗記錄
        
        Args:
            feed_id: 威脅情資來源 ID
        
        Returns:
            Optional[FailureRecord]: 失敗記錄，如果不存在則返回 None
        """
        return self._failure_records.get(feed_id)
    
    def _is_in_cooldown(self, record: FailureRecord) -> bool:
        """
        檢查是否在告警冷卻時間內
        
        Args:
            record: 失敗記錄
        
        Returns:
            bool: 是否在冷卻時間內
        """
        if not record.alert_sent_at:
            return False
        
        cooldown_end = record.alert_sent_at + timedelta(hours=self.alert_cooldown_hours)
        return datetime.utcnow() < cooldown_end
    
    def get_all_failure_records(self) -> Dict[str, FailureRecord]:
        """
        取得所有失敗記錄
        
        Returns:
            Dict[str, FailureRecord]: 所有失敗記錄
        """
        return self._failure_records.copy()

