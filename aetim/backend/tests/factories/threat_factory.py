"""
威脅情資測試資料工廠
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from threat_intelligence.infrastructure.persistence.models import ThreatFeed, Threat


class ThreatFeedFactory:
    """威脅情資來源測試資料工廠"""

    @staticmethod
    def create(
        name: Optional[str] = None,
        priority: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        collection_frequency: Optional[str] = None,
        **kwargs
    ) -> ThreatFeed:
        """建立測試用威脅情資來源"""
        return ThreatFeed(
            id=str(uuid.uuid4()),
            name=name or "Test Feed",
            description=kwargs.get("description", "Test threat feed"),
            priority=priority or "P1",
            is_enabled=is_enabled if is_enabled is not None else True,
            collection_frequency=collection_frequency or "每日",
            collection_strategy=kwargs.get("collection_strategy", "API"),
            api_key=kwargs.get("api_key"),
            last_collection_time=kwargs.get("last_collection_time"),
            last_collection_status=kwargs.get("last_collection_status"),
            last_collection_error=kwargs.get("last_collection_error"),
            created_at=kwargs.get("created_at", datetime.utcnow()),
            updated_at=kwargs.get("updated_at", datetime.utcnow()),
            created_by=kwargs.get("created_by", "system"),
            updated_by=kwargs.get("updated_by", "system"),
        )

    @staticmethod
    def create_cisa_kev(**kwargs) -> ThreatFeed:
        """建立 CISA KEV 來源"""
        return ThreatFeedFactory.create(
            name="CISA KEV",
            priority="P0",
            collection_frequency="每小時",
            collection_strategy="API / JSON Feed - 最高優先級，任何匹配資產的 CVE 將觸發即時緊急警報",
            **kwargs
        )

    @staticmethod
    def create_nvd(**kwargs) -> ThreatFeed:
        """建立 NVD 來源"""
        return ThreatFeedFactory.create(
            name="NVD",
            priority="P1",
            collection_frequency="每日",
            collection_strategy="API - 使用資產清單中的關鍵字 (CPEs) 進行主動查詢",
            **kwargs
        )

    @staticmethod
    def create_vmware_vmsa(**kwargs) -> ThreatFeed:
        """建立 VMware VMSA 來源"""
        return ThreatFeedFactory.create(
            name="VMware VMSA",
            priority="P1",
            collection_frequency="每日",
            collection_strategy="RSS Feeds - VMware VMSA 的 RSS 訂閱",
            **kwargs
        )

    @staticmethod
    def create_msrc(**kwargs) -> ThreatFeed:
        """建立 MSRC 來源"""
        return ThreatFeedFactory.create(
            name="MSRC",
            priority="P1",
            collection_frequency="每日",
            collection_strategy="RSS Feeds - MSRC 的 RSS 訂閱",
            **kwargs
        )

    @staticmethod
    def create_twcert(**kwargs) -> ThreatFeed:
        """建立 TWCERT/CC 來源"""
        return ThreatFeedFactory.create(
            name="TWCERT/CC & TW-CERT",
            priority="P2",
            collection_frequency="每日",
            collection_strategy="Email / RSS / Web 爬蟲 - AI 使用 NLP 處理中文通報，提取 IOCs",
            **kwargs
        )


class ThreatFactory:
    """威脅測試資料工廠"""

    @staticmethod
    def create(
        threat_feed_id: str,
        cve: Optional[str] = None,
        title: Optional[str] = None,
        cvss_base_score: Optional[float] = None,
        severity: Optional[str] = None,
        **kwargs
    ) -> Threat:
        """建立測試用威脅"""
        return Threat(
            id=str(uuid.uuid4()),
            threat_feed_id=threat_feed_id,
            cve=cve or f"CVE-2024-{kwargs.get('item', 1):04d}",
            title=title or f"Test Threat {kwargs.get('item', 1)}",
            description=kwargs.get("description", "Test threat description"),
            cvss_base_score=cvss_base_score or 7.5,
            cvss_vector=kwargs.get("cvss_vector"),
            severity=severity or "High",
            published_date=kwargs.get("published_date", datetime.utcnow() - timedelta(days=1)),
            affected_products=kwargs.get("affected_products"),
            threat_type=kwargs.get("threat_type", "RCE"),
            ttps=kwargs.get("ttps"),
            iocs=kwargs.get("iocs"),
            source_url=kwargs.get("source_url", "https://example.com/threat"),
            raw_data=kwargs.get("raw_data"),
            status=kwargs.get("status", "New"),
            created_at=kwargs.get("created_at", datetime.utcnow()),
            updated_at=kwargs.get("updated_at", datetime.utcnow()),
        )

    @staticmethod
    def create_critical(**kwargs) -> Threat:
        """建立嚴重威脅（CVSS >= 9.0）"""
        return ThreatFactory.create(
            cvss_base_score=9.5,
            severity="Critical",
            **kwargs
        )

    @staticmethod
    def create_high(**kwargs) -> Threat:
        """建立高風險威脅（CVSS 7.0-8.9）"""
        return ThreatFactory.create(
            cvss_base_score=7.5,
            severity="High",
            **kwargs
        )

    @staticmethod
    def create_medium(**kwargs) -> Threat:
        """建立中風險威脅（CVSS 4.0-6.9）"""
        return ThreatFactory.create(
            cvss_base_score=5.5,
            severity="Medium",
            **kwargs
        )

    @staticmethod
    def create_low(**kwargs) -> Threat:
        """建立低風險威脅（CVSS < 4.0）"""
        return ThreatFactory.create(
            cvss_base_score=3.5,
            severity="Low",
            **kwargs
        )

