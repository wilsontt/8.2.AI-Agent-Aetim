"""
資料庫連線設定

實作資料庫連線與初始化，支援 SQLite（開發）與 MS SQL Server（生產）。
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from typing import AsyncGenerator

# 確保資料目錄存在
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data"
)
os.makedirs(DATA_DIR, exist_ok=True)

# 資料庫 URL（從環境變數讀取）
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{os.path.join(DATA_DIR, 'aetim.db')}",
)

# 建立非同步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 開發時可設為 True 以查看 SQL
    future=True,
)

# 建立 Session 工廠
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 建立 Base 類別（所有模型繼承此類別）
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    取得資料庫 Session（依賴注入用）
    
    Yields:
        AsyncSession: 資料庫 Session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    初始化資料庫
    
    建立所有資料表（如果不存在）。
    """
    # 匯入所有模型以確保它們被註冊到 Base.metadata
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
    )
    from system_management.infrastructure.persistence.models import AuditLog

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
