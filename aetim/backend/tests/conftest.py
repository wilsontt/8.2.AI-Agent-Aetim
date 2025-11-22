"""
Pytest 配置與共用 Fixtures

本模組提供所有測試共用的 fixtures 與配置。
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool
from shared_kernel.infrastructure.redis import init_redis, close_redis
from shared_kernel.infrastructure.database import Base
import os

# 測試用資料庫 URL（使用記憶體資料庫）
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///:memory:"
)

# 測試用引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False} if "memory" in TEST_DATABASE_URL else {},
    poolclass=StaticPool if "memory" in TEST_DATABASE_URL else None,
    echo=False,
    future=True,
)

# 測試用 Session 工廠
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """建立事件循環"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session():
    """提供測試用的資料庫 Session"""
    # 建立所有資料表
    async with test_engine.begin() as conn:
        # 匯入所有模型
        from asset_management.infrastructure.persistence.models import (
            Asset,
            AssetProduct,
        )
        from threat_intelligence.infrastructure.persistence.models import (
            ThreatFeed,
            Threat,
        )
        from analysis_assessment.infrastructure.persistence.models import (
            PIR,
            ThreatAssetAssociation,
            RiskAssessment,
        )
        from reporting_notification.infrastructure.persistence.models import (
            Report,
            NotificationRule,
            Notification,
        )
        from system_management.infrastructure.persistence.models import (
            User,
            Role,
            Permission,
            UserRole,
            RolePermission,
            SystemConfiguration,
            Schedule,
            AuditLog,
        )
        
        await conn.run_sync(Base.metadata.create_all)
    
    # 建立 Session
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    # 清理資料表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def redis_client():
    """提供測試用的 Redis 客戶端"""
    await init_redis()
    yield
    await close_redis()


@pytest.fixture(scope="function")
async def test_client():
    """提供測試用的 FastAPI 測試客戶端"""
    from fastapi.testclient import TestClient
    from main import app
    
    with TestClient(app) as client:
        yield client


# 測試資料 Fixtures（使用 Factory Pattern）
from tests.factories import (
    AssetFactory,
    AssetProductFactory,
    ThreatFeedFactory,
    ThreatFactory,
    PIRFactory,
    UserFactory,
    RoleFactory,
    PermissionFactory,
)


@pytest.fixture
def sample_asset():
    """建立範例資產"""
    return AssetFactory.create()


@pytest.fixture
def sample_assets():
    """建立多個範例資產"""
    return AssetFactory.create_batch(10)


@pytest.fixture
def sample_threat_feed():
    """建立範例威脅來源"""
    return ThreatFeedFactory.create()


@pytest.fixture
def sample_threat(sample_threat_feed):
    """建立範例威脅"""
    return ThreatFactory.create(threat_feed_id=sample_threat_feed.id)


@pytest.fixture
def sample_pir():
    """建立範例 PIR"""
    return PIRFactory.create()


@pytest.fixture
def sample_user():
    """建立範例使用者"""
    return UserFactory.create()


@pytest.fixture
def sample_role():
    """建立範例角色"""
    return RoleFactory.create()
