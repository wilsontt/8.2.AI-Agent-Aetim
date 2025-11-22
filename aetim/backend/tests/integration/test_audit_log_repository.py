"""
稽核日誌 Repository 整合測試

測試 AuditLogRepository 與資料庫的互動。
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from system_management.domain.entities.audit_log import AuditLog
from system_management.infrastructure.persistence.audit_log_repository import AuditLogRepository
from system_management.infrastructure.persistence.models import AuditLog as AuditLogModel
from shared_kernel.infrastructure.database import Base

# 使用記憶體 SQLite 資料庫進行測試
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_session():
    """建立測試資料庫 Session"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # 建立所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def audit_log_repository(db_session):
    """建立 AuditLogRepository 實例"""
    return AuditLogRepository(db_session)


@pytest.mark.asyncio
class TestAuditLogRepository:
    """稽核日誌 Repository 測試"""
    
    async def test_save_audit_log(self, audit_log_repository):
        """測試儲存稽核日誌"""
        audit_log = AuditLog.create(
            user_id="user-123",
            action="CREATE",
            resource_type="Asset",
            resource_id="asset-456",
            details={"field": "value"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        
        await audit_log_repository.save(audit_log)
        
        # 驗證已儲存
        saved_log = await audit_log_repository.get_by_id(audit_log.id)
        assert saved_log is not None
        assert saved_log.id == audit_log.id
        assert saved_log.user_id == "user-123"
        assert saved_log.action == "CREATE"
        assert saved_log.resource_type == "Asset"
        assert saved_log.resource_id == "asset-456"
        assert saved_log.details == {"field": "value"}
        assert saved_log.ip_address == "192.168.1.1"
        assert saved_log.user_agent == "Mozilla/5.0"
    
    async def test_save_audit_log_immutable(self, audit_log_repository):
        """測試稽核日誌不可修改（業務規則）"""
        audit_log = AuditLog.create(
            user_id="user-123",
            action="CREATE",
            resource_type="Asset",
        )
        
        await audit_log_repository.save(audit_log)
        
        # 嘗試再次儲存（應該失敗）
        with pytest.raises(ValueError, match="稽核日誌不可修改"):
            await audit_log_repository.save(audit_log)
    
    async def test_get_by_id_exists(self, audit_log_repository):
        """測試依 ID 查詢稽核日誌（存在）"""
        audit_log = AuditLog.create(
            user_id="user-123",
            action="CREATE",
            resource_type="Asset",
        )
        
        await audit_log_repository.save(audit_log)
        
        found_log = await audit_log_repository.get_by_id(audit_log.id)
        
        assert found_log is not None
        assert found_log.id == audit_log.id
        assert found_log.action == "CREATE"
    
    async def test_get_by_id_not_exists(self, audit_log_repository):
        """測試依 ID 查詢稽核日誌（不存在）"""
        found_log = await audit_log_repository.get_by_id("non-existent-id")
        
        assert found_log is None
    
    async def test_get_by_filters_all(self, audit_log_repository):
        """測試查詢所有稽核日誌"""
        # 建立多筆稽核日誌
        for i in range(5):
            audit_log = AuditLog.create(
                user_id=f"user-{i}",
                action="CREATE",
                resource_type="Asset",
                resource_id=f"asset-{i}",
            )
            await audit_log_repository.save(audit_log)
        
        logs, total_count = await audit_log_repository.get_by_filters()
        
        assert total_count == 5
        assert len(logs) == 5
    
    async def test_get_by_filters_by_user_id(self, audit_log_repository):
        """測試依使用者 ID 篩選"""
        # 建立多筆稽核日誌
        for i in range(3):
            audit_log = AuditLog.create(
                user_id="user-123",
                action="CREATE",
                resource_type="Asset",
            )
            await audit_log_repository.save(audit_log)
        
        for i in range(2):
            audit_log = AuditLog.create(
                user_id="user-456",
                action="UPDATE",
                resource_type="Asset",
            )
            await audit_log_repository.save(audit_log)
        
        logs, total_count = await audit_log_repository.get_by_filters(user_id="user-123")
        
        assert total_count == 3
        assert len(logs) == 3
        assert all(log.user_id == "user-123" for log in logs)
    
    async def test_get_by_filters_by_action(self, audit_log_repository):
        """測試依操作類型篩選"""
        # 建立多筆稽核日誌
        for i in range(3):
            audit_log = AuditLog.create(
                user_id="user-123",
                action="CREATE",
                resource_type="Asset",
            )
            await audit_log_repository.save(audit_log)
        
        for i in range(2):
            audit_log = AuditLog.create(
                user_id="user-123",
                action="UPDATE",
                resource_type="Asset",
            )
            await audit_log_repository.save(audit_log)
        
        logs, total_count = await audit_log_repository.get_by_filters(action="CREATE")
        
        assert total_count == 3
        assert len(logs) == 3
        assert all(log.action == "CREATE" for log in logs)
    
    async def test_get_by_filters_by_resource_type(self, audit_log_repository):
        """測試依資源類型篩選"""
        # 建立多筆稽核日誌
        for i in range(3):
            audit_log = AuditLog.create(
                user_id="user-123",
                action="CREATE",
                resource_type="Asset",
            )
            await audit_log_repository.save(audit_log)
        
        for i in range(2):
            audit_log = AuditLog.create(
                user_id="user-123",
                action="CREATE",
                resource_type="PIR",
            )
            await audit_log_repository.save(audit_log)
        
        logs, total_count = await audit_log_repository.get_by_filters(resource_type="Asset")
        
        assert total_count == 3
        assert len(logs) == 3
        assert all(log.resource_type == "Asset" for log in logs)
    
    async def test_get_by_filters_by_date_range(self, audit_log_repository):
        """測試依日期範圍篩選"""
        now = datetime.utcnow()
        
        # 建立不同時間的稽核日誌
        for i in range(3):
            audit_log = AuditLog.create(
                user_id="user-123",
                action="CREATE",
                resource_type="Asset",
            )
            # 手動設定時間（測試用）
            audit_log.created_at = now - timedelta(days=i)
            await audit_log_repository.save(audit_log)
        
        start_date = now - timedelta(days=2)
        end_date = now
        
        logs, total_count = await audit_log_repository.get_by_filters(
            start_date=start_date,
            end_date=end_date,
        )
        
        assert total_count >= 2
        assert all(start_date <= log.created_at <= end_date for log in logs)
    
    async def test_get_by_filters_pagination(self, audit_log_repository):
        """測試分頁"""
        # 建立 10 筆稽核日誌
        for i in range(10):
            audit_log = AuditLog.create(
                user_id="user-123",
                action="CREATE",
                resource_type="Asset",
            )
            await audit_log_repository.save(audit_log)
        
        # 第一頁
        logs_page1, total_count = await audit_log_repository.get_by_filters(
            page=1,
            page_size=3,
        )
        
        assert total_count == 10
        assert len(logs_page1) == 3
        
        # 第二頁
        logs_page2, total_count = await audit_log_repository.get_by_filters(
            page=2,
            page_size=3,
        )
        
        assert total_count == 10
        assert len(logs_page2) == 3
        
        # 驗證不同頁的資料不同
        assert logs_page1[0].id != logs_page2[0].id
    
    async def test_get_by_filters_sorting(self, audit_log_repository):
        """測試排序"""
        # 建立多筆稽核日誌（不同時間）
        for i in range(5):
            audit_log = AuditLog.create(
                user_id="user-123",
                action="CREATE",
                resource_type="Asset",
            )
            # 手動設定時間（測試用）
            audit_log.created_at = datetime.utcnow() - timedelta(hours=i)
            await audit_log_repository.save(audit_log)
        
        # 依建立時間升序排序
        logs_asc, _ = await audit_log_repository.get_by_filters(
            sort_by="created_at",
            sort_order="asc",
        )
        
        # 驗證排序正確（最舊的在前）
        for i in range(len(logs_asc) - 1):
            assert logs_asc[i].created_at <= logs_asc[i + 1].created_at
        
        # 依建立時間降序排序（預設）
        logs_desc, _ = await audit_log_repository.get_by_filters(
            sort_by="created_at",
            sort_order="desc",
        )
        
        # 驗證排序正確（最新的在前）
        for i in range(len(logs_desc) - 1):
            assert logs_desc[i].created_at >= logs_desc[i + 1].created_at
    
    async def test_get_by_filters_invalid_sort_by(self, audit_log_repository):
        """測試無效的排序欄位"""
        with pytest.raises(ValueError, match="無效的排序欄位"):
            await audit_log_repository.get_by_filters(
                sort_by="invalid_field",
            )

