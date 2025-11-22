"""
優先情資需求（PIR）測試資料工廠
"""

import uuid
from datetime import datetime
from typing import Optional

from analysis_assessment.infrastructure.persistence.models import PIR


class PIRFactory:
    """優先情資需求測試資料工廠"""

    @staticmethod
    def create(
        name: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        condition_type: Optional[str] = None,
        condition_value: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        **kwargs
    ) -> PIR:
        """建立測試用 PIR"""
        return PIR(
            id=str(uuid.uuid4()),
            name=name or f"PIR-{kwargs.get('item', 1):02d}",
            description=description or f"Test PIR {kwargs.get('item', 1)} description",
            priority=priority or "高",
            condition_type=condition_type or "產品名稱",
            condition_value=condition_value or "nginx",
            is_enabled=is_enabled if is_enabled is not None else True,
            created_at=kwargs.get("created_at", datetime.utcnow()),
            updated_at=kwargs.get("updated_at", datetime.utcnow()),
            created_by=kwargs.get("created_by", "system"),
            updated_by=kwargs.get("updated_by", "system"),
        )

    @staticmethod
    def create_product_name_pir(**kwargs) -> PIR:
        """建立產品名稱條件 PIR"""
        return PIRFactory.create(
            name=kwargs.get("name", "PIR-01"),
            description=kwargs.get("description", "監控特定產品名稱的威脅"),
            priority=kwargs.get("priority", "高"),
            condition_type="產品名稱",
            condition_value=kwargs.get("condition_value", "nginx"),
            **kwargs
        )

    @staticmethod
    def create_cve_pir(**kwargs) -> PIR:
        """建立 CVE 條件 PIR"""
        return PIRFactory.create(
            name=kwargs.get("name", "PIR-02"),
            description=kwargs.get("description", "監控特定 CVE 編號的威脅"),
            priority=kwargs.get("priority", "高"),
            condition_type="CVE",
            condition_value=kwargs.get("condition_value", "CVE-2024"),
            **kwargs
        )

    @staticmethod
    def create_threat_type_pir(**kwargs) -> PIR:
        """建立威脅類型條件 PIR"""
        return PIRFactory.create(
            name=kwargs.get("name", "PIR-03"),
            description=kwargs.get("description", "監控特定威脅類型的威脅"),
            priority=kwargs.get("priority", "中"),
            condition_type="威脅類型",
            condition_value=kwargs.get("condition_value", "RCE"),
            **kwargs
        )

    @staticmethod
    def create_cisa_kev_pir(**kwargs) -> PIR:
        """建立 CISA KEV 條件 PIR"""
        return PIRFactory.create(
            name=kwargs.get("name", "PIR-04"),
            description=kwargs.get("description", "監控 CISA KEV 清單中的威脅"),
            priority=kwargs.get("priority", "高"),
            condition_type="CISA KEV",
            condition_value=kwargs.get("condition_value", "true"),
            **kwargs
        )

    @staticmethod
    def create_taiwan_cert_pir(**kwargs) -> PIR:
        """建立台灣 CERT 條件 PIR"""
        return PIRFactory.create(
            name=kwargs.get("name", "PIR-05"),
            description=kwargs.get("description", "監控台灣 CERT 通報的威脅"),
            priority=kwargs.get("priority", "中"),
            condition_type="來源",
            condition_value=kwargs.get("condition_value", "TWCERT/CC"),
            **kwargs
        )

