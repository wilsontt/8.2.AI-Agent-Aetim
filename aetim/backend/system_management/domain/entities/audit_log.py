"""
稽核日誌實體

稽核日誌實體用於記錄所有涉及資料存取、修改、刪除的操作。
符合 ISO 27001:2022 要求（NFR-005）。
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import json


@dataclass
class AuditLog:
    """
    稽核日誌實體
    
    稽核日誌是不可變的，一旦建立就不能修改（符合 NFR-005 要求）。
    """
    
    id: str
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """驗證實體的有效性"""
        if not self.action or not self.action.strip():
            raise ValueError("操作類型不能為空")
        
        if not self.resource_type or not self.resource_type.strip():
            raise ValueError("資源類型不能為空")
        
        # 驗證操作類型
        valid_actions = ["CREATE", "UPDATE", "DELETE", "IMPORT", "VIEW", "TOGGLE", "EXPORT", "LOGIN", "LOGOUT"]
        if self.action.upper() not in valid_actions:
            raise ValueError(f"操作類型必須為以下之一：{', '.join(valid_actions)}")
    
    @classmethod
    def create(
        cls,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> "AuditLog":
        """
        建立稽核日誌（工廠方法）
        
        Args:
            user_id: 使用者 ID（可選）
            action: 操作類型（CREATE/UPDATE/DELETE/IMPORT/VIEW/TOGGLE/EXPORT）
            resource_type: 資源類型（Asset/PIR/ThreatFeed 等）
            resource_id: 資源 ID（可選）
            details: 操作詳情（可選，字典格式）
            ip_address: IP 位址（可選）
            user_agent: User Agent（可選）
        
        Returns:
            AuditLog: 新建立的稽核日誌實體
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action.upper(),
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        轉換為字典格式
        
        Returns:
            Dict[str, Any]: 稽核日誌字典
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": json.dumps(self.details) if self.details else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at,
        }
    
    def __repr__(self):
        return (
            f"AuditLog(id='{self.id}', "
            f"action='{self.action}', "
            f"resource_type='{self.resource_type}', "
            f"resource_id='{self.resource_id}', "
            f"created_at={self.created_at})"
        )

