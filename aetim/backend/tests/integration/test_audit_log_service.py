"""
稽核日誌服務整合測試

測試 AuditLogService 的完整功能。
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from system_management.application.services.audit_log_service import AuditLogService
from system_management.application.dtos.audit_log_dto import AuditLogFilterRequest
from system_management.domain.entities.audit_log import AuditLog
from system_management.infrastructure.persistence.audit_log_repository import AuditLogRepository
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
def audit_log_service(db_session):
    """建立 AuditLogService 實例"""
    repository = AuditLogRepository(db_session)
    return AuditLogService(repository)


@pytest.mark.asyncio
class TestAuditLogService:
    """稽核日誌服務測試"""
    
    async def test_log_action_success(self, audit_log_service):
        """測試成功記錄操作"""
        audit_log_id = await audit_log_service.log_action(
            user_id="user-123",
            action="CREATE",
            resource_type="Asset",
            resource_id="asset-456",
            details={"field": "value"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
        )
        
        assert audit_log_id is not None
        
        # 驗證已記錄
        audit_log = await audit_log_service.get_audit_log_by_id(audit_log_id)
        assert audit_log is not None
        assert audit_log.user_id == "user-123"
        assert audit_log.action == "CREATE"
        assert audit_log.resource_type == "Asset"
        assert audit_log.resource_id == "asset-456"
        assert audit_log.details == {"field": "value"}
        assert audit_log.ip_address == "192.168.1.1"
        assert audit_log.user_agent == "Mozilla/5.0"
    
    async def test_log_action_without_optional_fields(self, audit_log_service):
        """測試記錄操作（不包含可選欄位）"""
        audit_log_id = await audit_log_service.log_action(
            user_id=None,
            action="VIEW",
            resource_type="Asset",
        )
        
        assert audit_log_id is not None
        
        audit_log = await audit_log_service.get_audit_log_by_id(audit_log_id)
        assert audit_log.user_id is None
        assert audit_log.action == "VIEW"
        assert audit_log.resource_id is None
        assert audit_log.details is None
    
    async def test_log_action_invalid_action(self, audit_log_service):
        """測試記錄操作（無效的操作類型）"""
        with pytest.raises(ValueError):
            await audit_log_service.log_action(
                user_id="user-123",
                action="INVALID",
                resource_type="Asset",
            )
    
    async def test_get_audit_logs_all(self, audit_log_service):
        """測試查詢所有稽核日誌"""
        # 建立多筆稽核日誌
        for i in range(5):
            await audit_log_service.log_action(
                user_id="user-123",
                action="CREATE",
                resource_type="Asset",
                resource_id=f"asset-{i}",
            )
        
        request = AuditLogFilterRequest(page=1, page_size=20)
        response = await audit_log_service.get_audit_logs(request)
        
        assert response.total_count == 5
        assert len(response.data) == 5
        assert response.page == 1
        assert response.page_size == 20
        assert response.total_pages == 1
    
    async def test_get_audit_logs_by_user_id(self, audit_log_service):
        """測試依使用者 ID 查詢"""
        # 建立多筆稽核日誌
        for i in range(3):
            await audit_log_service.log_action(
                user_id="user-123",
                action="CREATE",
                resource_type="Asset",
            )
        
        for i in range(2):
            await audit_log_service.log_action(
                user_id="user-456",
                action="UPDATE",
                resource_type="Asset",
            )
        
        request = AuditLogFilterRequest(user_id="user-123", page=1, page_size=20)
        response = await audit_log_service.get_audit_logs(request)
        
        assert response.total_count == 3
        assert len(response.data) == 3
        assert all(log.user_id == "user-123" for log in response.data)
    
    async def test_get_audit_logs_by_action(self, audit_log_service):
        """測試依操作類型查詢"""
        # 建立多筆稽核日誌
        for i in range(3):
            await audit_log_service.log_action(
                user_id="user-123",
                action="CREATE",
                resource_type="Asset",
            )
        
        for i in range(2):
            await audit_log_service.log_action(
                user_id="user-123",
                action="UPDATE",
                resource_type="Asset",
            )
        
        request = AuditLogFilterRequest(action="CREATE", page=1, page_size=20)
        response = await audit_log_service.get_audit_logs(request)
        
        assert response.total_count == 3
        assert len(response.data) == 3
        assert all(log.action == "CREATE" for log in response.data)
    
    async def test_get_audit_logs_pagination(self, audit_log_service):
        """測試分頁"""
        # 建立 10 筆稽核日誌
        for i in range(10):
            await audit_log_service.log_action(
                user_id="user-123",
                action="CREATE",
                resource_type="Asset",
            )
        
        # 第一頁
        request_page1 = AuditLogFilterRequest(page=1, page_size=3)
        response_page1 = await audit_log_service.get_audit_logs(request_page1)
        
        assert response_page1.total_count == 10
        assert len(response_page1.data) == 3
        assert response_page1.page == 1
        assert response_page1.total_pages == 4
        
        # 第二頁
        request_page2 = AuditLogFilterRequest(page=2, page_size=3)
        response_page2 = await audit_log_service.get_audit_logs(request_page2)
        
        assert response_page2.total_count == 10
        assert len(response_page2.data) == 3
        assert response_page2.page == 2
    
    async def test_get_audit_log_by_id_exists(self, audit_log_service):
        """測試查詢稽核日誌詳情（存在）"""
        audit_log_id = await audit_log_service.log_action(
            user_id="user-123",
            action="CREATE",
            resource_type="Asset",
        )
        
        audit_log = await audit_log_service.get_audit_log_by_id(audit_log_id)
        
        assert audit_log is not None
        assert audit_log.id == audit_log_id
        assert audit_log.action == "CREATE"
    
    async def test_get_audit_log_by_id_not_exists(self, audit_log_service):
        """測試查詢稽核日誌詳情（不存在）"""
        audit_log = await audit_log_service.get_audit_log_by_id("non-existent-id")
        
        assert audit_log is None

