"""
pytest 配置與共用 fixtures

本模組提供所有測試共用的 fixtures 與配置。
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from shared_kernel.infrastructure.redis import init_redis, close_redis
import os

# 測試用資料庫 URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///./data/test.db"
)

# 測試用 Base
TestBase = declarative_base()

# 測試用引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
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
    async with test_engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
    
    async with test_engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.drop_all)


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

