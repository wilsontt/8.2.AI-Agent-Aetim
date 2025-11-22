"""
資產 Repository 實作

使用 SQLAlchemy 實作資產的持久化操作。
"""

from typing import Optional, List, Tuple
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...domain.interfaces.asset_repository import IAssetRepository
from ...domain.aggregates.asset import Asset
from .models import Asset as AssetModel, AssetProduct as AssetProductModel
from .asset_mapper import AssetMapper


class AssetRepository(IAssetRepository):
    """資產 Repository 實作"""
    
    def __init__(self, session: AsyncSession):
        """
        初始化 Repository
        
        Args:
            session: 資料庫 Session
        """
        self.session = session
    
    async def save(self, asset: Asset) -> None:
        """
        儲存資產（新增或更新）
        
        Args:
            asset: 資產聚合根
        """
        # 檢查資產是否存在
        result = await self.session.execute(
            select(AssetModel)
            .options(selectinload(AssetModel.products))
            .where(AssetModel.id == asset.id)
        )
        existing_asset = result.scalar_one_or_none()
        
        if existing_asset:
            # 更新現有資產
            AssetMapper.update_model(existing_asset, asset)
            
            # 更新產品（刪除舊的，新增新的）
            # 先刪除所有現有產品
            for product_model in list(existing_asset.products):
                await self.session.delete(product_model)
            
            # 新增新產品
            for product in asset.products:
                product_model = AssetProductModel(
                    id=product.id,
                    asset_id=asset.id,
                    product_name=product.product_name,
                    product_version=product.product_version,
                    product_type=product.product_type,
                    original_text=product.original_text,
                    created_at=asset.created_at,
                    updated_at=asset.updated_at,
                )
                existing_asset.products.append(product_model)
            
            self.session.add(existing_asset)
        else:
            # 新增資產
            asset_model = AssetMapper.to_model(asset)
            self.session.add(asset_model)
        
        await self.session.commit()
    
    async def get_by_id(self, asset_id: str) -> Optional[Asset]:
        """
        依 ID 查詢資產
        
        Args:
            asset_id: 資產 ID
        
        Returns:
            Asset: 資產聚合根，如果不存在則返回 None
        """
        result = await self.session.execute(
            select(AssetModel)
            .options(selectinload(AssetModel.products))  # Eager Loading
            .where(AssetModel.id == asset_id)
        )
        asset_model = result.scalar_one_or_none()
        
        if not asset_model:
            return None
        
        return AssetMapper.to_domain(asset_model)
    
    async def delete(self, asset_id: str) -> None:
        """
        刪除資產
        
        Args:
            asset_id: 資產 ID
        
        Raises:
            ValueError: 當資產不存在時
        """
        result = await self.session.execute(
            select(AssetModel).where(AssetModel.id == asset_id)
        )
        asset_model = result.scalar_one_or_none()
        
        if not asset_model:
            raise ValueError(f"資產 ID {asset_id} 不存在")
        
        # 刪除資產（cascade 會自動刪除相關產品）
        await self.session.delete(asset_model)
        await self.session.commit()
    
    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> Tuple[List[Asset], int]:
        """
        查詢所有資產（支援分頁與排序）
        
        Args:
            page: 頁碼（從 1 開始）
            page_size: 每頁筆數（預設 20，至少 20）
            sort_by: 排序欄位（host_name、owner、created_at 等）
            sort_order: 排序方向（asc、desc）
        
        Returns:
            Tuple[List[Asset], int]: (資產清單, 總筆數)
        """
        # 確保 page_size 至少為 20
        page_size = max(page_size, 20)
        
        # 建立查詢
        query = select(AssetModel).options(selectinload(AssetModel.products))
        
        # 排序
        if sort_by:
            sort_column = self._get_sort_column(sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            # 預設排序：依建立時間降序
            query = query.order_by(AssetModel.created_at.desc())
        
        # 計算總筆數
        count_query = select(func.count(AssetModel.id))
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar()
        
        # 分頁
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # 執行查詢
        result = await self.session.execute(query)
        asset_models = result.scalars().all()
        
        # 轉換為領域模型
        assets = [AssetMapper.to_domain(model) for model in asset_models]
        
        return assets, total_count
    
    async def search(
        self,
        product_name: Optional[str] = None,
        product_version: Optional[str] = None,
        product_type: Optional[str] = None,
        is_public_facing: Optional[bool] = None,
        data_sensitivity: Optional[str] = None,
        business_criticality: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> Tuple[List[Asset], int]:
        """
        搜尋資產（支援多條件篩選）
        
        Args:
            product_name: 產品名稱（模糊搜尋）
            product_version: 產品版本（模糊搜尋）
            product_type: 產品類型（OS/Application）
            is_public_facing: 是否對外暴露
            data_sensitivity: 資料敏感度（高/中/低）
            business_criticality: 業務關鍵性（高/中/低）
            page: 頁碼（從 1 開始）
            page_size: 每頁筆數（預設 20）
            sort_by: 排序欄位
            sort_order: 排序方向（asc、desc）
        
        Returns:
            Tuple[List[Asset], int]: (資產清單, 總筆數)
        """
        # 確保 page_size 至少為 20
        page_size = max(page_size, 20)
        
        # 建立查詢（使用 JOIN 以支援產品篩選）
        query = (
            select(AssetModel)
            .distinct()
            .options(selectinload(AssetModel.products))
            .outerjoin(AssetProductModel)
        )
        
        # 建立篩選條件
        conditions = []
        
        if product_name:
            conditions.append(
                AssetProductModel.product_name.ilike(f"%{product_name}%")
            )
        
        if product_version:
            conditions.append(
                AssetProductModel.product_version.ilike(f"%{product_version}%")
            )
        
        if product_type:
            conditions.append(AssetProductModel.product_type == product_type)
        
        if is_public_facing is not None:
            conditions.append(AssetModel.is_public_facing == is_public_facing)
        
        if data_sensitivity:
            conditions.append(AssetModel.data_sensitivity == data_sensitivity)
        
        if business_criticality:
            conditions.append(AssetModel.business_criticality == business_criticality)
        
        # 套用篩選條件
        if conditions:
            query = query.where(and_(*conditions))
        
        # 排序
        if sort_by:
            sort_column = self._get_sort_column(sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            # 預設排序：依建立時間降序
            query = query.order_by(AssetModel.created_at.desc())
        
        # 計算總筆數
        count_query = (
            select(func.count(func.distinct(AssetModel.id)))
            .outerjoin(AssetProductModel)
        )
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar()
        
        # 分頁
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # 執行查詢
        result = await self.session.execute(query)
        asset_models = result.scalars().all()
        
        # 轉換為領域模型
        assets = [AssetMapper.to_domain(model) for model in asset_models]
        
        return assets, total_count
    
    def _get_sort_column(self, sort_by: str):
        """
        取得排序欄位
        
        Args:
            sort_by: 排序欄位名稱
        
        Returns:
            排序欄位
        
        Raises:
            ValueError: 當排序欄位無效時
        """
        sort_mapping = {
            "host_name": AssetModel.host_name,
            "owner": AssetModel.owner,
            "created_at": AssetModel.created_at,
            "updated_at": AssetModel.updated_at,
            "data_sensitivity": AssetModel.data_sensitivity,
            "business_criticality": AssetModel.business_criticality,
        }
        
        if sort_by not in sort_mapping:
            raise ValueError(f"無效的排序欄位：{sort_by}")
        
        return sort_mapping[sort_by]

