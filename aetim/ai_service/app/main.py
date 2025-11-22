"""
AETIM AI/ML 服務主程式

本模組為 FastAPI 應用程式的入口點，負責：
- 初始化 FastAPI 應用程式
- 設定路由與中介軟體
- 啟動應用程式伺服器
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.models.request import ExtractRequest, SummarizeRequest
from app.models.response import ExtractResponse, SummarizeResponse

# 從環境變數讀取配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時初始化
    print(f"AI Service starting (Environment: {ENVIRONMENT}, Log Level: {LOG_LEVEL})")
    
    # TODO: 載入 ML 模型（spaCy、transformers 等）
    # 這裡可以在啟動時預載入模型以提高效能
    
    yield
    
    # 關閉時清理
    print("AI Service shutting down")


# 建立 FastAPI 應用程式
app = FastAPI(
    title="AETIM AI Service",
    description="AI/ML 服務 API - 提供威脅資訊提取、摘要生成等功能",
    version="1.0.0",
    lifespan=lifespan,
)

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境應限制來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    健康檢查端點
    
    Returns:
        dict: 服務健康狀態
    """
    return {
        "status": "healthy",
        "service": "ai-service",
        "version": "1.0.0",
    }


@app.get("/api/v1/health")
async def health_check_v1():
    """
    健康檢查端點（API v1）
    
    Returns:
        dict: 服務健康狀態
    """
    return await health_check()


@app.post("/api/v1/ai/extract", response_model=ExtractResponse)
async def extract_threat_info(request: ExtractRequest):
    """
    提取威脅資訊
    
    從文字內容中提取 CVE 編號、產品名稱、TTPs、IOCs 等威脅資訊。
    
    Args:
        request: 提取請求（包含文字內容）
    
    Returns:
        ExtractResponse: 提取結果（包含 CVE、產品、TTPs、IOCs、信心分數）
    """
    # TODO: 實作威脅資訊提取（T-2-1-5）
    return ExtractResponse(
        cve=[],
        products=[],
        ttps=[],
        iocs=[],
        confidence=0.0,
    )


@app.post("/api/v1/ai/summarize", response_model=SummarizeResponse)
async def summarize_threat(request: SummarizeRequest):
    """
    生成威脅摘要
    
    將威脅情資文字轉換為簡潔的摘要。
    
    Args:
        request: 摘要請求（包含文字內容、目標長度、語言、風格）
    
    Returns:
        SummarizeResponse: 摘要結果
    """
    # TODO: 實作威脅摘要生成（後續任務）
    return SummarizeResponse(
        summary="摘要功能尚未實作",
    )


@app.post("/api/v1/ai/translate-to-business", response_model=SummarizeResponse)
async def translate_to_business(request: SummarizeRequest):
    """
    轉換為業務語言
    
    將技術描述轉換為適合管理層的業務風險描述。
    
    Args:
        request: 轉換請求（包含技術描述）
    
    Returns:
        SummarizeResponse: 業務風險描述
    """
    # TODO: 實作業務語言轉換（後續任務）
    return SummarizeResponse(
        summary="業務語言轉換功能尚未實作",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=ENVIRONMENT == "development",
    )

