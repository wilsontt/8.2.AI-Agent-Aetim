"""
AETIM 後端應用程式主程式

本模組為 FastAPI 應用程式的入口點，負責：
- 初始化 FastAPI 應用程式
- 設定路由與中介軟體
- 啟動應用程式伺服器
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from shared_kernel.infrastructure.logging import setup_logging, get_logger
from shared_kernel.infrastructure.tracing import TracingMiddleware
from api.controllers import health, assets, threats, reports, metrics, pirs, threat_feeds, audit_logs, auth, system_configuration
from shared_kernel.infrastructure.database import init_db
from shared_kernel.infrastructure.redis import init_redis, close_redis
import os

# 從環境變數讀取日誌級別
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENABLE_FILE_LOGGING = os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true"

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時初始化
    setup_logging(LOG_LEVEL, enable_file_logging=ENABLE_FILE_LOGGING)
    logger.info("Application starting", extra={"log_level": LOG_LEVEL})
    
    await init_redis()
    await init_db()
    
    logger.info("Application started successfully")
    
    yield
    
    # 關閉時清理
    logger.info("Application shutting down")
    await close_redis()
    logger.info("Application stopped")


# 建立 FastAPI 應用程式
app = FastAPI(
    title="AETIM API",
    description="AI 驅動之自動化威脅情資管理系統 API",
    version="1.0.0",
    lifespan=lifespan,
)

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 設定追蹤中介軟體（必須在其他中介軟體之前）
app.add_middleware(TracingMiddleware)

# 設定身份驗證中介軟體（必須在路由之前）
from system_management.infrastructure.middleware.authentication import AuthenticationMiddleware
app.add_middleware(AuthenticationMiddleware)

# 註冊路由
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(metrics.router, prefix="/api/v1", tags=["Metrics"])
app.include_router(auth.router, tags=["身份驗證"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["Assets"])
app.include_router(pirs.router, prefix="/api/v1/pirs", tags=["PIRs"])
app.include_router(threat_feeds.router, prefix="/api/v1/threat-feeds", tags=["Threat Feeds"])
app.include_router(audit_logs.router, prefix="/api/v1/audit-logs", tags=["Audit Logs"])
app.include_router(threats.router, prefix="/api/v1/threats", tags=["Threats"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(system_configuration.router, tags=["系統設定"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

