"""
AETIM AI/ML 服務主程式

本模組為 FastAPI 應用程式的入口點，負責：
- 初始化 FastAPI 應用程式
- 設定路由與中介軟體
- 啟動應用程式伺服器
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import time
import traceback

from app.models.request import ExtractRequest, SummarizeRequest
from app.models.response import ExtractResponse, SummarizeResponse
from app.services.extraction_service import ExtractionService
from app.utils.logging import setup_logging, get_logger, log_ai_processing

# 從環境變數讀取配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# 設定日誌
setup_logging(LOG_LEVEL)
logger = get_logger(__name__)


# 全域提取服務實例
extraction_service = ExtractionService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時初始化
    logger.info(
        "AI Service starting",
        extra={
            "environment": ENVIRONMENT,
            "log_level": LOG_LEVEL,
        }
    )
    
    # TODO: 載入 ML 模型（spaCy、transformers 等）
    # 這裡可以在啟動時預載入模型以提高效能
    
    yield
    
    # 關閉時清理
    logger.info("AI Service shutting down")


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


@app.get("/api/v1/ai/health")
async def ai_health_check():
    """
    健康檢查端點（AI 服務專用）
    
    Returns:
        dict: 服務健康狀態
    """
    return await health_check()


@app.post("/api/v1/ai/extract", response_model=ExtractResponse)
async def extract_threat_info(request: ExtractRequest):
    """
    提取威脅資訊
    
    從文字內容中提取 CVE 編號、產品名稱、TTPs、IOCs 等威脅資訊。
    符合 AC-009-1 至 AC-009-5 要求。
    記錄 AI 處理日誌（AC-009-6）。
    
    Args:
        request: 提取請求（包含文字內容）
    
    Returns:
        ExtractResponse: 提取結果（包含 CVE、產品、TTPs、IOCs、信心分數）
    
    Raises:
        HTTPException: 當請求無效或處理失敗時
    """
    start_time = time.time()
    
    try:
        # 驗證輸入
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文字內容不能為空",
            )
        
        # 使用整合提取服務提取威脅資訊
        result = extraction_service.extract(request.text)
        
        # 轉換 IOC 格式（從字典轉換為列表）
        ioc_list = []
        for ioc_type, values in result["iocs"].items():
            for value in values:
                ioc_list.append({
                    "type": ioc_type,
                    "value": value,
                    "confidence": 0.8,  # IOC 預設信心分數
                })
        
        response = ExtractResponse(
            cve=result["cve"],
            products=result["products"],
            ttps=result["ttps"],
            iocs=ioc_list,
            confidence=result["confidence"],
        )
        
        # 計算處理時間
        processing_time = time.time() - start_time
        
        # 記錄 AI 處理日誌（AC-009-6）
        log_ai_processing(
            logger=logger,
            input_text=request.text,
            result=result,
            confidence=result["confidence"],
            processing_time=processing_time,
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "提取威脅資訊失敗",
            extra={
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提取威脅資訊時發生錯誤：{str(e)}",
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
    
    Raises:
        HTTPException: 當請求無效或處理失敗時
    """
    try:
        # 驗證輸入
        if not request.content or not request.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="內容不能為空",
            )
        
        # TODO: 實作威脅摘要生成（後續任務）
        logger.warning("摘要功能尚未實作，返回預設回應")
        return SummarizeResponse(
            summary="摘要功能尚未實作",
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "生成威脅摘要失敗",
            extra={
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成威脅摘要時發生錯誤：{str(e)}",
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
    
    Raises:
        HTTPException: 當請求無效或處理失敗時
    """
    try:
        # 驗證輸入
        if not request.content or not request.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="內容不能為空",
            )
        
        # TODO: 實作業務語言轉換（後續任務）
        logger.warning("業務語言轉換功能尚未實作，返回預設回應")
        return SummarizeResponse(
            summary="業務語言轉換功能尚未實作",
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "轉換為業務語言失敗",
            extra={
                "error": str(e),
                "traceback": traceback.format_exc(),
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"轉換為業務語言時發生錯誤：{str(e)}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=ENVIRONMENT == "development",
    )

