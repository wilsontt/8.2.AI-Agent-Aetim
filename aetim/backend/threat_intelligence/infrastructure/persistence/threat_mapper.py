"""
威脅 Mapper

處理領域模型與資料庫模型之間的轉換。
"""

import json
import uuid
from typing import List, Optional
from datetime import datetime

from ...domain.aggregates.threat import Threat
from ...domain.value_objects.threat_severity import ThreatSeverity
from ...domain.value_objects.threat_status import ThreatStatus
from ...domain.entities.threat_product import ThreatProduct
from ..models import Threat as ThreatModel
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class ThreatMapper:
    """
    威脅 Mapper
    
    負責領域模型與資料庫模型之間的轉換。
    """
    
    @staticmethod
    def to_domain(model: ThreatModel) -> Threat:
        """
        將資料庫模型轉換為領域模型
        
        Args:
            model: 資料庫模型
        
        Returns:
            Threat: 領域聚合根
        """
        # 解析產品資訊
        products = []
        if model.affected_products:
            try:
                products_data = json.loads(model.affected_products)
                for product_data in products_data:
                    # 如果沒有 id，自動生成
                    product_id = product_data.get("id")
                    if not product_id:
                        product_id = str(uuid.uuid4())
                    
                    products.append(
                        ThreatProduct(
                            id=product_id,
                            product_name=product_data.get("product_name", ""),
                            product_version=product_data.get("product_version"),
                            product_type=product_data.get("product_type"),
                            original_text=product_data.get("original_text"),
                        )
                    )
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(
                    f"解析產品資訊失敗：{str(e)}",
                    extra={"threat_id": model.id, "error": str(e)}
                )
        
        # 解析 TTPs
        ttps = []
        if model.ttps:
            try:
                ttps = json.loads(model.ttps)
            except json.JSONDecodeError as e:
                logger.warning(
                    f"解析 TTPs 失敗：{str(e)}",
                    extra={"threat_id": model.id, "error": str(e)}
                )
        
        # 解析 IOCs
        iocs = {"ips": [], "domains": [], "hashes": []}
        if model.iocs:
            try:
                iocs = json.loads(model.iocs)
            except json.JSONDecodeError as e:
                logger.warning(
                    f"解析 IOCs 失敗：{str(e)}",
                    extra={"threat_id": model.id, "error": str(e)}
                )
        
        # 轉換嚴重程度
        severity = None
        if model.severity:
            try:
                severity = ThreatSeverity(model.severity)
            except ValueError:
                logger.warning(
                    f"無效的嚴重程度：{model.severity}",
                    extra={"threat_id": model.id}
                )
        
        # 轉換狀態
        status = ThreatStatus(model.status) if model.status else ThreatStatus("New")
        
        # 轉換 CVSS 分數
        cvss_base_score = None
        if model.cvss_base_score is not None:
            cvss_base_score = float(model.cvss_base_score)
        
        return Threat(
            id=model.id,
            threat_feed_id=model.threat_feed_id,
            title=model.title,
            description=model.description,
            cve_id=model.cve,
            cvss_base_score=cvss_base_score,
            cvss_vector=model.cvss_vector,
            severity=severity,
            status=status,
            source_url=model.source_url,
            published_date=model.published_date,
            collected_at=model.created_at,  # 使用 created_at 作為 collected_at
            products=products,
            ttps=ttps,
            iocs=iocs,
            raw_data=model.raw_data,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    
    @staticmethod
    def to_model(threat: Threat) -> ThreatModel:
        """
        將領域模型轉換為資料庫模型（新增用）
        
        Args:
            threat: 領域聚合根
        
        Returns:
            ThreatModel: 資料庫模型
        """
        # 序列化產品資訊
        affected_products = None
        if threat.products:
            products_data = [
                {
                    "id": p.id,
                    "product_name": p.product_name,
                    "product_version": p.product_version,
                    "product_type": p.product_type,
                    "original_text": p.original_text,
                }
                for p in threat.products
            ]
            affected_products = json.dumps(products_data, ensure_ascii=False)
        
        # 序列化 TTPs
        ttps_json = None
        if threat.ttps:
            ttps_json = json.dumps(threat.ttps, ensure_ascii=False)
        
        # 序列化 IOCs
        iocs_json = None
        if threat.iocs:
            iocs_json = json.dumps(threat.iocs, ensure_ascii=False)
        
        return ThreatModel(
            id=threat.id,
            threat_feed_id=threat.threat_feed_id,
            cve=threat.cve_id,
            title=threat.title,
            description=threat.description,
            cvss_base_score=threat.cvss_base_score,
            cvss_vector=threat.cvss_vector,
            severity=threat.severity.value if threat.severity else None,
            status=threat.status.value,
            source_url=threat.source_url,
            published_date=threat.published_date,
            affected_products=affected_products,
            ttps=ttps_json,
            iocs=iocs_json,
            raw_data=threat.raw_data,
            created_at=threat.created_at,
            updated_at=threat.updated_at,
        )
    
    @staticmethod
    def update_model(model: ThreatModel, threat: Threat) -> None:
        """
        更新資料庫模型（更新用）
        
        Args:
            model: 現有的資料庫模型
            threat: 領域聚合根
        """
        # 更新基本欄位
        model.cve = threat.cve_id
        model.title = threat.title
        model.description = threat.description
        model.cvss_base_score = threat.cvss_base_score
        model.cvss_vector = threat.cvss_vector
        model.severity = threat.severity.value if threat.severity else None
        model.status = threat.status.value
        model.source_url = threat.source_url
        model.published_date = threat.published_date
        model.updated_at = datetime.utcnow()
        
        # 序列化產品資訊
        if threat.products:
            products_data = [
                {
                    "id": p.id,
                    "product_name": p.product_name,
                    "product_version": p.product_version,
                    "product_type": p.product_type,
                    "original_text": p.original_text,
                }
                for p in threat.products
            ]
            model.affected_products = json.dumps(products_data, ensure_ascii=False)
        else:
            model.affected_products = None
        
        # 序列化 TTPs
        if threat.ttps:
            model.ttps = json.dumps(threat.ttps, ensure_ascii=False)
        else:
            model.ttps = None
        
        # 序列化 IOCs
        if threat.iocs:
            model.iocs = json.dumps(threat.iocs, ensure_ascii=False)
        else:
            model.iocs = None
        
        # 更新原始資料
        model.raw_data = threat.raw_data

