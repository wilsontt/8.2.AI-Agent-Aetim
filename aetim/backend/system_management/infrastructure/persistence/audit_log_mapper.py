"""
稽核日誌領域模型與資料模型映射器

負責領域模型（AuditLog）與資料模型（AuditLog）之間的轉換。
"""

import json
from ...domain.entities.audit_log import AuditLog
from .models import AuditLog as AuditLogModel


class AuditLogMapper:
    """稽核日誌映射器"""
    
    @staticmethod
    def to_domain(audit_log_model: AuditLogModel) -> AuditLog:
        """
        將資料模型轉換為領域模型
        
        Args:
            audit_log_model: 資料模型
        
        Returns:
            AuditLog: 領域模型（實體）
        """
        details = None
        if audit_log_model.details:
            try:
                details = json.loads(audit_log_model.details)
            except json.JSONDecodeError:
                details = None
        
        return AuditLog(
            id=str(audit_log_model.id),
            user_id=str(audit_log_model.user_id) if audit_log_model.user_id else None,
            action=audit_log_model.action,
            resource_type=audit_log_model.resource_type,
            resource_id=str(audit_log_model.resource_id) if audit_log_model.resource_id else None,
            details=details,
            ip_address=audit_log_model.ip_address,
            user_agent=audit_log_model.user_agent,
            created_at=audit_log_model.created_at,
        )
    
    @staticmethod
    def to_model(audit_log: AuditLog) -> AuditLogModel:
        """
        將領域模型轉換為資料模型
        
        Args:
            audit_log: 領域模型（實體）
        
        Returns:
            AuditLogModel: 資料模型
        """
        return AuditLogModel(
            id=audit_log.id,
            user_id=audit_log.user_id,
            action=audit_log.action,
            resource_type=audit_log.resource_type,
            resource_id=audit_log.resource_id,
            details=json.dumps(audit_log.details) if audit_log.details else None,
            ip_address=audit_log.ip_address,
            user_agent=audit_log.user_agent,
            created_at=audit_log.created_at,
        )

