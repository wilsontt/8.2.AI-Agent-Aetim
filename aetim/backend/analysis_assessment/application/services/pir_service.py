"""
PIR 服務

提供 PIR 的 CRUD 操作和查詢功能。
"""

from typing import Optional, List
from ...domain.interfaces.pir_repository import IPIRRepository
from ...domain.aggregates.pir import PIR
from ..dtos.pir_dto import (
    CreatePIRRequest,
    UpdatePIRRequest,
    PIRResponse,
    PIRListResponse,
)
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class PIRService:
    """
    PIR 服務
    
    提供 PIR 的 CRUD 操作和查詢功能。
    """
    
    def __init__(self, repository: IPIRRepository):
        """
        初始化服務
        
        Args:
            repository: PIR Repository
        """
        self.repository = repository
    
    async def create_pir(
        self,
        request: CreatePIRRequest,
        user_id: str = "system",
    ) -> str:
        """
        建立 PIR
        
        Args:
            request: 建立 PIR 請求
            user_id: 使用者 ID（預設 "system"）
        
        Returns:
            str: PIR ID
        
        Raises:
            ValueError: 當輸入參數無效時
        """
        logger.info("建立 PIR", extra={"name": request.name, "user_id": user_id})
        
        # 1. 建立 PIR 聚合
        pir = PIR.create(
            name=request.name,
            description=request.description,
            priority=request.priority,
            condition_type=request.condition_type,
            condition_value=request.condition_value,
            is_enabled=request.is_enabled,
            created_by=user_id,
        )
        
        # 2. 儲存
        await self.repository.save(pir)
        
        # 3. 發布領域事件（如果需要）
        events = pir.get_domain_events()
        if events:
            logger.info("PIR 建立事件", extra={"pir_id": pir.id, "event_count": len(events)})
        
        logger.info("PIR 建立成功", extra={"pir_id": pir.id})
        
        return pir.id
    
    async def update_pir(
        self,
        pir_id: str,
        request: UpdatePIRRequest,
        user_id: str = "system",
    ) -> None:
        """
        更新 PIR
        
        Args:
            pir_id: PIR ID
            request: 更新 PIR 請求
            user_id: 使用者 ID（預設 "system"）
        
        Raises:
            ValueError: 當 PIR 不存在或輸入參數無效時
        """
        logger.info("更新 PIR", extra={"pir_id": pir_id, "user_id": user_id})
        
        # 1. 取得 PIR
        pir = await self.repository.get_by_id(pir_id)
        if not pir:
            raise ValueError(f"PIR ID {pir_id} 不存在")
        
        # 2. 更新 PIR
        update_kwargs = {}
        if request.name is not None:
            update_kwargs["name"] = request.name
        if request.description is not None:
            update_kwargs["description"] = request.description
        if request.priority is not None:
            update_kwargs["priority"] = request.priority
        if request.condition_type is not None:
            update_kwargs["condition_type"] = request.condition_type
        if request.condition_value is not None:
            update_kwargs["condition_value"] = request.condition_value
        
        pir.update(updated_by=user_id, **update_kwargs)
        
        # 3. 儲存
        await self.repository.save(pir)
        
        # 4. 發布領域事件（如果需要）
        events = pir.get_domain_events()
        if events:
            logger.info("PIR 更新事件", extra={"pir_id": pir.id, "event_count": len(events)})
        
        logger.info("PIR 更新成功", extra={"pir_id": pir.id})
    
    async def delete_pir(
        self,
        pir_id: str,
        user_id: str = "system",
    ) -> None:
        """
        刪除 PIR
        
        Args:
            pir_id: PIR ID
            user_id: 使用者 ID（預設 "system"）
        
        Raises:
            ValueError: 當 PIR 不存在時
        """
        logger.info("刪除 PIR", extra={"pir_id": pir_id, "user_id": user_id})
        
        # 檢查 PIR 是否存在
        pir = await self.repository.get_by_id(pir_id)
        if not pir:
            raise ValueError(f"PIR ID {pir_id} 不存在")
        
        # 刪除 PIR
        await self.repository.delete(pir_id)
        
        logger.info("PIR 刪除成功", extra={"pir_id": pir_id})
    
    async def toggle_pir(
        self,
        pir_id: str,
        user_id: str = "system",
    ) -> None:
        """
        切換 PIR 啟用狀態
        
        Args:
            pir_id: PIR ID
            user_id: 使用者 ID（預設 "system"）
        
        Raises:
            ValueError: 當 PIR 不存在時
        """
        logger.info("切換 PIR 啟用狀態", extra={"pir_id": pir_id, "user_id": user_id})
        
        # 1. 取得 PIR
        pir = await self.repository.get_by_id(pir_id)
        if not pir:
            raise ValueError(f"PIR ID {pir_id} 不存在")
        
        # 2. 切換啟用狀態
        pir.toggle(updated_by=user_id)
        
        # 3. 儲存
        await self.repository.save(pir)
        
        # 4. 發布領域事件（如果需要）
        events = pir.get_domain_events()
        if events:
            logger.info("PIR 切換事件", extra={"pir_id": pir.id, "is_enabled": pir.is_enabled})
        
        logger.info("PIR 切換成功", extra={"pir_id": pir.id, "is_enabled": pir.is_enabled})
    
    async def get_pirs(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> PIRListResponse:
        """
        查詢 PIR 清單（支援分頁、排序）
        
        Args:
            page: 頁碼（從 1 開始）
            page_size: 每頁筆數（預設 20）
            sort_by: 排序欄位
            sort_order: 排序方向（asc/desc）
        
        Returns:
            PIRListResponse: PIR 清單回應
        """
        pirs, total_count = await self.repository.get_all(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        
        # 計算總頁數
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
        
        # 轉換為回應格式
        pir_responses = [self._to_response(pir) for pir in pirs]
        
        return PIRListResponse(
            data=pir_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    
    async def get_pir_by_id(self, pir_id: str) -> Optional[PIRResponse]:
        """
        查詢 PIR 詳情
        
        Args:
            pir_id: PIR ID
        
        Returns:
            PIRResponse: PIR 回應，如果不存在則返回 None
        """
        pir = await self.repository.get_by_id(pir_id)
        
        if not pir:
            return None
        
        return self._to_response(pir)
    
    async def get_enabled_pirs(self) -> List[PIRResponse]:
        """
        查詢啟用的 PIR
        
        Returns:
            List[PIRResponse]: 啟用的 PIR 清單
        """
        pirs = await self.repository.get_enabled_pirs()
        
        return [self._to_response(pir) for pir in pirs]
    
    async def find_matching_pirs(self, threat_data: dict) -> List[PIRResponse]:
        """
        查詢符合威脅資料的 PIR
        
        業務規則：只有啟用的 PIR 才會被用於威脅分析（AC-005-2）
        
        Args:
            threat_data: 威脅資料字典（包含 cve、product_name、threat_type 等）
        
        Returns:
            List[PIRResponse]: 符合條件的 PIR 清單（僅包含啟用的 PIR）
        """
        pirs = await self.repository.find_matching_pirs(threat_data)
        
        return [self._to_response(pir) for pir in pirs]
    
    def _to_response(self, pir: PIR) -> PIRResponse:
        """
        將領域模型轉換為回應格式
        
        Args:
            pir: PIR 聚合根
        
        Returns:
            PIRResponse: PIR 回應
        """
        return PIRResponse(
            id=pir.id,
            name=pir.name,
            description=pir.description,
            priority=pir.priority.value,
            condition_type=pir.condition_type,
            condition_value=pir.condition_value,
            is_enabled=pir.is_enabled,
            created_at=pir.created_at,
            updated_at=pir.updated_at,
            created_by=pir.created_by,
            updated_by=pir.updated_by,
        )

