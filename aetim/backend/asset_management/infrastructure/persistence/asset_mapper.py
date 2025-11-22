"""
資產領域模型與資料模型映射器

負責領域模型（Asset）與資料模型（Asset、AssetProduct）之間的轉換。
"""

from typing import List
from ...domain.aggregates.asset import Asset
from ...domain.entities.asset_product import AssetProduct
from ...domain.value_objects.data_sensitivity import DataSensitivity
from ...domain.value_objects.business_criticality import BusinessCriticality
from .models import Asset as AssetModel, AssetProduct as AssetProductModel


class AssetMapper:
    """資產映射器"""
    
    @staticmethod
    def to_domain(asset_model: AssetModel) -> Asset:
        """
        將資料模型轉換為領域模型
        
        Args:
            asset_model: 資料模型
        
        Returns:
            Asset: 領域模型（聚合根）
        """
        # 轉換產品
        products = [
            AssetProduct(
                id=str(product.id),
                product_name=product.product_name,
                product_version=product.product_version,
                product_type=product.product_type,
                original_text=product.original_text,
            )
            for product in asset_model.products
        ]
        
        # 建立領域模型
        asset = Asset(
            id=str(asset_model.id),
            host_name=asset_model.host_name,
            ip=asset_model.ip,
            item=asset_model.item,
            operating_system=asset_model.operating_system,
            running_applications=asset_model.running_applications,
            owner=asset_model.owner,
            data_sensitivity=DataSensitivity(asset_model.data_sensitivity),
            business_criticality=BusinessCriticality(asset_model.business_criticality),
            is_public_facing=asset_model.is_public_facing,
            products=products,
            created_at=asset_model.created_at,
            updated_at=asset_model.updated_at,
            created_by=asset_model.created_by,
            updated_by=asset_model.updated_by,
        )
        
        # 清除領域事件（從資料庫載入的物件不應有未發布的事件）
        asset.clear_domain_events()
        
        return asset
    
    @staticmethod
    def to_model(asset: Asset) -> AssetModel:
        """
        將領域模型轉換為資料模型
        
        Args:
            asset: 領域模型（聚合根）
        
        Returns:
            AssetModel: 資料模型
        """
        asset_model = AssetModel(
            id=asset.id,
            item=asset.item,
            ip=asset.ip,
            host_name=asset.host_name,
            operating_system=asset.operating_system,
            running_applications=asset.running_applications,
            owner=asset.owner,
            data_sensitivity=asset.data_sensitivity.value,
            is_public_facing=asset.is_public_facing,
            business_criticality=asset.business_criticality.value,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
            created_by=asset.created_by,
            updated_by=asset.updated_by,
        )
        
        # 轉換產品
        asset_model.products = [
            AssetProductModel(
                id=product.id,
                asset_id=asset.id,
                product_name=product.product_name,
                product_version=product.product_version,
                product_type=product.product_type,
                original_text=product.original_text,
                created_at=asset.created_at,
                updated_at=asset.updated_at,
            )
            for product in asset.products
        ]
        
        return asset_model
    
    @staticmethod
    def update_model(asset_model: AssetModel, asset: Asset) -> None:
        """
        更新資料模型（不建立新物件）
        
        Args:
            asset_model: 現有的資料模型
            asset: 領域模型（聚合根）
        """
        asset_model.item = asset.item
        asset_model.ip = asset.ip
        asset_model.host_name = asset.host_name
        asset_model.operating_system = asset.operating_system
        asset_model.running_applications = asset.running_applications
        asset_model.owner = asset.owner
        asset_model.data_sensitivity = asset.data_sensitivity.value
        asset_model.is_public_facing = asset.is_public_facing
        asset_model.business_criticality = asset.business_criticality.value
        asset_model.updated_at = asset.updated_at
        asset_model.updated_by = asset.updated_by
        
        # 產品更新在 Repository 層處理（需要 session）

