"""
稽核日誌 Repository 實作

使用 SQLAlchemy 實作 AuditLog 的持久化操作。
"""

from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.interfaces.audit_log_repository import IAuditLogRepository
from ...domain.entities.audit_log import AuditLog
from .models import AuditLog as AuditLogModel
from .audit_log_mapper import AuditLogMapper


class AuditLogRepository(IAuditLogRepository):
    """稽核日誌 Repository 實作"""
    
    def __init__(self, session: AsyncSession):
        """
        初始化 Repository
        
        Args:
            session: 資料庫 Session
        """
        self.session = session
    
    async def save(self, audit_log: AuditLog) -> None:
        """
        儲存稽核日誌（僅新增，不可修改）
        
        業務規則：稽核日誌不可篡改（寫入後不可修改）
        
        Args:
            audit_log: 稽核日誌實體
        """
        # 檢查稽核日誌是否存在（理論上不應該存在，因為每次都是新建）
        result = await self.session.execute(
            select(AuditLogModel).where(AuditLogModel.id == audit_log.id)
        )
        existing_log = result.scalar_one_or_none()
        
        if existing_log:
            # 如果已存在，不允許修改（業務規則：稽核日誌不可篡改）
            raise ValueError("稽核日誌不可修改")
        
        # 新增稽核日誌
        audit_log_model = AuditLogMapper.to_model(audit_log)
        self.session.add(audit_log_model)
        await self.session.commit()
    
    async def get_by_id(self, audit_log_id: str) -> Optional[AuditLog]:
        """
        依 ID 查詢稽核日誌
        
        Args:
            audit_log_id: 稽核日誌 ID
        
        Returns:
            AuditLog: 稽核日誌實體，如果不存在則返回 None
        """
        result = await self.session.execute(
            select(AuditLogModel).where(AuditLogModel.id == audit_log_id)
        )
        audit_log_model = result.scalar_one_or_none()
        
        if not audit_log_model:
            return None
        
        return AuditLogMapper.to_domain(audit_log_model)
    
    async def get_by_filters(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> Tuple[List[AuditLog], int]:
        """
        依條件查詢稽核日誌（支援多種篩選條件和分頁）
        
        Args:
            user_id: 使用者 ID（可選）
            action: 操作類型（可選）
            resource_type: 資源類型（可選）
            resource_id: 資源 ID（可選）
            start_date: 開始日期（可選）
            end_date: 結束日期（可選）
            page: 頁碼（從 1 開始）
            page_size: 每頁筆數（預設 20）
            sort_by: 排序欄位（created_at 等）
            sort_order: 排序方向（asc、desc）
        
        Returns:
            Tuple[List[AuditLog], int]: (稽核日誌清單, 總筆數)
        """
        # 建立查詢
        query = select(AuditLogModel)
        conditions = []
        
        # 篩選條件
        if user_id:
            conditions.append(AuditLogModel.user_id == user_id)
        
        if action:
            conditions.append(AuditLogModel.action == action.upper())
        
        if resource_type:
            conditions.append(AuditLogModel.resource_type == resource_type)
        
        if resource_id:
            conditions.append(AuditLogModel.resource_id == resource_id)
        
        if start_date:
            conditions.append(AuditLogModel.created_at >= start_date)
        
        if end_date:
            conditions.append(AuditLogModel.created_at <= end_date)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 排序
        if sort_by:
            sort_column = self._get_sort_column(sort_by)
            if sort_order.lower() == "asc":
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())
        else:
            # 預設排序：依建立時間降序（最新的在前）
            query = query.order_by(AuditLogModel.created_at.desc())
        
        # 計算總筆數
        count_query = select(func.count(AuditLogModel.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar()
        
        # 分頁
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # 執行查詢
        result = await self.session.execute(query)
        audit_log_models = result.scalars().all()
        
        # 轉換為領域模型
        audit_logs = [AuditLogMapper.to_domain(model) for model in audit_log_models]
        
        return audit_logs, total_count
    
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
            "created_at": AuditLogModel.created_at,
            "action": AuditLogModel.action,
            "resource_type": AuditLogModel.resource_type,
        }
        
        if sort_by not in sort_mapping:
            raise ValueError(f"無效的排序欄位：{sort_by}")
        
        return sort_mapping[sort_by]

