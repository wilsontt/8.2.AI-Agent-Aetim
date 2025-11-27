"""
端對端測試共用設定檔

提供端對端測試共用的 fixtures 和設定。
符合 T-5-4-1：端對端測試所有功能
"""

import pytest
import sys
import os
from typing import AsyncGenerator

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from shared_kernel.infrastructure.database import Base


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    建立測試用的資料庫會話
    
    Yields:
        AsyncSession: 資料庫會話
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_user_id() -> str:
    """
    測試使用者 ID
    
    Returns:
        str: 測試使用者 ID
    """
    return "test-user-123"


@pytest.fixture(scope="function")
async def test_ip_address() -> str:
    """
    測試 IP 位址
    
    Returns:
        str: 測試 IP 位址
    """
    return "127.0.0.1"


@pytest.fixture(scope="function")
async def test_user_agent() -> str:
    """
    測試 User Agent
    
    Returns:
        str: 測試 User Agent
    """
    return "Mozilla/5.0 (Test Browser)"

