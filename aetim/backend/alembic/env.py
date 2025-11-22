"""
Alembic 環境配置

用於資料庫遷移的環境設定，支援非同步 SQLAlchemy。
"""

from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
import asyncio
import os
import sys
from pathlib import Path

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alembic import context
from shared_kernel.infrastructure.database import Base, DATABASE_URL

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
    AuditLog,
)

# Alembic Config 物件
config = context.config

# 設定資料庫 URL（從環境變數或預設值）
if config.get_main_option("sqlalchemy.url") is None or config.get_main_option("sqlalchemy.url") == "":
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

# 設定日誌
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目標元資料
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    執行離線遷移（生成 SQL 腳本）
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    執行遷移
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    執行線上遷移（連接到資料庫）
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = DATABASE_URL
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

