"""
權限名稱值物件

定義系統支援的權限名稱。
"""

from enum import Enum


class PermissionName(str, Enum):
    """
    權限名稱枚舉
    
    定義各功能模組的權限清單。
    """
    
    # 資產管理
    ASSET_VIEW = "asset:view"
    ASSET_CREATE = "asset:create"
    ASSET_UPDATE = "asset:update"
    ASSET_DELETE = "asset:delete"
    ASSET_IMPORT = "asset:import"
    
    # PIR 管理
    PIR_VIEW = "pir:view"
    PIR_CREATE = "pir:create"
    PIR_UPDATE = "pir:update"
    PIR_DELETE = "pir:delete"
    PIR_TOGGLE = "pir:toggle"
    
    # 威脅情資來源管理
    THREAT_FEED_VIEW = "threat_feed:view"
    THREAT_FEED_CREATE = "threat_feed:create"
    THREAT_FEED_UPDATE = "threat_feed:update"
    THREAT_FEED_DELETE = "threat_feed:delete"
    THREAT_FEED_TOGGLE = "threat_feed:toggle"
    
    # 威脅情資
    THREAT_VIEW = "threat:view"
    
    # 關聯分析
    ASSOCIATION_VIEW = "association:view"
    
    # 風險評估
    RISK_ASSESSMENT_VIEW = "risk_assessment:view"
    
    # 報告
    REPORT_VIEW = "report:view"
    REPORT_CREATE = "report:create"
    REPORT_DOWNLOAD = "report:download"
    
    # IT 工單
    TICKET_VIEW = "ticket:view"
    TICKET_EXPORT = "ticket:export"
    TICKET_UPDATE_STATUS = "ticket:update_status"
    
    # 通知規則
    NOTIFICATION_RULE_VIEW = "notification_rule:view"
    NOTIFICATION_RULE_CREATE = "notification_rule:create"
    NOTIFICATION_RULE_UPDATE = "notification_rule:update"
    NOTIFICATION_RULE_DELETE = "notification_rule:delete"
    
    # 系統設定
    SYSTEM_CONFIG_VIEW = "system_config:view"
    SYSTEM_CONFIG_UPDATE = "system_config:update"
    
    # 排程管理
    SCHEDULE_VIEW = "schedule:view"
    SCHEDULE_CREATE = "schedule:create"
    SCHEDULE_UPDATE = "schedule:update"
    SCHEDULE_DELETE = "schedule:delete"
    SCHEDULE_TRIGGER = "schedule:trigger"
    
    # 稽核日誌
    AUDIT_LOG_VIEW = "audit_log:view"
    
    def __str__(self) -> str:
        return self.value

