# 系統架構文件

## 概述

AETIM（AI 驅動之自動化威脅情資管理系統）採用微服務架構，包含後端 API 服務、前端 Web 應用、AI/ML 服務等模組。

## 系統架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                        使用者端                              │
│                    (Web Browser)                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ HTTPS
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                     前端服務 (Next.js)                       │
│                  Port: 3030                                 │
│  - React 18+                                                │
│  - Next.js 14+ (App Router)                                 │
│  - TypeScript 5+                                            │
│  - Tailwind CSS 3+                                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ REST API
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                   後端 API 服務 (FastAPI)                    │
│                  Port: 8000                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ API 層                                               │   │
│  │ - 身份驗證與授權                                       │   │
│  │ - 資產管理                                            │   │
│  │ - 威脅情資管理                                         │   │
│  │ - 報告生成                                            │   │
│  │ - 系統管理                                            │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 應用層 (Application Layer)                           │   │
│  │ - 業務邏輯處理                                        │   │
│  │ - DTO 轉換                                           │   │
│  │ - 領域事件處理                                        │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 領域層 (Domain Layer)                                │   │
│  │ - 領域模型 (Aggregates, Entities, Value Objects)     │   │
│  │ - 領域服務                                           │   │
│  │ - 領域事件                                           │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 基礎設施層 (Infrastructure Layer)                    │   │
│  │ - 資料庫存取 (SQLAlchemy)                            │   │
│  │ - 外部服務整合                                       │   │
│  │ - 訊息匯流排                                         │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────┬───────────────────────────┬─────────────────────┘
            │                           │
            │                           │
┌───────────▼───────────┐   ┌───────────▼───────────┐
│   資料庫 (SQLite)      │   │   Redis (快取)         │
│   Port: N/A           │   │   Port: 6379          │
└───────────────────────┘   └───────────────────────┘
            │
            │
┌───────────▼───────────────────────────────────────┐
│              AI/ML 服務 (FastAPI)                  │
│              Port: 8001                           │
│  - 威脅情資提取                                     │
│  - CVE 提取                                        │
│  - IOC 提取                                        │
│  - TTP 提取                                        │
│  - 產品資訊提取                                     │
└───────────────────────────────────────────────────┘
```

## 模組架構

### 1. 後端 API 服務

#### 1.1 模組結構

```
backend/
├── api/                          # API 層
│   └── controllers/             # API 控制器
├── asset_management/             # 資產管理模組
│   ├── application/             # 應用層
│   ├── domain/                  # 領域層
│   └── infrastructure/          # 基礎設施層
├── threat_intelligence/          # 威脅情資模組
│   ├── application/
│   ├── domain/
│   └── infrastructure/
├── analysis_assessment/          # 分析與評估模組
│   ├── application/
│   ├── domain/
│   └── infrastructure/
├── reporting_notification/       # 報告與通知模組
│   ├── application/
│   ├── domain/
│   └── infrastructure/
├── system_management/            # 系統管理模組
│   ├── application/
│   ├── domain/
│   └── infrastructure/
└── shared_kernel/               # 共享核心模組
    ├── application/
    ├── domain/
    └── infrastructure/
```

#### 1.2 分層架構

**API 層**
- 處理 HTTP 請求與回應
- 路由定義
- 請求驗證
- 回應格式化

**應用層**
- 業務邏輯協調
- DTO 轉換
- 領域事件發布
- 交易管理

**領域層**
- 核心業務邏輯
- 領域模型
- 領域規則
- 領域事件

**基礎設施層**
- 資料庫存取
- 外部服務整合
- 訊息匯流排
- 快取服務

### 2. 前端 Web 應用

#### 2.1 架構模式

- **框架**：Next.js 14+ (App Router)
- **UI 函式庫**：React 18+
- **狀態管理**：React Hooks + Context
- **路由**：Next.js App Router
- **樣式**：Tailwind CSS 3+

#### 2.2 目錄結構

```
frontend/
├── app/                         # Next.js App Router
│   ├── (auth)/                 # 認證路由群組
│   ├── dashboard/              # 儀表板頁面
│   ├── assets/                  # 資產管理頁面
│   ├── threats/                 # 威脅管理頁面
│   └── ...
├── components/                  # React 元件
│   ├── auth/                   # 認證相關元件
│   ├── layout/                 # 布局元件
│   └── ...
├── lib/                        # 工具函式庫
│   ├── api/                    # API 客戶端
│   ├── auth/                   # 認證工具
│   └── utils/                  # 工具函式
└── types/                      # TypeScript 型別定義
```

### 3. AI/ML 服務

#### 3.1 功能

- **威脅情資提取**：從原始威脅情資中提取結構化資訊
- **CVE 提取**：識別和提取 CVE 編號
- **IOC 提取**：識別和提取 Indicators of Compromise
- **TTP 提取**：識別和提取 Tactics, Techniques, and Procedures
- **產品資訊提取**：識別和提取產品名稱與版本

#### 3.2 技術堆疊

- **框架**：FastAPI
- **NLP 函式庫**：spaCy, transformers
- **API 格式**：RESTful API

## 資料流程

### 1. 威脅收集流程

```
威脅來源 (NVD, CISA KEV, etc.)
    │
    ▼
威脅收集服務 (ThreatCollectionService)
    │
    ▼
AI/ML 服務 (威脅情資提取)
    │
    ▼
威脅儲存 (ThreatRepository)
    │
    ▼
關聯分析服務 (AssociationAnalysisService)
    │
    ▼
風險計算服務 (RiskCalculationService)
    │
    ▼
報告生成服務 (ReportGenerationService)
```

### 2. 資產管理流程

```
CSV 檔案匯入
    │
    ▼
資產解析服務 (AssetParsingService)
    │
    ▼
資產儲存 (AssetRepository)
    │
    ▼
產品資訊提取 (AssetProduct)
```

### 3. 使用者認證流程

```
前端應用
    │
    ▼
OAuth2/OIDC IdP
    │
    ▼
後端 API (AuthService)
    │
    ▼
使用者儲存 (UserRepository)
    │
    ▼
權限檢查 (AuthorizationService)
```

## 技術決策

### 1. 後端架構

- **選擇**：Clean Architecture / DDD
- **理由**：關注點分離、可測試性、可維護性
- **優點**：模組化、易於擴展、業務邏輯獨立

### 2. 前端架構

- **選擇**：Next.js App Router
- **理由**：伺服器端渲染、路由整合、效能優化
- **優點**：SEO 友善、快速載入、開發體驗良好

### 3. 資料庫

- **開發環境**：SQLite
- **生產環境**：MS SQL Server
- **理由**：開發簡單、生產穩定、企業級功能

### 4. 快取

- **選擇**：Redis
- **理由**：高效能、分散式支援、豐富資料結構
- **用途**：API 回應快取、會話儲存、速率限制

## 安全性架構

### 1. 身份驗證

- **協議**：OAuth 2.0 / OIDC
- **Token 類型**：JWT
- **驗證方式**：JWKS

### 2. 授權

- **模型**：RBAC (Role-Based Access Control)
- **角色**：CISO, IT_Admin, Analyst, Viewer
- **權限**：資源級別權限控制

### 3. 資料保護

- **傳輸加密**：TLS 1.2+
- **儲存加密**：敏感資料加密
- **輸入驗證**：SQL 注入、XSS 防護

## 監控與可觀測性

### 1. 日誌

- **格式**：結構化日誌 (JSON)
- **級別**：DEBUG, INFO, WARN, ERROR, FATAL
- **內容**：請求 ID、回應時間、狀態碼

### 2. 指標

- **格式**：Prometheus
- **指標**：API 回應時間、請求數量、錯誤率

### 3. 追蹤

- **方式**：分佈式追蹤
- **ID**：Trace ID
- **範圍**：跨模組 API 呼叫

## 部署架構

### 1. 開發環境

- **容器化**：Docker Compose
- **服務**：後端、前端、AI 服務、Redis、資料庫

### 2. 生產環境

- **容器化**：Docker / Kubernetes
- **反向代理**：Nginx / Traefik
- **負載平衡**：多實例部署
- **資料庫**：MS SQL Server（高可用性）

## 相關文件

- **API 文件**：`docs/API.md`
- **部署文件**：`docs/DEPLOYMENT.md`
- **開發文件**：`docs/DEVELOPMENT.md`

