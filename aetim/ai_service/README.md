# AETIM AI/ML 服務

AI/ML 服務提供威脅資訊提取、摘要生成等功能。

## 專案結構

```
ai_service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 應用程式入口
│   ├── models/              # 資料模型
│   │   ├── __init__.py
│   │   ├── request.py       # 請求模型
│   │   └── response.py      # 回應模型
│   ├── services/            # 服務層
│   │   └── __init__.py
│   ├── processors/          # 處理器（提取器）
│   │   └── __init__.py
│   └── ml_models/          # ML 模型管理
│       ├── __init__.py
│       └── model_loader.py  # 模型載入器
├── tests/                   # 測試
│   ├── __init__.py
│   └── test_health.py
├── requirements.txt         # Python 依賴
├── pytest.ini              # pytest 配置
├── .env.example             # 環境變數範例
└── README.md                # 本檔案
```

## 安裝與執行

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 下載 spaCy 中文模型

```bash
python -m spacy download zh_core_web_sm
```

### 3. 設定環境變數

複製 `.env.example` 為 `.env` 並填入實際值：

```bash
cp .env.example .env
```

### 4. 執行服務

#### 開發模式

```bash
python -m app.main
```

或使用 uvicorn：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

#### Docker 執行

```bash
docker-compose up ai-service
```

## API 端點

### 健康檢查

```http
GET /health
GET /api/v1/health
```

### 提取威脅資訊

```http
POST /api/v1/ai/extract
Content-Type: application/json

{
  "text": "威脅情資文字內容..."
}
```

### 生成摘要

```http
POST /api/v1/ai/summarize
Content-Type: application/json

{
  "content": "要摘要的內容...",
  "target_length": 200,
  "language": "zh-TW",
  "style": "executive"
}
```

### 轉換為業務語言

```http
POST /api/v1/ai/translate-to-business
Content-Type: application/json

{
  "content": "技術描述..."
}
```

## 測試

執行測試：

```bash
pytest
```

執行測試並顯示覆蓋率：

```bash
pytest --cov=app --cov-report=html
```

## 開發注意事項

1. **模型下載**：首次執行前需要下載 spaCy 中文模型
2. **依賴安裝**：某些 ML 模型可能需要較大的磁碟空間
3. **效能考量**：模型載入可能需要一些時間，建議在啟動時預載入

