"""
威脅聚合根

威脅聚合根包含所有業務邏輯方法，負責維護威脅的一致性。
"""

from typing import Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from ..value_objects.threat_severity import ThreatSeverity
from ..value_objects.threat_status import ThreatStatus
from ..entities.threat_product import ThreatProduct
from ..domain_events.threat_created_event import ThreatCreatedEvent
from ..domain_events.threat_status_updated_event import ThreatStatusUpdatedEvent
from ..domain_events.threat_updated_event import ThreatUpdatedEvent


@dataclass
class Threat:
    """
    威脅聚合根
    
    聚合根負責：
    1. 維護聚合的一致性邊界
    2. 實作業務邏輯
    3. 發布領域事件
    
    狀態管理（AC-014-3）：
    - New: 新增（剛收集到的威脅）
    - Analyzing: 分析中（正在進行關聯分析）
    - Processed: 已處理（已完成分析與風險評估）
    - Closed: 已關閉（威脅已處理或不再相關）
    """
    
    id: str
    threat_feed_id: str
    title: str
    description: Optional[str] = None
    cve_id: Optional[str] = None
    cvss_base_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    severity: Optional[ThreatSeverity] = None
    status: ThreatStatus = field(default_factory=lambda: ThreatStatus("New"))
    source_url: Optional[str] = None
    published_date: Optional[datetime] = None
    collected_at: Optional[datetime] = None
    products: List[ThreatProduct] = field(default_factory=list)
    ttps: List[str] = field(default_factory=list)  # TTP IDs (例如：T1566.001)
    iocs: Dict[str, List[str]] = field(
        default_factory=lambda: {"ips": [], "domains": [], "hashes": []}
    )
    raw_data: Optional[str] = None  # JSON 格式的原始資料
    _domain_events: List = field(default_factory=list, repr=False)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """驗證聚合根的有效性"""
        if not self.title or not self.title.strip():
            raise ValueError("威脅標題不能為空")
        
        if not self.threat_feed_id:
            raise ValueError("威脅情資來源 ID 不能為空")
        
        # 如果未提供 ID，自動生成
        if not self.id:
            self.id = str(uuid.uuid4())
        
        # 如果未提供 collected_at，使用當前時間
        if not self.collected_at:
            self.collected_at = datetime.utcnow()
        
        # 根據 CVSS 分數自動設定嚴重程度（如果未提供）
        if self.cvss_base_score is not None and self.severity is None:
            self.severity = self._determine_severity_from_cvss(self.cvss_base_score)
    
    @staticmethod
    def create(
        threat_feed_id: str,
        title: str,
        description: Optional[str] = None,
        cve_id: Optional[str] = None,
        cvss_base_score: Optional[float] = None,
        cvss_vector: Optional[str] = None,
        severity: Optional[ThreatSeverity] = None,
        source_url: Optional[str] = None,
        published_date: Optional[datetime] = None,
        collected_at: Optional[datetime] = None,
    ) -> "Threat":
        """
        建立新的威脅（工廠方法）
        
        Args:
            threat_feed_id: 威脅情資來源 ID
            title: 威脅標題
            description: 威脅描述
            cve_id: CVE 編號
            cvss_base_score: CVSS 基礎分數
            cvss_vector: CVSS 向量字串
            severity: 嚴重程度
            source_url: 來源 URL
            published_date: 發布日期
            collected_at: 收集時間
        
        Returns:
            Threat: 新建立的威脅聚合根
        """
        threat = Threat(
            id=str(uuid.uuid4()),
            threat_feed_id=threat_feed_id,
            title=title,
            description=description,
            cve_id=cve_id,
            cvss_base_score=cvss_base_score,
            cvss_vector=cvss_vector,
            severity=severity,
            source_url=source_url,
            published_date=published_date,
            collected_at=collected_at or datetime.utcnow(),
        )
        
        # 發布領域事件
        threat._domain_events.append(
            ThreatCreatedEvent(
                threat_id=threat.id,
                cve_id=threat.cve_id,
                threat_feed_id=threat.threat_feed_id,
                created_at=threat.created_at,
            )
        )
        
        return threat
    
    def update_status(self, new_status: str) -> None:
        """
        更新威脅狀態（業務規則方法）
        
        Args:
            new_status: 新狀態（New, Analyzing, Processed, Closed）
        
        Raises:
            ValueError: 如果狀態轉換不合法
        """
        new_status_obj = ThreatStatus(new_status)
        old_status = self.status.value
        
        # 檢查狀態轉換是否合法
        if not self.status.can_transition_to(new_status):
            raise ValueError(
                f"無法從狀態 '{old_status}' 轉換到 '{new_status}'。"
                f"允許的轉換：{self.status.TRANSITION_RULES.get(old_status, [])}"
            )
        
        self.status = new_status_obj
        self.updated_at = datetime.utcnow()
        
        # 發布領域事件
        self._domain_events.append(
            ThreatStatusUpdatedEvent(
                threat_id=self.id,
                old_status=old_status,
                new_status=new_status,
                updated_at=self.updated_at,
            )
        )
    
    def add_product(
        self,
        product_name: str,
        product_version: Optional[str] = None,
        product_type: Optional[str] = None,
        original_text: Optional[str] = None,
    ) -> None:
        """
        新增產品資訊（業務規則方法）
        
        Args:
            product_name: 產品名稱
            product_version: 產品版本
            product_type: 產品類型
            original_text: 原始文字
        """
        # 檢查是否已存在相同的產品
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
            return  # 已存在，不重複新增
        
        product = ThreatProduct(
            id=str(uuid.uuid4()),
            product_name=product_name,
            product_version=product_version,
            product_type=product_type,
            original_text=original_text,
        )
        
        self.products.append(product)
        self.updated_at = datetime.utcnow()
        
        # 發布領域事件
        self._domain_events.append(
            ThreatUpdatedEvent(
                threat_id=self.id,
                updated_fields=["products"],
                updated_at=self.updated_at,
            )
        )
    
    def add_ttp(self, ttp_id: str) -> None:
        """
        新增 TTP（業務規則方法）
        
        Args:
            ttp_id: TTP ID（例如：T1566.001）
        """
        if ttp_id not in self.ttps:
            self.ttps.append(ttp_id)
            self.updated_at = datetime.utcnow()
            
            # 發布領域事件
            self._domain_events.append(
                ThreatUpdatedEvent(
                    threat_id=self.id,
                    updated_fields=["ttps"],
                    updated_at=self.updated_at,
                )
            )
    
    def add_ioc(self, ioc_type: str, ioc_value: str) -> None:
        """
        新增 IOC（業務規則方法）
        
        Args:
            ioc_type: IOC 類型（ips, domains, hashes）
            ioc_value: IOC 值
        """
        if ioc_type not in self.iocs:
            self.iocs[ioc_type] = []
        
        if ioc_value not in self.iocs[ioc_type]:
            self.iocs[ioc_type].append(ioc_value)
            self.updated_at = datetime.utcnow()
            
            # 發布領域事件
            self._domain_events.append(
                ThreatUpdatedEvent(
                    threat_id=self.id,
                    updated_fields=["iocs"],
                    updated_at=self.updated_at,
                )
            )
    
    def update(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        cvss_base_score: Optional[float] = None,
        cvss_vector: Optional[str] = None,
        severity: Optional[ThreatSeverity] = None,
        source_url: Optional[str] = None,
        published_date: Optional[datetime] = None,
    ) -> None:
        """
        更新威脅屬性（業務規則方法）
        
        Args:
            title: 威脅標題
            description: 威脅描述
            cvss_base_score: CVSS 基礎分數
            cvss_vector: CVSS 向量字串
            severity: 嚴重程度
            source_url: 來源 URL
            published_date: 發布日期
        """
        updated_fields = []
        
        if title is not None:
            if not title.strip():
                raise ValueError("威脅標題不能為空")
            self.title = title
            updated_fields.append("title")
        
        if description is not None:
            self.description = description
            updated_fields.append("description")
        
        if cvss_base_score is not None:
            self.cvss_base_score = cvss_base_score
            updated_fields.append("cvss_base_score")
            # 如果未提供 severity，根據 CVSS 分數自動設定
            if severity is None:
                self.severity = self._determine_severity_from_cvss(cvss_base_score)
                updated_fields.append("severity")
        
        if cvss_vector is not None:
            self.cvss_vector = cvss_vector
            updated_fields.append("cvss_vector")
        
        if severity is not None:
            self.severity = severity
            updated_fields.append("severity")
        
        if source_url is not None:
            self.source_url = source_url
            updated_fields.append("source_url")
        
        if published_date is not None:
            self.published_date = published_date
            updated_fields.append("published_date")
        
        if updated_fields:
            self.updated_at = datetime.utcnow()
            
            # 發布領域事件
            self._domain_events.append(
                ThreatUpdatedEvent(
                    threat_id=self.id,
                    updated_fields=updated_fields,
                    updated_at=self.updated_at,
                )
            )
    
    def get_domain_events(self) -> List:
        """
        取得領域事件列表
        
        Returns:
            List: 領域事件列表
        """
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """清除領域事件列表"""
        self._domain_events.clear()
    
    @staticmethod
    def _determine_severity_from_cvss(cvss_score: float) -> ThreatSeverity:
        """
        根據 CVSS 分數決定嚴重程度
        
        Args:
            cvss_score: CVSS 分數
        
        Returns:
            ThreatSeverity: 嚴重程度值物件
        """
        if cvss_score >= 9.0:
            return ThreatSeverity("Critical")
        elif cvss_score >= 7.0:
            return ThreatSeverity("High")
        elif cvss_score >= 4.0:
            return ThreatSeverity("Medium")
        else:
            return ThreatSeverity("Low")

