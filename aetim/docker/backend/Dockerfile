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

# 建立資料目錄
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8000

# 啟動應用程式
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

