"""
資產測試資料工廠
"""

import uuid
from datetime import datetime
from typing import Optional

from asset_management.infrastructure.persistence.models import Asset, AssetProduct


class AssetFactory:
    """資產測試資料工廠"""

    @staticmethod
    def create(
        host_name: Optional[str] = None,
        ip: Optional[str] = None,
        operating_system: Optional[str] = None,
        running_applications: Optional[str] = None,
        owner: Optional[str] = None,
        data_sensitivity: Optional[str] = None,
        is_public_facing: Optional[bool] = None,
        business_criticality: Optional[str] = None,
        **kwargs
    ) -> Asset:
        """建立測試用資產"""
        return Asset(
            id=str(uuid.uuid4()),
            item=kwargs.get("item"),
            ip=ip or f"10.0.{kwargs.get('item', 1) % 255}.{kwargs.get('item', 1) % 255}",
            host_name=host_name or f"test-host-{kwargs.get('item', 1)}",
            operating_system=operating_system or "Linux 5.4",
            running_applications=running_applications or "nginx 1.18",
            owner=owner or "test-owner",
            data_sensitivity=data_sensitivity or "中",
            is_public_facing=is_public_facing if is_public_facing is not None else False,
            business_criticality=business_criticality or "中",
            created_at=kwargs.get("created_at", datetime.utcnow()),
            updated_at=kwargs.get("updated_at", datetime.utcnow()),
            created_by=kwargs.get("created_by", "system"),
            updated_by=kwargs.get("updated_by", "system"),
        )

    @staticmethod
    def create_high_priority(**kwargs) -> Asset:
        """建立高優先級資產（高敏感度、高關鍵性、對外暴露）"""
        return AssetFactory.create(
            data_sensitivity="高",
            business_criticality="高",
            is_public_facing=True,
            **kwargs
        )

    @staticmethod
    def create_low_priority(**kwargs) -> Asset:
        """建立低優先級資產（低敏感度、低關鍵性、不對外暴露）"""
        return AssetFactory.create(
            data_sensitivity="低",
            business_criticality="低",
            is_public_facing=False,
            **kwargs
        )

    @staticmethod
    def create_public_facing(**kwargs) -> Asset:
        """建立對外暴露資產"""
        return AssetFactory.create(
            is_public_facing=True,
            **kwargs
        )

    @staticmethod
    def create_batch(count: int, **kwargs) -> list[Asset]:
        """批次建立資產"""
        return [AssetFactory.create(item=i, **kwargs) for i in range(1, count + 1)]


class AssetProductFactory:
    """資產產品測試資料工廠"""

    @staticmethod
    def create(
        asset_id: str,
        product_name: Optional[str] = None,
        product_version: Optional[str] = None,
        product_type: Optional[str] = None,
        original_text: Optional[str] = None,
        **kwargs
    ) -> AssetProduct:
        """建立測試用資產產品"""
        return AssetProduct(
            id=str(uuid.uuid4()),
            asset_id=asset_id,
            product_name=product_name or "nginx",
            product_version=product_version or "1.18.0",
            product_type=product_type or "Application",
            original_text=original_text or f"{product_name or 'nginx'} {product_version or '1.18.0'}",
            created_at=kwargs.get("created_at", datetime.utcnow()),
            updated_at=kwargs.get("updated_at", datetime.utcnow()),
        )

    @staticmethod
    def create_os_product(asset_id: str, **kwargs) -> AssetProduct:
        """建立作業系統產品"""
        return AssetProductFactory.create(
            asset_id=asset_id,
            product_name=kwargs.get("product_name", "Linux"),
            product_version=kwargs.get("product_version", "5.4"),
            product_type="OS",
            **kwargs
        )

    @staticmethod
    def create_application_product(asset_id: str, **kwargs) -> AssetProduct:
        """建立應用程式產品"""
        return AssetProductFactory.create(
            asset_id=asset_id,
            product_name=kwargs.get("product_name", "nginx"),
            product_version=kwargs.get("product_version", "1.18.0"),
            product_type="Application",
            **kwargs
        )

