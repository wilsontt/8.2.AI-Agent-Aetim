"""
資產服務

提供資產的 CRUD 操作和查詢功能。
"""

from typing import Optional, List, Tuple
from ...domain.interfaces.asset_repository import IAssetRepository
from ...domain.aggregates.asset import Asset
from ...domain.domain_services.asset_parsing_service import AssetParsingService
from ..dtos.asset_dto import (
    CreateAssetRequest,
    UpdateAssetRequest,
    AssetResponse,
    AssetListResponse,
    AssetSearchRequest,
    ProductResponse,
)
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class AssetService:
    """
    資產服務
    
    提供資產的 CRUD 操作和查詢功能。
    """
    
    def __init__(
        self,
        repository: IAssetRepository,
        parsing_service: AssetParsingService,
    ):
        """
        初始化服務
        
        Args:
            repository: 資產 Repository
            parsing_service: 資產解析服務
        """
        self.repository = repository
        self.parsing_service = parsing_service
    
    async def create_asset(
        self,
        request: CreateAssetRequest,
        user_id: str = "system",
    ) -> str:
        """
        建立資產
        
        Args:
            request: 建立資產請求
            user_id: 使用者 ID（預設 "system"）
        
        Returns:
            str: 資產 ID
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        logger.info("建立資產", extra={"host_name": request.host_name, "user_id": user_id})
        
        # 1. 建立資產聚合
        asset = Asset.create(
            host_name=request.host_name,
            operating_system=request.operating_system,
            running_applications=request.running_applications,
            owner=request.owner,
            data_sensitivity=request.data_sensitivity,
            business_criticality=request.business_criticality,
            ip=request.ip,
            item=request.item,
            is_public_facing=request.is_public_facing,
            created_by=user_id,
        )
        
        # 2. 解析產品資訊
        products = self.parsing_service.parse_products(request.running_applications)
        for product in products:
            try:
                asset.add_product(
                    product.product_name,
                    product.product_version,
                    product.product_type,
                    product.original_text,
                )
            except ValueError as e:
                # 如果產品已存在，記錄警告但繼續處理
                logger.warning("產品已存在，跳過", extra={"error": str(e), "product_name": product.product_name})
        
        # 3. 儲存
        await self.repository.save(asset)
        
        # 4. 發布領域事件（如果需要）
        # 注意：領域事件發布應該在應用層處理，這裡先記錄日誌
        events = asset.get_domain_events()
        if events:
            logger.info("資產建立事件", extra={"asset_id": asset.id, "event_count": len(events)})
        
        logger.info("資產建立成功", extra={"asset_id": asset.id})
        
        return asset.id
    
    async def update_asset(
        self,
        asset_id: str,
        request: UpdateAssetRequest,
        user_id: str = "system",
    ) -> None:
        """
        更新資產
        
        Args:
            asset_id: 資產 ID
            request: 更新資產請求
            user_id: 使用者 ID（預設 "system"）
        
        Raises:
            ValueError: 當資產不存在或輸入參數無效時
        """
        logger.info("更新資產", extra={"asset_id": asset_id, "user_id": user_id})
        
        # 1. 取得資產
        asset = await self.repository.get_by_id(asset_id)
        if not asset:
            raise ValueError(f"資產 ID {asset_id} 不存在")
        
        # 2. 更新資產
        update_kwargs = {}
        if request.host_name is not None:
            update_kwargs["host_name"] = request.host_name
        if request.ip is not None:
            update_kwargs["ip"] = request.ip
        if request.operating_system is not None:
            update_kwargs["operating_system"] = request.operating_system
        if request.running_applications is not None:
            update_kwargs["running_applications"] = request.running_applications
        if request.owner is not None:
            update_kwargs["owner"] = request.owner
        if request.data_sensitivity is not None:
            update_kwargs["data_sensitivity"] = request.data_sensitivity
        if request.is_public_facing is not None:
            update_kwargs["is_public_facing"] = request.is_public_facing
        if request.business_criticality is not None:
            update_kwargs["business_criticality"] = request.business_criticality
        
        asset.update(updated_by=user_id, **update_kwargs)
        
        # 3. 如果更新了 running_applications，重新解析產品
        if request.running_applications is not None:
            # 清除現有產品
            for product in list(asset.products):
                asset.remove_product(product.id)
            
            # 解析並新增新產品
            products = self.parsing_service.parse_products(request.running_applications)
            for product in products:
                try:
                    asset.add_product(
                        product.product_name,
                        product.product_version,
                        product.product_type,
                        product.original_text,
                    )
                except ValueError as e:
                    logger.warning("產品已存在，跳過", extra={"error": str(e), "product_name": product.product_name})
        
        # 4. 儲存
        await self.repository.save(asset)
        
        # 5. 發布領域事件（如果需要）
        events = asset.get_domain_events()
        if events:
            logger.info("資產更新事件", extra={"asset_id": asset.id, "event_count": len(events)})
        
        logger.info("資產更新成功", extra={"asset_id": asset.id})
    
    async def delete_asset(
        self,
        asset_id: str,
        user_id: str = "system",
        confirm: bool = False,
    ) -> None:
        """
        刪除資產（包含確認邏輯）
        
        Args:
            asset_id: 資產 ID
            user_id: 使用者 ID（預設 "system"）
            confirm: 是否確認刪除（預設 False）
        
        Raises:
            ValueError: 當資產不存在或未確認刪除時
        """
        logger.info("刪除資產", extra={"asset_id": asset_id, "user_id": user_id, "confirm": confirm})
        
        if not confirm:
            raise ValueError("刪除資產需要確認，請設定 confirm=True")
        
        # 檢查資產是否存在
        asset = await self.repository.get_by_id(asset_id)
        if not asset:
            raise ValueError(f"資產 ID {asset_id} 不存在")
        
        # 刪除資產
        await self.repository.delete(asset_id)
        
        logger.info("資產刪除成功", extra={"asset_id": asset_id})
    
    async def batch_delete_assets(
        self,
        asset_ids: List[str],
        user_id: str = "system",
        confirm: bool = False,
    ) -> dict:
        """
        批次刪除資產
        
        Args:
            asset_ids: 資產 ID 清單
            user_id: 使用者 ID（預設 "system"）
            confirm: 是否確認刪除（預設 False）
        
        Returns:
            dict: 包含 success_count 和 failure_count 的字典
        
        Raises:
            ValueError: 當未確認刪除時
        """
        logger.info("批次刪除資產", extra={"count": len(asset_ids), "user_id": user_id, "confirm": confirm})
        
        if not confirm:
            raise ValueError("批次刪除資產需要確認，請設定 confirm=True")
        
        success_count = 0
        failure_count = 0
        errors = []
        
        for asset_id in asset_ids:
            try:
                await self.delete_asset(asset_id, user_id, confirm=True)
                success_count += 1
            except Exception as e:
                failure_count += 1
                errors.append({"asset_id": asset_id, "error": str(e)})
                logger.error("刪除資產失敗", extra={"asset_id": asset_id, "error": str(e)})
        
        logger.info("批次刪除完成", extra={"success_count": success_count, "failure_count": failure_count})
        
        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "errors": errors,
        }
    
    async def get_assets(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> AssetListResponse:
        """
        查詢資產清單（支援分頁、排序）
        
        Args:
            page: 頁碼（從 1 開始）
            page_size: 每頁筆數（至少 20）
            sort_by: 排序欄位
            sort_order: 排序方向（asc/desc）
        
        Returns:
            AssetListResponse: 資產清單回應
        """
        # 確保 page_size 至少為 20
        page_size = max(page_size, 20)
        
        assets, total_count = await self.repository.get_all(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        
        # 計算總頁數
        total_pages = (total_count + page_size - 1) // page_size
        
        # 轉換為回應格式
        asset_responses = [self._to_response(asset) for asset in assets]
        
        return AssetListResponse(
            data=asset_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    async def search_assets(
        self,
        request: AssetSearchRequest,
    ) -> AssetListResponse:
        """
        搜尋資產（支援多條件篩選、分頁、排序）
        
        Args:
            request: 搜尋請求
        
        Returns:
            AssetListResponse: 資產清單回應
        """
        assets, total_count = await self.repository.search(
            product_name=request.product_name,
            product_version=request.product_version,
            product_type=request.product_type,
            is_public_facing=request.is_public_facing,
            data_sensitivity=request.data_sensitivity,
            business_criticality=request.business_criticality,
            page=request.page,
            page_size=request.page_size,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
        )
        
        # 計算總頁數
        total_pages = (total_count + request.page_size - 1) // request.page_size
        
        # 轉換為回應格式
        asset_responses = [self._to_response(asset) for asset in assets]
        
        return AssetListResponse(
            data=asset_responses,
            total_count=total_count,
            page=request.page,
            page_size=request.page_size,
            total_pages=total_pages,
        )
    
    async def get_asset_by_id(self, asset_id: str) -> Optional[AssetResponse]:
        """
        查詢資產詳情
        
        Args:
            asset_id: 資產 ID
        
        Returns:
            AssetResponse: 資產回應，如果不存在則返回 None
        """
        asset = await self.repository.get_by_id(asset_id)
        
        if not asset:
            return None
        
        return self._to_response(asset)
    
    def _to_response(self, asset: Asset) -> AssetResponse:
        """
        將領域模型轉換為回應格式
        
        Args:
            asset: 資產聚合根
        
        Returns:
            AssetResponse: 資產回應
        """
        return AssetResponse(
            id=asset.id,
            host_name=asset.host_name,
            ip=asset.ip,
            item=asset.item,
            operating_system=asset.operating_system,
            running_applications=asset.running_applications,
            owner=asset.owner,
            data_sensitivity=asset.data_sensitivity.value,
            is_public_facing=asset.is_public_facing,
            business_criticality=asset.business_criticality.value,
            products=[
                ProductResponse(
                    id=product.id,
                    product_name=product.product_name,
                    product_version=product.product_version,
                    product_type=product.product_type,
                    original_text=product.original_text,
                )
                for product in asset.products
            ],
            created_at=asset.created_at,
            updated_at=asset.updated_at,
            created_by=asset.created_by,
            updated_by=asset.updated_by,
        )

