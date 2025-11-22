"""
資產聚合根

資產聚合根包含所有業務邏輯方法，負責維護資產的一致性。
"""

from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from ..value_objects.data_sensitivity import DataSensitivity
from ..value_objects.business_criticality import BusinessCriticality
from ..entities.asset_product import AssetProduct
from ..domain_events.asset_created_event import AssetCreatedEvent
from ..domain_events.asset_updated_event import AssetUpdatedEvent


@dataclass
class Asset:
    """
    資產聚合根
    
    聚合根負責：
    1. 維護聚合的一致性邊界
    2. 實作業務邏輯
    3. 發布領域事件
    """
    
    id: str
    host_name: str
    operating_system: str
    running_applications: str
    owner: str
    data_sensitivity: DataSensitivity
    business_criticality: BusinessCriticality
    ip: Optional[str] = None
    item: Optional[int] = None
    is_public_facing: bool = False
    products: List[AssetProduct] = field(default_factory=list)
    _domain_events: List = field(default_factory=list, repr=False)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    updated_by: str = "system"
    
    def __post_init__(self):
        """驗證聚合根的有效性"""
        if not self.host_name or not self.host_name.strip():
            raise ValueError("主機名稱不能為空")
        
        if not self.operating_system or not self.operating_system.strip():
            raise ValueError("作業系統不能為空")
        
        if not self.running_applications or not self.running_applications.strip():
            raise ValueError("運行的應用程式不能為空")
        
        if not self.owner or not self.owner.strip():
            raise ValueError("負責人不能為空")
        
        if not isinstance(self.data_sensitivity, DataSensitivity):
            raise ValueError("data_sensitivity 必須是 DataSensitivity 值物件")
        
        if not isinstance(self.business_criticality, BusinessCriticality):
            raise ValueError("business_criticality 必須是 BusinessCriticality 值物件")
    
    @classmethod
    def create(
        cls,
        host_name: str,
        operating_system: str,
        running_applications: str,
        owner: str,
        data_sensitivity: str,
        business_criticality: str,
        ip: Optional[str] = None,
        item: Optional[int] = None,
        is_public_facing: bool = False,
        created_by: str = "system",
    ) -> "Asset":
        """
        建立資產（工廠方法）
        
        Args:
            host_name: 主機名稱
            operating_system: 作業系統
            running_applications: 運行的應用程式
            owner: 負責人
            data_sensitivity: 資料敏感度（高/中/低）
            business_criticality: 業務關鍵性（高/中/低）
            ip: IP 位址（可選）
            item: 資產項目編號（可選）
            is_public_facing: 是否對外暴露（預設 False）
            created_by: 建立者（預設 "system"）
        
        Returns:
            Asset: 新建立的資產聚合根
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        asset = cls(
            id=str(uuid.uuid4()),
            host_name=host_name,
            ip=ip,
            item=item,
            operating_system=operating_system,
            running_applications=running_applications,
            owner=owner,
            data_sensitivity=DataSensitivity(data_sensitivity),
            business_criticality=BusinessCriticality(business_criticality),
            is_public_facing=is_public_facing,
            created_by=created_by,
            updated_by=created_by,
        )
        
        # 發布領域事件
        asset._domain_events.append(
            AssetCreatedEvent(
                asset_id=asset.id,
                host_name=asset.host_name,
                owner=asset.owner,
            )
        )
        
        return asset
    
    def update(
        self,
        host_name: Optional[str] = None,
        ip: Optional[str] = None,
        operating_system: Optional[str] = None,
        running_applications: Optional[str] = None,
        owner: Optional[str] = None,
        data_sensitivity: Optional[str] = None,
        business_criticality: Optional[str] = None,
        is_public_facing: Optional[bool] = None,
        updated_by: str = "system",
    ) -> None:
        """
        更新資產資訊
        
        Args:
            host_name: 主機名稱（可選）
            ip: IP 位址（可選）
            operating_system: 作業系統（可選）
            running_applications: 運行的應用程式（可選）
            owner: 負責人（可選）
            data_sensitivity: 資料敏感度（可選）
            business_criticality: 業務關鍵性（可選）
            is_public_facing: 是否對外暴露（可選）
            updated_by: 更新者（預設 "system"）
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        updated_fields = []
        
        if host_name is not None:
            if not host_name.strip():
                raise ValueError("主機名稱不能為空")
            self.host_name = host_name
            updated_fields.append("host_name")
        
        if ip is not None:
            self.ip = ip
            updated_fields.append("ip")
        
        if operating_system is not None:
            if not operating_system.strip():
                raise ValueError("作業系統不能為空")
            self.operating_system = operating_system
            updated_fields.append("operating_system")
        
        if running_applications is not None:
            if not running_applications.strip():
                raise ValueError("運行的應用程式不能為空")
            self.running_applications = running_applications
            updated_fields.append("running_applications")
        
        if owner is not None:
            if not owner.strip():
                raise ValueError("負責人不能為空")
            self.owner = owner
            updated_fields.append("owner")
        
        if data_sensitivity is not None:
            self.data_sensitivity = DataSensitivity(data_sensitivity)
            updated_fields.append("data_sensitivity")
        
        if business_criticality is not None:
            self.business_criticality = BusinessCriticality(business_criticality)
            updated_fields.append("business_criticality")
        
        if is_public_facing is not None:
            self.is_public_facing = is_public_facing
            updated_fields.append("is_public_facing")
        
        if updated_fields:
            self.updated_at = datetime.utcnow()
            self.updated_by = updated_by
            
            # 發布領域事件
            self._domain_events.append(
                AssetUpdatedEvent(
                    asset_id=self.id,
                    host_name=self.host_name,
                    updated_fields=updated_fields,
                )
            )
    
    def add_product(
        self,
        product_name: str,
        product_version: Optional[str] = None,
        product_type: Optional[str] = None,
        original_text: Optional[str] = None,
    ) -> AssetProduct:
        """
        新增產品資訊
        
        Args:
            product_name: 產品名稱
            product_version: 產品版本（可選）
            product_type: 產品類型（OS/Application，可選）
            original_text: 原始文字（可選）
        
        Returns:
            AssetProduct: 新建立的產品實體
        
        Raises:
            ValueError: 當產品名稱無效時
        """
        if not product_name or not product_name.strip():
            raise ValueError("產品名稱不能為空")
        
        # 檢查是否已存在相同產品
        existing_product = next(
            (
                p
                for p in self.products
                if p.product_name == product_name
                and p.product_version == product_version
            ),
            None,
        )
        
        if existing_product:
            raise ValueError(
                f"產品 {product_name} (版本: {product_version}) 已存在"
            )
        
        product = AssetProduct(
            id=str(uuid.uuid4()),
            product_name=product_name,
            product_version=product_version,
            product_type=product_type,
            original_text=original_text,
        )
        
        self.products.append(product)
        return product
    
    def remove_product(self, product_id: str) -> None:
        """
        移除產品資訊
        
        Args:
            product_id: 產品 ID
        
        Raises:
            ValueError: 當產品不存在時
        """
        product = next((p for p in self.products if p.id == product_id), None)
        
        if not product:
            raise ValueError(f"產品 ID {product_id} 不存在")
        
        self.products.remove(product)
    
    def calculate_risk_weight(self) -> float:
        """
        計算風險權重
        
        風險權重 = 資料敏感度權重 × 業務關鍵性權重
        
        Returns:
            float: 風險權重值
        """
        return self.data_sensitivity.weight * self.business_criticality.weight
    
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
            f"Asset(id='{self.id}', "
            f"host_name='{self.host_name}', "
            f"owner='{self.owner}', "
            f"products_count={len(self.products)})"
        )

