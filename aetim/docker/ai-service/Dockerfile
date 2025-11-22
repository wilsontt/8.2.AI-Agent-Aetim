FROM python:3.10-slim

WORKDIR /app

# 安裝系統依賴（包含 curl 用於健康檢查）
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 暴露端口
EXPOSE 8001

# 啟動 AI 服務
# 使用 app.main:app 因為 main.py 現在在 app/ 目錄下
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

