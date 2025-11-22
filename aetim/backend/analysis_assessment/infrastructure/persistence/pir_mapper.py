"""
PIR 領域模型與資料模型映射器

負責領域模型（PIR）與資料模型（PIR）之間的轉換。
"""

from ...domain.aggregates.pir import PIR
from ...domain.value_objects.pir_priority import PIRPriority
from .models import PIR as PIRModel


class PIRMapper:
    """PIR 映射器"""
    
    @staticmethod
    def to_domain(pir_model: PIRModel) -> PIR:
        """
        將資料模型轉換為領域模型
        
        Args:
            pir_model: 資料模型
        
        Returns:
            PIR: 領域模型（聚合根）
        """
        pir = PIR(
            id=str(pir_model.id),
            name=pir_model.name,
            description=pir_model.description,
            priority=PIRPriority(pir_model.priority),
            condition_type=pir_model.condition_type,
            condition_value=pir_model.condition_value,
            is_enabled=pir_model.is_enabled,
            created_at=pir_model.created_at,
            updated_at=pir_model.updated_at,
            created_by=pir_model.created_by,
            updated_by=pir_model.updated_by,
        )
        
        # 清除領域事件（從資料庫載入的物件不應有未發布的事件）
        pir.clear_domain_events()
        
        return pir
    
    @staticmethod
    def to_model(pir: PIR) -> PIRModel:
        """
        將領域模型轉換為資料模型
        
        Args:
            pir: 領域模型（聚合根）
        
        Returns:
            PIRModel: 資料模型
        """
        return PIRModel(
            id=pir.id,
            name=pir.name,
            description=pir.description,
            priority=pir.priority.value,
            condition_type=pir.condition_type,
            condition_value=pir.condition_value,
            is_enabled=pir.is_enabled,
            created_at=pir.created_at,
            updated_at=pir.updated_at,
            created_by=pir.created_by,
            updated_by=pir.updated_by,
        )
    
    @staticmethod
    def update_model(pir_model: PIRModel, pir: PIR) -> None:
        """
        更新資料模型（不建立新物件）
        
        Args:
            pir_model: 現有的資料模型
            pir: 領域模型（聚合根）
        """
        pir_model.name = pir.name
        pir_model.description = pir.description
        pir_model.priority = pir.priority.value
        pir_model.condition_type = pir.condition_type
        pir_model.condition_value = pir.condition_value
        pir_model.is_enabled = pir.is_enabled
        pir_model.updated_at = pir.updated_at
        pir_model.updated_by = pir.updated_by

