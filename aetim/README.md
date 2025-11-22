# AETIM - AI 驅動之自動化威脅情資管理系統

**專案名稱**：AI 驅動之自動化威脅情資管理系統 (AETIM)  
**版本**：v1.0.0  
**專案狀態**：開發中

## 專案概述

AETIM 是一個 AI 驅動的自動化威脅情資管理系統，旨在建立一個完整的自動化流程，主動蒐集、分析外部威脅情資，並與內部資產進行關聯性分析，最終產出可行動的報告，並即時通知相關人員。

## 專案結構

```
aetim/
├── backend/                    # 後端應用程式（Python/FastAPI）
│   ├── shared_kernel/         # 共享核心模組
│   ├── asset_management/      # 資產管理模組
│   ├── threat_intelligence/    # 威脅情資模組
│   ├── analysis_assessment/    # 分析與評估模組
│   ├── reporting_notification/ # 報告與通知模組
│   ├── system_management/      # 系統管理模組
│   ├── api/                    # API 層
│   └── tests/                  # 測試
├── frontend/                   # 前端應用程式（Next.js）
│   ├── app/                    # Next.js App Router
│   ├── components/            # React 元件
│   ├── lib/                   # 工具函式庫
│   └── types/                 # TypeScript 型別定義
├── ai_service/                # AI/ML 服務（Python）
│   ├── services/              # AI 服務
│   ├── models/               # AI 模型
│   └── utils/                # 工具函式
├── docker/                    # Docker 配置檔案
├── scripts/                   # 腳本檔案
├── data/                      # 資料目錄（SQLite 資料庫）
└── reports/                   # 報告目錄

```

## 技術堆疊

### 後端
- **框架**：FastAPI
- **程式語言**：Python 3.10+
- **ORM**：SQLAlchemy
- **資料庫遷移**：Alembic
- **資料庫**：SQLite（開發）/ MS SQL Server（生產）
- **緩存**：Redis 7.0+

### 前端
- **框架**：Next.js 14+ (App Router)
- **UI 函式庫**：React 18+
- **程式語言**：TypeScript 5+
- **樣式框架**：Tailwind CSS 3+

### AI/ML 服務
- **程式語言**：Python 3.10+
- **NLP 函式庫**：spaCy, transformers
- **API 整合**：RESTful API

### 容器化
- **容器化平台**：Docker
- **容器編排**：Docker Compose

## 快速開始

### 前置需求
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Redis 7.0+（或使用 Docker）

### 設定開發環境

1. **複製環境變數檔案**
   ```bash
   cp .env.example .env
   # 根據需要修改 .env 檔案
   ```

2. **執行設定腳本（可選）**
   ```bash
   ./scripts/setup.sh
   ```

3. **啟動所有服務**
   ```bash
   docker-compose up -d
   ```

4. **查看服務狀態**
   ```bash
   docker-compose ps
   ```

5. **查看日誌**
   ```bash
   docker-compose logs -f
   ```

6. **測試服務健康狀態**
   ```bash
   ./scripts/test_health.sh
   ```

### 服務端點

- **後端 API**：http://localhost:8000
  - API 文件：http://localhost:8000/docs
  - 健康檢查：http://localhost:8000/api/v1/health

- **前端應用**：http://localhost:3000

- **AI 服務**：http://localhost:8001
  - 健康檢查：http://localhost:8001/health

- **Redis**：localhost:6379

### 本地開發（不使用 Docker）

#### 後端開發

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

#### 前端開發

```bash
cd frontend
npm install
npm run dev
```

#### AI 服務開發

```bash
cd ai_service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

## 開發規範

本專案遵循專案憲章（Project Constitution）的所有原則，請參考：
- `系統需求設計與分析/1.專案憲章 Project Constitution..md`

### 程式碼風格

- **Python**：使用 Black 格式化，Ruff 進行 Lint
- **TypeScript**：使用 Prettier 格式化，ESLint 進行 Lint

### 測試

```bash
# 後端測試
cd backend
pytest

# 測試覆蓋率
pytest --cov=backend --cov-report=html
```

## 相關文件

- **系統需求規格**：`系統需求設計與分析/spec.md`
- **實作計畫**：`系統需求設計與分析/plan.md`
- **開發任務清單**：`系統需求設計與分析/tasks.md`
- **專案憲章**：`系統需求設計與分析/1.專案憲章 Project Constitution..md`

## 授權

MIT License
