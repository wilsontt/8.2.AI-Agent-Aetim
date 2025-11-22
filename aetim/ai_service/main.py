"""
AETIM AI/ML 服務主程式

本服務提供 AI/ML 相關功能，包括：
- 威脅資訊提取（CVE、產品名稱、TTPs、IOCs）
- 威脅摘要生成
- 業務風險描述生成
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AETIM AI Service",
    description="AI/ML 服務 API",
    version="1.0.0",
)

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy"}


@app.post("/extract")
async def extract_threat_info():
    """提取威脅資訊"""
    # TODO: 實作威脅資訊提取
    return {"message": "Extraction not implemented yet"}


@app.post("/summarize")
async def summarize_threat():
    """生成威脅摘要"""
    # TODO: 實作威脅摘要生成
    return {"message": "Summarization not implemented yet"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

