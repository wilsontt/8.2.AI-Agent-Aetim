"""
PIR 聚合根

PIR（優先情資需求）聚合根包含所有業務邏輯方法，負責維護 PIR 的一致性。
"""

from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from ..value_objects.pir_priority import PIRPriority
from ..domain_events.pir_created_event import PIRCreatedEvent
from ..domain_events.pir_updated_event import PIRUpdatedEvent
from ..domain_events.pir_toggled_event import PIRToggledEvent


@dataclass
class PIR:
    """
    PIR 聚合根
    
    聚合根負責：
    1. 維護聚合的一致性邊界
    2. 實作業務邏輯
    3. 發布領域事件
    
    業務規則：
    - 停用的 PIR 不得影響威脅分析流程（AC-005-2）
    """
    
    id: str
    name: str
    description: str
    priority: PIRPriority
    condition_type: str
    condition_value: str
    is_enabled: bool = True
    _domain_events: List = field(default_factory=list, repr=False)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    updated_by: str = "system"
    
    def __post_init__(self):
        """驗證聚合根的有效性"""
        if not self.name or not self.name.strip():
            raise ValueError("PIR 名稱不能為空")
        
        if not self.description or not self.description.strip():
            raise ValueError("PIR 描述不能為空")
        
        if not self.condition_type or not self.condition_type.strip():
            raise ValueError("條件類型不能為空")
        
        if not self.condition_value or not self.condition_value.strip():
            raise ValueError("條件值不能為空")
        
        if not isinstance(self.priority, PIRPriority):
            raise ValueError("priority 必須是 PIRPriority 值物件")
    
    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        priority: str,
        condition_type: str,
        condition_value: str,
        is_enabled: bool = True,
        created_by: str = "system",
    ) -> "PIR":
        """
        建立 PIR（工廠方法）
        
        Args:
            name: PIR 名稱
            description: PIR 描述
            priority: 優先級（高/中/低）
            condition_type: 條件類型（產品名稱、CVE 編號、威脅類型等）
            condition_value: 條件值
            is_enabled: 是否啟用（預設 True）
            created_by: 建立者（預設 "system"）
        
        Returns:
            PIR: 新建立的 PIR 聚合根
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        pir = cls(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            priority=PIRPriority(priority),
            condition_type=condition_type,
            condition_value=condition_value,
            is_enabled=is_enabled,
            created_by=created_by,
            updated_by=created_by,
        )
        
        # 發布領域事件
        pir._domain_events.append(
            PIRCreatedEvent(
                pir_id=pir.id,
                name=pir.name,
                priority=pir.priority.value,
                condition_type=pir.condition_type,
            )
        )
        
        return pir
    
    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        condition_type: Optional[str] = None,
        condition_value: Optional[str] = None,
        updated_by: str = "system",
    ) -> None:
        """
        更新 PIR 資訊
        
        Args:
            name: PIR 名稱（可選）
            description: PIR 描述（可選）
            priority: 優先級（可選）
            condition_type: 條件類型（可選）
            condition_value: 條件值（可選）
            updated_by: 更新者（預設 "system"）
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        updated_fields = []
        
        if name is not None:
            if not name.strip():
                raise ValueError("PIR 名稱不能為空")
            self.name = name
            updated_fields.append("name")
        
        if description is not None:
            if not description.strip():
                raise ValueError("PIR 描述不能為空")
            self.description = description
            updated_fields.append("description")
        
        if priority is not None:
            self.priority = PIRPriority(priority)
            updated_fields.append("priority")
        
        if condition_type is not None:
            if not condition_type.strip():
                raise ValueError("條件類型不能為空")
            self.condition_type = condition_type
            updated_fields.append("condition_type")
        
        if condition_value is not None:
            if not condition_value.strip():
                raise ValueError("條件值不能為空")
            self.condition_value = condition_value
            updated_fields.append("condition_value")
        
        if updated_fields:
            self.updated_at = datetime.utcnow()
            self.updated_by = updated_by
            
            # 發布領域事件
            self._domain_events.append(
                PIRUpdatedEvent(
                    pir_id=self.id,
                    name=self.name,
                    updated_fields=updated_fields,
                )
            )
    
    def toggle(self, updated_by: str = "system") -> None:
        """
        切換 PIR 啟用狀態
        
        Args:
            updated_by: 更新者（預設 "system"）
        """
        self.is_enabled = not self.is_enabled
        self.updated_at = datetime.utcnow()
        self.updated_by = updated_by
        
        # 發布領域事件
        self._domain_events.append(
            PIRToggledEvent(
                pir_id=self.id,
                name=self.name,
                is_enabled=self.is_enabled,
            )
        )
    
    def enable(self, updated_by: str = "system") -> None:
        """
        啟用 PIR
        
        Args:
            updated_by: 更新者（預設 "system"）
        """
        if not self.is_enabled:
            self.toggle(updated_by)
    
    def disable(self, updated_by: str = "system") -> None:
        """
        停用 PIR
        
        業務規則：停用的 PIR 不得影響威脅分析流程（AC-005-2）
        
        Args:
            updated_by: 更新者（預設 "system"）
        """
        if self.is_enabled:
            self.toggle(updated_by)
    
    def matches_condition(self, threat_data: dict) -> bool:
        """
        檢查威脅資料是否符合 PIR 條件
        
        此方法用於威脅分析流程，但只有啟用的 PIR 才會被使用。
        
        Args:
            threat_data: 威脅資料字典（包含 cve、product_name、threat_type 等）
        
        Returns:
            bool: 是否符合條件
        
        Note:
            停用的 PIR 不應被用於威脅分析（業務規則 AC-005-2）
        """
        if not self.is_enabled:
            return False
        
        if self.condition_type == "產品名稱":
            product_name = threat_data.get("product_name", "")
            return self.condition_value.lower() in product_name.lower()
        
        elif self.condition_type == "CVE 編號":
            cve = threat_data.get("cve", "")
            # 支援 CVE 前綴匹配（例如：CVE-2024-）
            if self.condition_value.endswith("-"):
                return cve.startswith(self.condition_value)
            return cve == self.condition_value
        
        elif self.condition_type == "威脅類型":
            threat_type = threat_data.get("threat_type", "")
            return self.condition_value.lower() in threat_type.lower()
        
        elif self.condition_type == "CVSS 分數":
            cvss_score = threat_data.get("cvss_score", 0.0)
            # 支援範圍匹配（例如："> 7.0"）
            if self.condition_value.startswith(">"):
                threshold = float(self.condition_value[1:].strip())
                return cvss_score > threshold
            elif self.condition_value.startswith("<"):
                threshold = float(self.condition_value[1:].strip())
                return cvss_score < threshold
            else:
                threshold = float(self.condition_value)
                return cvss_score >= threshold
        
        return False
    
    def get_domain_events(self) -> List:
        """
        取得領域事件清單
        
        Returns:
            List: 領域事件清單
        """
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """清除領域事件清單"""
        self._domain_events.clear()
    
    def __repr__(self):
        return (
            f"PIR(id='{self.id}', "
            f"name='{self.name}', "
            f"priority='{self.priority.value}', "
            f"is_enabled={self.is_enabled})"
        )

