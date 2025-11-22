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

from shared_kernel.infrastructure.logging import setup_logging
from api.controllers import health, assets, threats, reports
from shared_kernel.infrastructure.database import init_db
from shared_kernel.infrastructure.redis import init_redis, close_redis
import os

# 從環境變數讀取日誌級別
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時初始化
    setup_logging(LOG_LEVEL)
    await init_redis()
    await init_db()
    yield
    # 關閉時清理
    await close_redis()


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

# 註冊路由
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["Assets"])
app.include_router(threats.router, prefix="/api/v1/threats", tags=["Threats"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

