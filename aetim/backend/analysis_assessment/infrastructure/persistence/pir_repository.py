"""
PIR Repository 實作

使用 SQLAlchemy 實作 PIR 的持久化操作。
"""

from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.interfaces.pir_repository import IPIRRepository
from ...domain.aggregates.pir import PIR
from .models import PIR as PIRModel
from .pir_mapper import PIRMapper


class PIRRepository(IPIRRepository):
    """PIR Repository 實作"""
    
    def __init__(self, session: AsyncSession):
        """
        初始化 Repository
        
        Args:
            session: 資料庫 Session
        """
        self.session = session
    
    async def save(self, pir: PIR) -> None:
        """
        儲存 PIR（新增或更新）
        
        Args:
            pir: PIR 聚合根
        """
        # 檢查 PIR 是否存在
        result = await self.session.execute(
            select(PIRModel).where(PIRModel.id == pir.id)
        )
        existing_pir = result.scalar_one_or_none()
        
        if existing_pir:
            # 更新現有 PIR
            PIRMapper.update_model(existing_pir, pir)
            self.session.add(existing_pir)
        else:
            # 新增 PIR
            pir_model = PIRMapper.to_model(pir)
            self.session.add(pir_model)
        
        await self.session.commit()
    
    async def get_by_id(self, pir_id: str) -> Optional[PIR]:
        """
        依 ID 查詢 PIR
        
        Args:
            pir_id: PIR ID
        
        Returns:
            PIR: PIR 聚合根，如果不存在則返回 None
        """
        result = await self.session.execute(
            select(PIRModel).where(PIRModel.id == pir_id)
        )
        pir_model = result.scalar_one_or_none()
        
        if not pir_model:
            return None
        
        return PIRMapper.to_domain(pir_model)
    
    async def delete(self, pir_id: str) -> None:
        """
        刪除 PIR
        
        Args:
            pir_id: PIR ID
        
        Raises:
            ValueError: 當 PIR 不存在時
        """
        result = await self.session.execute(
            select(PIRModel).where(PIRModel.id == pir_id)
        )
        pir_model = result.scalar_one_or_none()
        
        if not pir_model:
            raise ValueError(f"PIR ID {pir_id} 不存在")
        
        await self.session.delete(pir_model)
        await self.session.commit()
    
    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> Tuple[List[PIR], int]:
        """
        查詢所有 PIR（支援分頁與排序）
        
        Args:
            page: 頁碼（從 1 開始）
            page_size: 每頁筆數（預設 20）
            sort_by: 排序欄位（name、priority、created_at 等）
            sort_order: 排序方向（asc、desc）
        
        Returns:
            Tuple[List[PIR], int]: (PIR 清單, 總筆數)
        """
        # 建立查詢
        query = select(PIRModel)
        
        # 排序
        if sort_by:
            sort_column = self._get_sort_column(sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            # 預設排序：依建立時間降序
            query = query.order_by(PIRModel.created_at.desc())
        
        # 計算總筆數
        count_query = select(func.count(PIRModel.id))
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar()
        
        # 分頁
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # 執行查詢
        result = await self.session.execute(query)
        pir_models = result.scalars().all()
        
        # 轉換為領域模型
        pirs = [PIRMapper.to_domain(model) for model in pir_models]
        
        return pirs, total_count
    
    async def get_enabled_pirs(self) -> List[PIR]:
        """
        查詢啟用的 PIR
        
        Returns:
            List[PIR]: 啟用的 PIR 清單
        """
        result = await self.session.execute(
            select(PIRModel).where(PIRModel.is_enabled == True)
        )
        pir_models = result.scalars().all()
        
        # 轉換為領域模型
        pirs = [PIRMapper.to_domain(model) for model in pir_models]
        
        return pirs
    
    async def find_matching_pirs(self, threat_data: dict) -> List[PIR]:
        """
        查詢符合威脅資料的 PIR
        
        業務規則：只有啟用的 PIR 才會被用於威脅分析（AC-005-2）
        
        Args:
            threat_data: 威脅資料字典（包含 cve、product_name、threat_type 等）
        
        Returns:
            List[PIR]: 符合條件的 PIR 清單（僅包含啟用的 PIR）
        """
        # 取得所有啟用的 PIR
        enabled_pirs = await self.get_enabled_pirs()
        
        # 過濾符合條件的 PIR
        matching_pirs = [pir for pir in enabled_pirs if pir.matches_condition(threat_data)]
        
        return matching_pirs
    
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
            "name": PIRModel.name,
            "priority": PIRModel.priority,
            "created_at": PIRModel.created_at,
            "updated_at": PIRModel.updated_at,
            "is_enabled": PIRModel.is_enabled,
        }
        
        if sort_by not in sort_mapping:
            raise ValueError(f"無效的排序欄位：{sort_by}")
        
        return sort_mapping[sort_by]

