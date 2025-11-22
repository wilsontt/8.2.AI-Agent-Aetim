# 系統實作計畫文件 (System Implementation Plan)

**專案名稱**：AI 驅動之自動化威脅情資管理系統 (AETIM)  
**文件版本**：v1.0.0  
**撰寫日期**：2025-11-21  
**最後修訂**：2025-11-21  
**文件狀態**：已核准 (Approved)

---

## 目錄

1. [目的](#1-目的)
2. [範圍](#2-範圍)
3. [系統架構設計](#3-系統架構設計)
   - [3.1 架構模式](#31-架構模式)
   - [3.2 有界上下文劃分](#32-有界上下文劃分)
   - [3.3 模組化單體設計](#33-模組化單體設計)
   - [3.4 技術堆疊選擇](#34-技術堆疊選擇)
4. [資料庫設計](#4-資料庫設計)
   - [4.1 資料模型](#41-資料模型)
   - [4.2 資料庫 Schema](#42-資料庫-schema)
   - [4.3 資料遷移策略](#43-資料遷移策略)
5. [API 設計](#5-api-設計)
   - [5.1 RESTful API 規格](#51-restful-api-規格)
   - [5.2 API 端點定義](#52-api-端點定義)
   - [5.3 身份驗證與授權](#53-身份驗證與授權)
6. [模組設計](#6-模組設計)
   - [6.1 基礎建設與情資定義模組](#61-基礎建設與情資定義模組)
   - [6.2 自動化收集與關聯分析模組](#62-自動化收集與關聯分析模組)
   - [6.3 報告生成與即時通知模組](#63-報告生成與即時通知模組)
   - [6.4 Web 管理界面模組](#64-web-管理界面模組)
7. [AI/ML 整合設計](#7-aiml-整合設計)
   - [7.1 NLP 處理架構](#71-nlp-處理架構)
   - [7.2 威脅資訊提取](#72-威脅資訊提取)
   - [7.3 報告摘要生成](#73-報告摘要生成)
8. [測試策略](#8-測試策略)
   - [8.1 單元測試](#81-單元測試)
   - [8.2 整合測試](#82-整合測試)
   - [8.3 端對端測試](#83-端對端測試)
   - [8.4 效能測試](#84-效能測試)
9. [部署計畫](#9-部署計畫)
   - [9.1 容器化策略](#91-容器化策略)
   - [9.2 環境配置](#92-環境配置)
   - [9.3 監控與日誌](#93-監控與日誌)
10. [開發時程](#10-開發時程)
    - [10.1 階段劃分](#101-階段劃分)
    - [10.2 里程碑](#102-里程碑)
11. [風險管理](#11-風險管理)
12. [憲章遵循檢查](#12-憲章遵循檢查)
13. [參考文件](#13-參考文件)

---

## 1. 目的

本文件旨在定義「AI 驅動之自動化威脅情資管理系統 (AETIM)」的系統實作計畫，包含系統架構設計、技術選型、模組設計、測試策略與部署計畫。

本計畫遵循專案憲章（Project Constitution）的所有原則，特別是：
- **P0：規格驅動開發 (SDD)**：本文件為 Phase 2: 計畫 (PLAN) 階段產出
- **P10：架構設計**：嚴格遵循 DDD 方法論與模組化單體架構
- **P11：技術堆疊**：在指定技術堆疊內開發
- **P7：嚴謹測試標準**：定義完整的測試策略
- **H3：合規要求**：包含憲章遵循檢查章節

---

## 2. 範圍

### 2.1 計畫範圍

本計畫涵蓋以下內容：

1. **系統架構設計**
   - 領域驅動設計 (DDD) 的領域模型與有界上下文
   - 模組化單體架構設計
   - 技術堆疊選擇與理由

2. **資料庫設計**
   - 資料模型設計
   - 資料庫 Schema 定義
   - 資料遷移策略

3. **API 設計**
   - RESTful API 規格
   - 端點定義與介面設計
   - 身份驗證與授權機制

4. **模組設計**
   - 各功能模組的詳細設計
   - 模組間的通訊機制
   - 非同步處理設計

5. **AI/ML 整合設計**
   - NLP 處理架構
   - 威脅資訊提取機制
   - 報告摘要生成策略

6. **測試策略**
   - 單元測試、整合測試、端對端測試計畫
   - 測試覆蓋率目標
   - 測試自動化策略

7. **部署計畫**
   - 容器化策略
   - 環境配置
   - 監控與日誌方案

### 2.2 計畫邊界

**包含在計畫範圍內：**
- 系統架構與模組設計
- 資料庫設計與 API 設計
- 測試策略與部署計畫
- AI/ML 整合設計

**不包含在計畫範圍內：**
- 詳細的程式碼實作（將在 Phase 3: 任務階段定義）
- 外部威脅情資來源的 API 詳細規格（僅定義整合介面）
- 企業 IdP 的實作細節（僅定義整合介面）

---

## 3. 系統架構設計

### 3.1 架構模式

本系統採用**模組化單體 (Modular Monolith)** 架構模式，並嚴格遵循**領域驅動設計 (DDD)** 方法論。此架構選擇符合專案憲章 P10 的規範，旨在建立一個高內聚、低耦合、可演進的系統架構。

#### 3.1.1 架構模式選擇：模組化單體

**選擇理由**：

1. **簡化部署與運維**（符合 P1：簡潔優先於複雜）
   - 單一應用程式部署，降低部署複雜度
   - 簡化監控、日誌收集與故障排除
   - 減少網路延遲與服務間通訊開銷

2. **清晰的模組邊界**
   - 每個模組代表一個有界上下文（Bounded Context）
   - 模組間透過明確的介面進行通訊
   - 便於未來拆分為微服務（如需要）

3. **開發效率**
   - 開發團隊可在單一程式碼庫中協作
   - 簡化跨模組的重構與測試
   - 降低分散式系統的複雜性

4. **符合專案規模**
   - 初期系統規模適中，無需分散式架構的複雜性
   - 未來可根據需求演進為微服務架構

#### 3.1.2 領域驅動設計 (DDD) 方法論

本系統嚴格遵循 DDD 方法論，將系統劃分為多個**有界上下文 (Bounded Context)**，每個上下文代表一個獨立的業務領域。

**DDD 核心概念應用**：

1. **領域模型 (Domain Model)**
   - 每個有界上下文擁有獨立的領域模型
   - 領域模型封裝業務邏輯與規則
   - 避免貧血模型（Anemic Domain Model）

2. **聚合 (Aggregate)**
   - 定義資料一致性邊界
   - 確保業務規則的一致性
   - 例如：資產（Asset）聚合、威脅（Threat）聚合

3. **領域服務 (Domain Service)**
   - 處理跨聚合的業務邏輯
   - 例如：風險分數計算服務、關聯分析服務

4. **應用服務 (Application Service)**
   - 協調領域模型與基礎設施
   - 處理用例（Use Case）的執行流程
   - 不包含業務邏輯，僅負責協調

#### 3.1.3 非同步通訊機制

根據專案憲章 P10 規範，對於非即時性的跨模組操作，必須使用事件/訊息佇列進行非同步處理。

**非同步通訊應用場景**：

1. **威脅情資收集**
   - 收集作業觸發後，以非同步方式處理
   - 避免阻塞使用者請求
   - 支援長時間執行的收集任務

2. **關聯分析與風險計算**
   - 威脅情資收集完成後，觸發關聯分析事件
   - 分析完成後，觸發風險計算事件
   - 確保處理流程的可擴充性

3. **報告生成**
   - 週報生成以非同步方式執行
   - 生成完成後透過事件通知相關模組
   - 支援長時間執行的報告生成任務

4. **通知發送**
   - 通知發送以非同步方式處理
   - 避免影響主要業務流程的效能
   - 支援重試機制與錯誤處理

**事件驅動架構**：

- **事件發布者 (Event Publisher)**：發布領域事件
- **事件訂閱者 (Event Subscriber)**：訂閱並處理事件
- **事件儲存 (Event Store)**：持久化事件（用於稽核與重播）

#### 3.1.4 架構層次結構

系統採用分層架構（Layered Architecture），確保關注點分離：

```
┌─────────────────────────────────────────┐
│  表現層 (Presentation Layer)             │
│  - Web UI (Next.js + React)             │
│  - API Controllers                      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  應用層 (Application Layer)              │
│  - Application Services                 │
│  - Use Cases / Command Handlers         │
│  - DTOs / View Models                   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  領域層 (Domain Layer)                   │
│  - Domain Models / Entities             │
│  - Domain Services                      │
│  - Domain Events                        │
│  - Value Objects                        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  基礎設施層 (Infrastructure Layer)        │
│  - Data Access (Repository)             │
│  - External Services Integration        │
│  - Message Queue / Event Bus            │
│  - File Storage                         │
└─────────────────────────────────────────┘
```

**各層職責**：

1. **表現層**：處理 HTTP 請求、UI 渲染、輸入驗證
2. **應用層**：協調領域邏輯、處理用例、管理交易
3. **領域層**：核心業務邏輯、領域規則、領域事件
4. **基礎設施層**：資料持久化、外部服務整合、技術實作

#### 3.1.5 模組間通訊模式

**同步通訊**：
- 用於即時性要求高的操作
- 透過應用服務直接呼叫
- 例如：查詢資產清冊、檢視威脅詳情

**非同步通訊**：
- 用於非即時性操作
- 透過事件/訊息佇列
- 例如：威脅收集、報告生成、通知發送

**通訊介面**：
- 模組間透過明確的介面（Interface）進行通訊
- 禁止跨模組直接存取資料庫（符合 P12：單一事實來源）
- 每個模組擁有獨立的資料存取層

### 3.2 有界上下文劃分

根據領域驅動設計 (DDD) 方法論，本系統劃分為以下**有界上下文 (Bounded Context)**，每個上下文代表一個獨立的業務領域，擁有自己的領域模型與業務規則。

#### 3.2.1 有界上下文總覽

系統共劃分為 **5 個主要有界上下文**：

1. **資產管理上下文 (Asset Management Context)**
2. **威脅情資上下文 (Threat Intelligence Context)**
3. **分析與評估上下文 (Analysis & Assessment Context)**
4. **報告與通知上下文 (Reporting & Notification Context)**
5. **系統管理上下文 (System Management Context)**

#### 3.2.2 資產管理上下文 (Asset Management Context)

**職責**：管理組織內部資產清冊，提供資產資訊給其他上下文使用。

**核心領域概念**：

- **聚合根 (Aggregate Root)**：`Asset`（資產）
- **實體 (Entity)**：`Asset`、`AssetProduct`（資產產品資訊）
- **值物件 (Value Object)**：`IPAddress`、`DataSensitivity`、`BusinessCriticality`
- **領域服務 (Domain Service)**：`AssetParsingService`（資產解析服務）

**主要功能**：
- 資產清冊的 CRUD 操作（US-001, US-002, US-003）
- CSV 檔案匯入與解析
- 資產搜尋與篩選
- 產品名稱與版本資訊提取

**領域規則**：
- 資產必須有唯一識別碼
- 資產的資料敏感度與業務關鍵性用於風險計算
- 對外暴露資產（Public-facing = Y）需特別標記

**對外介面**：
- 提供資產查詢服務給「分析與評估上下文」
- 發布資產變更事件（`AssetCreated`、`AssetUpdated`、`AssetDeleted`）

#### 3.2.3 威脅情資上下文 (Threat Intelligence Context)

**職責**：管理威脅情資來源訂閱、收集威脅情資、儲存威脅資訊。

**核心領域概念**：

- **聚合根**：`ThreatFeed`（威脅情資來源）、`Threat`（威脅）
- **實體**：`ThreatFeed`、`Threat`、`ThreatSource`（威脅來源）
- **值物件**：`CVE`、`CVSS`、`ThreatType`、`Priority`
- **領域服務**：`ThreatCollectionService`（威脅收集服務）、`ThreatParsingService`（威脅解析服務）

**主要功能**：
- 威脅情資來源訂閱管理（US-006, US-007）
- 自動化威脅情資收集（US-008）
- AI/NLP 威脅資訊提取（US-009）
- 威脅資料標準化與儲存（US-014）

**領域規則**：
- 威脅必須有唯一的 CVE 編號或識別碼
- 威脅收集必須遵循來源的優先級設定
- 收集失敗需記錄並觸發告警

**對外介面**：
- 提供威脅查詢服務給「分析與評估上下文」
- 發布威脅收集完成事件（`ThreatCollected`、`ThreatCollectionFailed`）

#### 3.2.4 分析與評估上下文 (Analysis & Assessment Context)

**職責**：執行威脅與資產的關聯分析、計算風險分數、管理優先情資需求 (PIR)。

**核心領域概念**：

- **聚合根**：`PIR`（優先情資需求）、`ThreatAssetAssociation`（威脅資產關聯）、`RiskAssessment`（風險評估）
- **實體**：`PIR`、`ThreatAssetAssociation`、`RiskAssessment`
- **值物件**：`RiskScore`、`PIRCondition`、`MatchingCriteria`
- **領域服務**：`AssociationAnalysisService`（關聯分析服務）、`RiskCalculationService`（風險計算服務）、`PIRMatchingService`（PIR 匹配服務）

**主要功能**：
- PIR 定義與管理（US-004, US-005）
- 威脅與資產關聯分析（US-010, US-011）
- 風險分數計算（US-012, US-013）

**領域規則**：
- 風險分數計算公式：`基礎 CVSS 分數 × 資產重要性加權 × 其他加權因子`
- 符合 PIR 的威脅需優先處理
- 關聯分析必須支援模糊比對（產品名稱變體、版本範圍）

**對外介面**：
- 訂閱「資產管理上下文」的資產變更事件
- 訂閱「威脅情資上下文」的威脅收集完成事件
- 提供風險評估結果給「報告與通知上下文」
- 發布風險評估完成事件（`RiskAssessmentCompleted`）

#### 3.2.5 報告與通知上下文 (Reporting & Notification Context)

**職責**：生成各類報告（CISO 週報、IT 工單）、發送通知、管理通知規則。

**核心領域概念**：

- **聚合根**：`Report`（報告）、`NotificationRule`（通知規則）、`Notification`（通知）
- **實體**：`Report`、`NotificationRule`、`Notification`、`ReportTemplate`（報告範本）
- **值物件**：`ReportFormat`、`NotificationType`、`RecipientList`
- **領域服務**：`ReportGenerationService`（報告生成服務）、`AISummaryService`（AI 摘要服務）、`NotificationService`（通知服務）

**主要功能**：
- CISO 週報生成（US-015, US-016）
- IT 工單生成（US-017, US-018）
- 通知規則設定與發送（US-019, US-020, US-021）

**領域規則**：
- 週報必須包含 AI 生成的業務風險描述
- 嚴重威脅（風險分數 ≥ 8.0）需立即發送通知
- 報告檔案需按年月目錄結構儲存

**對外介面**：
- 訂閱「分析與評估上下文」的風險評估完成事件
- 提供報告查詢與下載服務
- 發布通知發送事件（`NotificationSent`）

#### 3.2.6 系統管理上下文 (System Management Context)

**職責**：管理系統設定、排程、身份驗證、授權、稽核日誌。

**核心領域概念**：

- **聚合根**：`SystemConfiguration`（系統設定）、`Schedule`（排程）、`User`（使用者）、`Role`（角色）、`AuditLog`（稽核日誌）
- **實體**：`SystemConfiguration`、`Schedule`、`User`、`Role`、`Permission`（權限）、`AuditLog`
- **值物件**：`CronExpression`、`ScheduleStatus`、`UserRole`
- **領域服務**：`AuthenticationService`（身份驗證服務）、`AuthorizationService`（授權服務）、`AuditLogService`（稽核日誌服務）

**主要功能**：
- 身份驗證與授權（US-022, US-023）
- 系統設定管理（US-024）
- 排程管理（US-025, US-026）
- 狀態監控（US-027, US-028, US-029）

**領域規則**：
- 所有資料異動必須記錄稽核日誌
- 排程必須支援 Cron 表達式
- 角色權限必須遵循 RBAC 模型

**對外介面**：
- 提供身份驗證與授權服務給所有其他上下文
- 提供稽核日誌記錄服務
- 提供排程管理服務

#### 3.2.7 上下文關係圖

```
┌─────────────────────────────────────────────────────────────┐
│              系統管理上下文 (System Management)               │
│  - 身份驗證/授權                                              │
│  - 排程管理                                                  │
│  - 稽核日誌                                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓ 提供服務
        ┌───────────────────┴───────────────────┐
        ↓                                       ↓
┌───────────────────┐              ┌──────────────────────┐
│  資產管理上下文     │              │  威脅情資上下文        │
│  (Asset Mgmt)     │              │  (Threat Intel)      │
│  - 資產清冊管理     │              │  - 來源訂閱           │
│  - 資產匯入        │              │  - 威脅收集           │
└───────────────────┘              │  - AI 資訊提取        │
        ↓ 發布事件                  └──────────────────────┘
        └───────────────┬───────────────┘
                        ↓ 訂閱事件
        ┌───────────────────────────────┐
        │  分析與評估上下文               │
        │  (Analysis & Assessment)      │
        │  - PIR 管理                    │
        │  - 關聯分析                    │
        │  - 風險計算                    │
        └───────────────────────────────┘
                        ↓ 發布事件
        ┌───────────────────────────────┐
        │  報告與通知上下文               │
        │  (Reporting & Notification)   │
        │  - 報告生成                    │
        │  - 通知發送                    │
        └───────────────────────────────┘
```

#### 3.2.8 上下文間通訊模式

**事件驅動通訊**（非同步）：
- `AssetCreated` / `AssetUpdated` / `AssetDeleted`：資產管理上下文 → 分析與評估上下文
- `ThreatCollected`：威脅情資上下文 → 分析與評估上下文
- `RiskAssessmentCompleted`：分析與評估上下文 → 報告與通知上下文
- `NotificationSent`：報告與通知上下文 → 系統管理上下文（稽核）

**服務呼叫通訊**（同步）：
- 資產查詢服務：分析與評估上下文 → 資產管理上下文
- 威脅查詢服務：分析與評估上下文 → 威脅情資上下文
- 身份驗證服務：所有上下文 → 系統管理上下文

**共享核心**（Shared Kernel）：
- 共用值物件：`CVE`、`CVSS`、`RiskScore` 等
- 共用介面：事件介面、服務介面

### 3.3 模組化單體設計

本系統採用**模組化單體 (Modular Monolith)** 架構，將系統組織為清晰的模組，但部署為單一應用程式。每個模組對應一個有界上下文，確保模組間界線清晰，便於未來演進。

#### 3.3.1 模組化單體結構總覽

系統由以下模組組成：

```
AETIM (模組化單體應用程式)
├── Shared Kernel (共享核心)
│   ├── Common (共用值物件、介面)
│   ├── Events (事件定義)
│   └── Infrastructure (共用基礎設施)
│
├── AssetManagement (資產管理模組)
├── ThreatIntelligence (威脅情資模組)
├── AnalysisAssessment (分析與評估模組)
├── ReportingNotification (報告與通知模組)
└── SystemManagement (系統管理模組)
```

#### 3.3.2 模組目錄結構

每個模組遵循相同的目錄結構，確保一致性與可維護性：

```
{ModuleName}/
├── Domain/                    # 領域層
│   ├── Entities/              # 實體
│   ├── ValueObjects/          # 值物件
│   ├── Aggregates/            # 聚合
│   ├── DomainServices/        # 領域服務
│   ├── DomainEvents/          # 領域事件
│   └── Interfaces/            # 領域介面
│
├── Application/               # 應用層
│   ├── Commands/              # 命令
│   ├── Queries/               # 查詢
│   ├── DTOs/                  # 資料傳輸物件
│   ├── Services/              # 應用服務
│   └── Handlers/              # 命令/查詢處理器
│
├── Infrastructure/            # 基礎設施層
│   ├── Persistence/           # 資料持久化
│   ├── ExternalServices/      # 外部服務整合
│   └── Messaging/             # 訊息處理
│
└── API/                       # API 層（僅限需要對外暴露的模組）
    ├── Controllers/           # API 控制器
    └── Middleware/            # 中介軟體
```

#### 3.3.3 資產管理模組 (AssetManagement)

**模組職責**：管理組織內部資產清冊。

**模組結構**：

```
AssetManagement/
├── Domain/
│   ├── Entities/
│   │   ├── Asset.cs           # 資產實體
│   │   └── AssetProduct.cs    # 資產產品資訊
│   ├── ValueObjects/
│   │   ├── IPAddress.cs
│   │   ├── DataSensitivity.cs
│   │   └── BusinessCriticality.cs
│   ├── Aggregates/
│   │   └── AssetAggregate.cs  # 資產聚合根
│   ├── DomainServices/
│   │   └── AssetParsingService.cs
│   └── DomainEvents/
│       ├── AssetCreated.cs
│       ├── AssetUpdated.cs
│       └── AssetDeleted.cs
│
├── Application/
│   ├── Commands/
│   │   ├── CreateAssetCommand.cs
│   │   ├── UpdateAssetCommand.cs
│   │   ├── DeleteAssetCommand.cs
│   │   └── ImportAssetsCommand.cs
│   ├── Queries/
│   │   ├── GetAssetQuery.cs
│   │   └── ListAssetsQuery.cs
│   └── Services/
│       └── AssetApplicationService.cs
│
└── Infrastructure/
    ├── Persistence/
    │   ├── AssetRepository.cs
    │   └── AssetDbContext.cs
    └── FileProcessing/
        └── CsvAssetImporter.cs
```

**對外介面**：
- `IAssetQueryService`：提供資產查詢服務
- 發布領域事件：`AssetCreated`、`AssetUpdated`、`AssetDeleted`

**依賴關係**：
- 依賴 `SharedKernel`（共用值物件、事件介面）
- 依賴 `SystemManagement`（身份驗證、稽核日誌）

#### 3.3.4 威脅情資模組 (ThreatIntelligence)

**模組職責**：管理威脅情資來源訂閱、收集威脅情資、儲存威脅資訊。

**模組結構**：

```
ThreatIntelligence/
├── Domain/
│   ├── Entities/
│   │   ├── Threat.cs          # 威脅實體
│   │   ├── ThreatFeed.cs      # 威脅情資來源
│   │   └── ThreatSource.cs
│   ├── ValueObjects/
│   │   ├── CVE.cs
│   │   ├── CVSS.cs
│   │   └── ThreatType.cs
│   ├── Aggregates/
│   │   ├── ThreatAggregate.cs
│   │   └── ThreatFeedAggregate.cs
│   ├── DomainServices/
│   │   ├── ThreatCollectionService.cs
│   │   └── ThreatParsingService.cs
│   └── DomainEvents/
│       ├── ThreatCollected.cs
│       └── ThreatCollectionFailed.cs
│
├── Application/
│   ├── Commands/
│   │   ├── SubscribeFeedCommand.cs
│   │   ├── CollectThreatsCommand.cs
│   │   └── UpdateThreatCommand.cs
│   ├── Queries/
│   │   ├── GetThreatQuery.cs
│   │   └── ListThreatsQuery.cs
│   └── Services/
│       └── ThreatApplicationService.cs
│
└── Infrastructure/
    ├── Persistence/
    │   ├── ThreatRepository.cs
    │   └── ThreatDbContext.cs
    ├── ExternalServices/
    │   ├── CisaKeVClient.cs
    │   ├── NvdClient.cs
    │   ├── VmwareVmsaClient.cs
    │   ├── MsrcClient.cs
    │   └── TwcertClient.cs
    └── AI/
        └── ThreatExtractionService.cs
```

**對外介面**：
- `IThreatQueryService`：提供威脅查詢服務
- 發布領域事件：`ThreatCollected`、`ThreatCollectionFailed`

**依賴關係**：
- 依賴 `SharedKernel`
- 依賴 `SystemManagement`（排程管理、身份驗證）

#### 3.3.5 分析與評估模組 (AnalysisAssessment)

**模組職責**：執行威脅與資產的關聯分析、計算風險分數、管理優先情資需求 (PIR)。

**模組結構**：

```
AnalysisAssessment/
├── Domain/
│   ├── Entities/
│   │   ├── PIR.cs             # 優先情資需求
│   │   ├── ThreatAssetAssociation.cs
│   │   └── RiskAssessment.cs
│   ├── ValueObjects/
│   │   ├── RiskScore.cs
│   │   ├── PIRCondition.cs
│   │   └── MatchingCriteria.cs
│   ├── Aggregates/
│   │   ├── PIRAggregate.cs
│   │   └── RiskAssessmentAggregate.cs
│   ├── DomainServices/
│   │   ├── AssociationAnalysisService.cs
│   │   ├── RiskCalculationService.cs
│   │   └── PIRMatchingService.cs
│   └── DomainEvents/
│       └── RiskAssessmentCompleted.cs
│
├── Application/
│   ├── Commands/
│   │   ├── CreatePIRCommand.cs
│   │   ├── UpdatePIRCommand.cs
│   │   └── PerformAnalysisCommand.cs
│   ├── Queries/
│   │   ├── GetPIRQuery.cs
│   │   ├── GetRiskAssessmentQuery.cs
│   │   └── ListAssociationsQuery.cs
│   └── Services/
│       └── AnalysisApplicationService.cs
│
└── Infrastructure/
    ├── Persistence/
    │   ├── PIRRepository.cs
    │   ├── AssociationRepository.cs
    │   └── AnalysisDbContext.cs
    └── Messaging/
        └── EventSubscriber.cs  # 訂閱其他模組的事件
```

**對外介面**：
- `IPIRQueryService`：提供 PIR 查詢服務
- `IRiskAssessmentService`：提供風險評估服務
- 發布領域事件：`RiskAssessmentCompleted`

**依賴關係**：
- 依賴 `SharedKernel`
- 依賴 `AssetManagement`（透過 `IAssetQueryService`）
- 依賴 `ThreatIntelligence`（透過 `IThreatQueryService`）
- 依賴 `SystemManagement`（身份驗證、稽核日誌）

#### 3.3.6 報告與通知模組 (ReportingNotification)

**模組職責**：生成各類報告、發送通知、管理通知規則。

**模組結構**：

```
ReportingNotification/
├── Domain/
│   ├── Entities/
│   │   ├── Report.cs          # 報告
│   │   ├── NotificationRule.cs
│   │   ├── Notification.cs
│   │   └── ReportTemplate.cs
│   ├── ValueObjects/
│   │   ├── ReportFormat.cs
│   │   ├── NotificationType.cs
│   │   └── RecipientList.cs
│   ├── Aggregates/
│   │   ├── ReportAggregate.cs
│   │   └── NotificationAggregate.cs
│   ├── DomainServices/
│   │   ├── ReportGenerationService.cs
│   │   ├── AISummaryService.cs
│   │   └── NotificationService.cs
│   └── DomainEvents/
│       └── NotificationSent.cs
│
├── Application/
│   ├── Commands/
│   │   ├── GenerateReportCommand.cs
│   │   ├── CreateNotificationRuleCommand.cs
│   │   └── SendNotificationCommand.cs
│   ├── Queries/
│   │   ├── GetReportQuery.cs
│   │   └── ListReportsQuery.cs
│   └── Services/
│       └── ReportingApplicationService.cs
│
└── Infrastructure/
    ├── Persistence/
    │   ├── ReportRepository.cs
    │   └── ReportingDbContext.cs
    ├── FileStorage/
    │   └── ReportFileStorage.cs
    ├── AI/
    │   └── ReportSummaryService.cs
    └── Notification/
        ├── EmailNotificationService.cs
        └── NotificationSender.cs
```

**對外介面**：
- `IReportQueryService`：提供報告查詢服務
- 發布領域事件：`NotificationSent`

**依賴關係**：
- 依賴 `SharedKernel`
- 依賴 `AnalysisAssessment`（透過 `IRiskAssessmentService`）
- 依賴 `SystemManagement`（身份驗證、稽核日誌）

#### 3.3.7 系統管理模組 (SystemManagement)

**模組職責**：管理系統設定、排程、身份驗證、授權、稽核日誌。

**模組結構**：

```
SystemManagement/
├── Domain/
│   ├── Entities/
│   │   ├── User.cs            # 使用者
│   │   ├── Role.cs            # 角色
│   │   ├── Permission.cs      # 權限
│   │   ├── SystemConfiguration.cs
│   │   ├── Schedule.cs        # 排程
│   │   └── AuditLog.cs        # 稽核日誌
│   ├── ValueObjects/
│   │   ├── CronExpression.cs
│   │   ├── ScheduleStatus.cs
│   │   └── UserRole.cs
│   ├── Aggregates/
│   │   ├── UserAggregate.cs
│   │   └── ScheduleAggregate.cs
│   ├── DomainServices/
│   │   ├── AuthenticationService.cs
│   │   ├── AuthorizationService.cs
│   │   └── AuditLogService.cs
│   └── DomainEvents/
│       └── AuditLogCreated.cs
│
├── Application/
│   ├── Commands/
│   │   ├── CreateUserCommand.cs
│   │   ├── UpdateConfigurationCommand.cs
│   │   └── CreateScheduleCommand.cs
│   ├── Queries/
│   │   ├── GetUserQuery.cs
│   │   └── ListAuditLogsQuery.cs
│   └── Services/
│       ├── AuthenticationApplicationService.cs
│       └── AuthorizationApplicationService.cs
│
└── Infrastructure/
    ├── Persistence/
    │   ├── UserRepository.cs
    │   ├── ScheduleRepository.cs
    │   └── SystemManagementDbContext.cs
    ├── Authentication/
    │   └── OidcAuthenticationService.cs
    └── Scheduling/
        └── ScheduleExecutor.cs
```

**對外介面**：
- `IAuthenticationService`：提供身份驗證服務
- `IAuthorizationService`：提供授權服務
- `IAuditLogService`：提供稽核日誌服務
- `IScheduleService`：提供排程管理服務

**依賴關係**：
- 依賴 `SharedKernel`
- 無其他模組依賴（為基礎模組）

#### 3.3.8 共享核心模組 (SharedKernel)

**模組職責**：提供所有模組共用的基礎設施與定義。

**模組結構**：

```
SharedKernel/
├── Common/
│   ├── ValueObjects/          # 共用值物件
│   │   ├── CVE.cs
│   │   ├── CVSS.cs
│   │   └── RiskScore.cs
│   └── Interfaces/            # 共用介面
│       └── IEventBus.cs
│
├── Events/
│   ├── IDomainEvent.cs        # 領域事件介面
│   └── BaseEvent.cs
│
└── Infrastructure/
    ├── Messaging/
    │   ├── EventBus.cs         # 事件匯流排實作
    │   └── MessageQueue.cs
    ├── Logging/
    │   └── StructuredLogger.cs
    └── Monitoring/
        └── HealthCheck.cs
```

#### 3.3.9 模組依賴關係圖

```
                    ┌─────────────────────┐
                    │  SharedKernel       │
                    │  (共享核心)          │
                    └─────────────────────┘
                            ↑
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────┴────────┐  ┌──────┴────────┐  ┌──────┴────────┐
│ SystemMgmt     │  │ AssetMgmt     │  │ ThreatIntel   │
│ (系統管理)      │  │ (資產管理)     │   │ (威脅情資)     │
└───────┬────────┘  └──────┬────────┘  └──────┬────────┘
        │                  │                  │
        │                  └────────┬────────┘
        │                           │
        │                  ┌────────┴────────┐
        │                  │ AnalysisAssess  │
        │                  │ (分析與評估)      │
        │                  └────────┬────────┘
        │                           │
        └───────────────────────────┼───────────┐
                                    │           │
                          ┌─────────┴─────────┐ │
                          │ ReportingNotify   │ │
                          │ (報告與通知)       │ │
                          └───────────────────┘ │
                                                │
                          ┌─────────────────────┘
                          │
                    ┌─────┴─────┐
                    │   Web UI  │
                    │  (Next.js)│
                    └───────────┘
```

**依賴規則**：
- 所有模組依賴 `SharedKernel`
- `SystemManagement` 為基礎模組，不依賴其他業務模組
- `AnalysisAssessment` 依賴 `AssetManagement` 和 `ThreatIntelligence`
- `ReportingNotification` 依賴 `AnalysisAssessment`
- 禁止循環依賴

#### 3.3.10 模組通訊機制

**同步通訊**（服務介面）：
- 透過定義的服務介面（如 `IAssetQueryService`）進行同步呼叫
- 使用依賴注入（Dependency Injection）管理服務實例

**非同步通訊**（事件匯流排）：
- 透過 `IEventBus` 發布與訂閱領域事件
- 使用訊息佇列（如 RabbitMQ 或內建記憶體佇列）實作事件匯流排
- 支援事件持久化與重播

**通訊範例**：

```python
# 資產管理模組發布事件
await event_bus.publish(AssetCreatedEvent(asset_id))

# 分析與評估模組訂閱事件
@event_bus.subscribe(AssetCreatedEvent)
async def handle_asset_created(event: AssetCreatedEvent):
    await perform_association_analysis(event.asset_id)
```

#### 3.3.11 部署結構

**單一應用程式部署**：
- 所有模組編譯為單一可執行檔或 DLL
- 單一資料庫（可依模組劃分 Schema）
- 單一 Web 伺服器實例

**未來演進路徑**：
- 當特定模組需要獨立擴充時，可將其拆分為微服務
- 保持模組間介面不變，僅改變部署方式
- 例如：將 `ThreatIntelligence` 模組拆分為獨立服務，以處理大量威脅收集作業

### 3.4 技術堆疊選擇

本系統的技術堆疊選擇遵循專案憲章 P11 的規範，確保統一技術堆疊以降低維護、安全和人員培訓的複雜性與成本。

#### 3.4.1 前端 UI/UX 技術堆疊

**選擇技術**：
- **框架**：Next.js 14+（App Router）
- **UI 函式庫**：React 18+
- **程式語言**：TypeScript 5+
- **樣式框架**：Tailwind CSS 3+
- **響應式設計**：支援桌面、平板、手機

**選擇理由**：

1. **Next.js 14+**
   - 提供 Server-Side Rendering (SSR) 與 Static Site Generation (SSG)
   - 內建 API Routes，簡化前後端整合
   - 優秀的效能優化（自動程式碼分割、圖片優化）
   - 符合 P1：簡潔優先於複雜

2. **React 18+**
   - 成熟的 UI 函式庫，生態系統豐富
   - 支援 Concurrent Rendering，提升使用者體驗
   - 元件化開發，符合模組化設計

3. **TypeScript**
   - 嚴格型別檢查，符合專案憲章要求（不得使用 any）
   - 提升程式碼可維護性與可讀性
   - 減少執行時錯誤

4. **Tailwind CSS**
   - 原生支援，無需額外配置
   - 快速開發，一致的設計系統
   - 符合 P8：一致的使用者體驗

**在本系統中的應用**：
- Web 管理界面（US-022 ~ US-029）
- 資產清冊管理介面
- 威脅情資檢視與分析介面
- 報告檢視與下載介面
- 系統設定與排程管理介面

#### 3.4.2 後端 API 技術堆疊

**選擇技術**：
- **框架**：ASP.NET Core 8+ WebAPI
- **程式語言**：C# 12
- **ORM**：Entity Framework Core 8+
- **替代方案**：Python 3.10+（僅用於 AI/ML 處理模組）

**選擇理由**：

1. **ASP.NET Core 8+**
   - 高效能、跨平台（Windows、Linux、macOS）
   - 內建依賴注入、中介軟體管道
   - 優秀的 API 開發支援
   - 符合 P10：模組化單體架構

2. **C# 12**
   - 強型別語言，符合嚴格型別要求
   - 優秀的 LINQ 支援，簡化資料查詢
   - 豐富的 .NET 生態系統
   - 良好的非同步程式設計支援（async/await）

3. **Entity Framework Core**
   - Code-First 開發模式
   - 資料庫遷移工具（符合 P12：資料庫變更管理）
   - 支援多種資料庫（SQLite、SQL Server）
   - LINQ 查詢支援

4. **Python（AI/ML 模組）**
   - 豐富的 AI/ML 函式庫（如 transformers、spaCy）
   - 適合 NLP 處理與威脅資訊提取
   - 可作為獨立服務或透過 API 整合

**在本系統中的應用**：
- RESTful API 端點實作
- 領域邏輯與業務規則實作
- 資料持久化與查詢
- 事件匯流排與訊息佇列處理
- AI/NLP 處理（Python 服務）

#### 3.4.3 資料庫技術堆疊

**選擇技術**：
- **開發環境**：SQLite 3.40+
- **生產環境**：MS SQL Server 2022+ 或 SQLite（依規模選擇）

**選擇理由**：

1. **SQLite（開發/小型部署）**
   - 零配置，適合開發與測試
   - 單一檔案資料庫，易於備份與遷移
   - 符合 P1：簡潔優先於複雜
   - 適合初期部署與小型組織

2. **MS SQL Server 2022+（生產/大型部署）**
   - 企業級資料庫，效能與可靠性高
   - 完整的交易支援與並發控制
   - 豐富的管理工具與監控功能
   - 符合 NFR-002：系統容量要求（支援 10,000+ 資產、100,000+ 威脅記錄）

**資料庫架構**：
- 每個模組擁有獨立的 Schema 或資料表前綴
- 使用 Entity Framework Core Migrations 管理 Schema 變更
- 符合 P12：資料庫變更必須透過遷移工具

**在本系統中的應用**：
- 資產清冊資料儲存
- 威脅情資資料儲存
- 風險評估結果儲存
- 報告與通知記錄
- 系統設定與稽核日誌

#### 3.4.4 API 規格

**選擇技術**：
- **API 風格**：RESTful API
- **API 規格**：OpenAPI 3.x（Swagger）
- **API 版本控制**：URL 路徑版本控制（如 `/api/v1/`）

**選擇理由**：

1. **RESTful API**
   - 標準化的 API 設計模式
   - 符合 HTTP 語義，易於理解與使用
   - 良好的快取支援
   - 符合 P1：簡潔優先於複雜

2. **OpenAPI 3.x**
   - 標準化的 API 文件格式
   - 自動生成 API 文件與客戶端程式碼
   - 支援 API 測試與驗證
   - 符合 P3：清晰與可測試性

**API 設計原則**：
- 使用 HTTP 動詞（GET、POST、PUT、DELETE、PATCH）
- 資源導向的 URL 設計（如 `/api/v1/assets`、`/api/v1/threats`）
- 統一的錯誤回應格式
- 支援分頁、排序、篩選

**在本系統中的應用**：
- 資產管理 API（US-001 ~ US-003）
- 威脅情資查詢 API
- 風險評估 API
- 報告生成與查詢 API
- 系統管理 API

#### 3.4.5 緩存技術堆疊

**選擇技術**：
- **緩存系統**：Redis 7.0+

**選擇理由**：

1. **Redis**
   - 高效能的記憶體資料庫
   - 支援多種資料結構（String、Hash、List、Set、Sorted Set）
   - 支援 Pub/Sub，可用於事件匯流排
   - 支援持久化（RDB、AOF）

2. **應用場景**：
   - 威脅情資查詢結果快取
   - 資產清冊快取
   - 會話儲存（Session Storage）
   - 事件匯流排（替代方案）

**在本系統中的應用**：
- 威脅情資查詢快取（減少資料庫查詢）
- 資產清冊快取（提升查詢效能）
- 風險評估結果快取
- 報告生成狀態快取

#### 3.4.6 容器化技術堆疊

**選擇技術**：
- **容器化平台**：Docker
- **容器編排**：Docker Compose（開發環境）

**選擇理由**：

1. **Docker**
   - 標準化的容器化技術
   - 簡化部署與環境配置
   - 支援多階段建置（Multi-stage Build）
   - 符合 P1：簡潔優先於複雜

2. **容器化策略**：
   - 前端應用容器（Next.js）
   - 後端 API 容器（ASP.NET Core）
   - 資料庫容器（SQLite 檔案或 SQL Server）
   - Redis 容器
   - Python AI 服務容器（如需要）

**在本系統中的應用**：
- 開發環境統一配置
- 生產環境部署標準化
- 簡化依賴管理與版本控制
- 支援水平擴充（未來需求）

#### 3.4.7 AI/ML 技術堆疊

**選擇技術**：
- **程式語言**：Python 3.10+
- **NLP 函式庫**：
  - **spaCy**：實體識別與命名實體識別（NER）
  - **transformers**（Hugging Face）：預訓練模型（BERT、GPT）
  - **regex**：正則表達式（CVE 編號識別）
- **API 整合**：透過 RESTful API 與主系統整合

**選擇理由**：

1. **Python**
   - 豐富的 AI/ML 生態系統
   - 適合 NLP 處理與威脅資訊提取
   - 可作為獨立服務，不影響主系統效能

2. **spaCy**
   - 高效能的 NLP 處理
   - 支援多種語言（包含中文）
   - 適合實體識別與資訊提取

3. **transformers**
   - 預訓練模型支援
   - 適合威脅摘要生成
   - 可微調以適應特定領域

**在本系統中的應用**：
- CVE 編號識別（US-009-1）
- 產品名稱與版本資訊提取（US-009-2）
- TTPs 與 IOC 識別（US-009-3, US-009-4）
- 威脅摘要生成（US-015-4）
- 業務風險描述生成（US-015-4）

#### 3.4.8 訊息佇列與事件匯流排

**選擇技術**：
- **主要方案**：內建記憶體事件匯流排（ASP.NET Core）
- **替代方案**：RabbitMQ 或 Redis Pub/Sub（生產環境）

**選擇理由**：

1. **內建記憶體事件匯流排**
   - 簡化開發與測試
   - 符合 P1：簡潔優先於複雜
   - 適合初期部署

2. **RabbitMQ / Redis Pub/Sub**
   - 支援持久化與可靠性
   - 適合生產環境
   - 支援分散式部署

**在本系統中的應用**：
- 領域事件發布與訂閱
- 非同步任務處理
- 模組間非同步通訊

#### 3.4.9 身份驗證與授權

**選擇技術**：
- **身份驗證協議**：OIDC / OAuth 2.0
- **實作方式**：整合現有 IdP（Identity Provider）
- **授權框架**：ASP.NET Core Identity + 自訂 RBAC

**選擇理由**：

1. **OIDC / OAuth 2.0**
   - 標準化的身份驗證協議
   - 符合 P2：設計即安全
   - 支援單一登入 (SSO)

2. **RBAC**
   - 符合 P2：角色基礎存取控制
   - 靈活的權限管理
   - 易於擴充與維護

**在本系統中的應用**：
- 使用者身份驗證（US-022）
- 角色基礎授權（US-023）
- API 端點保護
- 前端路由保護

#### 3.4.10 日誌與監控

**選擇技術**：
- **日誌框架**：Serilog（結構化日誌）
- **日誌格式**：JSON
- **監控框架**：ASP.NET Core Health Checks
- **追蹤框架**：OpenTelemetry（未來擴充）

**選擇理由**：

1. **Serilog**
   - 結構化日誌支援（符合 P13）
   - 豐富的輸出目標（檔案、資料庫、Elasticsearch）
   - 效能優異

2. **Health Checks**
   - 標準化的健康檢查端點
   - 符合 P13：可觀測性要求
   - 支援依賴檢查（資料庫、Redis 等）

**在本系統中的應用**：
- 應用程式日誌記錄
- 錯誤追蹤與診斷
- 效能監控
- 系統健康檢查（`/health` 端點）

#### 3.4.11 技術堆疊總覽表

| 層級 | 技術 | 版本 | 用途 |
|------|------|------|------|
| **前端** | Next.js | 14+ | Web 應用框架 |
| | React | 18+ | UI 函式庫 |
| | TypeScript | 5+ | 程式語言 |
| | Tailwind CSS | 3+ | 樣式框架 |
| **後端** | ASP.NET Core | 8+ | Web API 框架 |
| | C# | 12 | 程式語言 |
| | Entity Framework Core | 8+ | ORM |
| | Python | 3.10+ | AI/ML 處理 |
| **資料庫** | SQLite | 3.40+ | 開發/小型部署 |
| | MS SQL Server | 2022+ | 生產/大型部署 |
| **緩存** | Redis | 7.0+ | 快取系統 |
| **API** | OpenAPI | 3.x | API 規格 |
| **容器化** | Docker | Latest | 容器化平台 |
| **AI/ML** | spaCy | Latest | NLP 處理 |
| | transformers | Latest | 預訓練模型 |
| **日誌** | Serilog | Latest | 結構化日誌 |
| **身份驗證** | OIDC/OAuth 2.0 | - | 身份驗證協議 |

---

## 4. 資料庫設計

本系統的資料庫設計遵循專案憲章 P12 的規範，確保單一事實來源 (SSoT) 與資料庫變更的可追蹤性。所有 Schema 變更必須透過 Entity Framework Core Migrations 以程式碼形式管理。

### 4.1 資料模型

本系統採用**領域驅動設計 (DDD)** 的資料模型，每個有界上下文擁有獨立的資料模型，透過明確的介面進行通訊。

#### 4.1.1 資料模型設計原則

1. **單一事實來源 (SSoT)**
   - 每個資料實體有唯一的「擁有者」模組
   - 禁止跨模組直接存取資料庫
   - 透過應用服務介面進行資料存取

2. **聚合設計**
   - 每個聚合根對應一個主要資料表
   - 聚合內的實體與值物件透過關聯表或內嵌欄位儲存
   - 確保聚合內資料的一致性

3. **資料庫命名規範**
   - 資料表名稱：使用複數形式，PascalCase（如 `Assets`、`Threats`）
   - 欄位名稱：使用 PascalCase（如 `AssetId`、`CreatedAt`）
   - 外鍵命名：`{ReferencedTable}Id`（如 `AssetId`、`ThreatId`）
   - 索引命名：`IX_{TableName}_{ColumnName}`

4. **通用欄位**
   - 所有資料表包含以下通用欄位：
     - `Id`：主鍵（GUID 或整數）
     - `CreatedAt`：建立時間（DateTime）
     - `UpdatedAt`：更新時間（DateTime）
     - `CreatedBy`：建立者（使用者 ID）
     - `UpdatedBy`：更新者（使用者 ID）

#### 4.1.2 資料模型總覽

系統資料模型分為以下模組：

1. **資產管理模組資料模型**
   - `Assets`：資產主表
   - `AssetProducts`：資產產品資訊

2. **威脅情資模組資料模型**
   - `ThreatFeeds`：威脅情資來源
   - `Threats`：威脅主表
   - `ThreatSources`：威脅來源資訊

3. **分析與評估模組資料模型**
   - `PIRs`：優先情資需求
   - `ThreatAssetAssociations`：威脅資產關聯
   - `RiskAssessments`：風險評估

4. **報告與通知模組資料模型**
   - `Reports`：報告主表
   - `NotificationRules`：通知規則
   - `Notifications`：通知記錄

5. **系統管理模組資料模型**
   - `Users`：使用者
   - `Roles`：角色
   - `UserRoles`：使用者角色關聯
   - `Permissions`：權限
   - `RolePermissions`：角色權限關聯
   - `SystemConfigurations`：系統設定
   - `Schedules`：排程
   - `AuditLogs`：稽核日誌

### 4.2 資料庫 Schema

#### 4.2.1 資產管理模組 Schema

**Assets（資產主表）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| Id | GUID (UNIQUEIDENTIFIER) | PK, NOT NULL | 資產唯一識別碼 |
| Item | INT | NULL | 資產項目編號 |
| IP | NVARCHAR(500) | NULL | IP 位址或 IP 範圍 |
| HostName | NVARCHAR(200) | NOT NULL | 主機名稱 |
| OperatingSystem | NVARCHAR(500) | NOT NULL | 作業系統（含版本） |
| RunningApplications | NVARCHAR(MAX) | NOT NULL | 運行的應用程式（含版本） |
| Owner | NVARCHAR(200) | NOT NULL | 負責人 |
| DataSensitivity | NVARCHAR(10) | NOT NULL | 資料敏感度（高/中/低） |
| IsPublicFacing | BIT | NOT NULL | 是否對外暴露（Y/N） |
| BusinessCriticality | NVARCHAR(10) | NOT NULL | 業務關鍵性（高/中/低） |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |
| UpdatedAt | DATETIME2 | NOT NULL | 更新時間 |
| CreatedBy | NVARCHAR(100) | NOT NULL | 建立者 |
| UpdatedBy | NVARCHAR(100) | NOT NULL | 更新者 |

**索引**：
- `IX_Assets_HostName`：主機名稱索引
- `IX_Assets_IsPublicFacing`：對外暴露索引
- `IX_Assets_DataSensitivity`：資料敏感度索引
- `IX_Assets_BusinessCriticality`：業務關鍵性索引

**AssetProducts（資產產品資訊）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| Id | GUID | PK, NOT NULL | 產品資訊唯一識別碼 |
| AssetId | GUID | FK → Assets.Id, NOT NULL | 資產 ID |
| ProductName | NVARCHAR(200) | NOT NULL | 產品名稱（解析後） |
| ProductVersion | NVARCHAR(100) | NULL | 產品版本（解析後） |
| ProductType | NVARCHAR(50) | NULL | 產品類型（OS/Application） |
| OriginalText | NVARCHAR(MAX) | NULL | 原始文字（用於比對） |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |
| UpdatedAt | DATETIME2 | NOT NULL | 更新時間 |

**索引**：
- `IX_AssetProducts_AssetId`：資產 ID 索引
- `IX_AssetProducts_ProductName`：產品名稱索引（用於威脅關聯）

#### 4.2.2 威脅情資模組 Schema

**ThreatFeeds（威脅情資來源）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| Id | GUID | PK, NOT NULL | 來源唯一識別碼 |
| Name | NVARCHAR(100) | NOT NULL, UNIQUE | 來源名稱（CISA KEV、NVD 等） |
| Priority | NVARCHAR(10) | NOT NULL | 優先級（P0/P1/P2/P3） |
| IsEnabled | BIT | NOT NULL | 是否啟用 |
| CollectionFrequency | NVARCHAR(50) | NOT NULL | 收集頻率（每小時/每日/每週） |
| CollectionStrategy | NVARCHAR(MAX) | NULL | 收集策略說明 |
| ApiKey | NVARCHAR(500) | NULL | API 金鑰（加密儲存） |
| LastCollectionTime | DATETIME2 | NULL | 最後收集時間 |
| LastCollectionStatus | NVARCHAR(20) | NULL | 最後收集狀態（Success/Failed） |
| LastCollectionError | NVARCHAR(MAX) | NULL | 最後收集錯誤訊息 |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |
| UpdatedAt | DATETIME2 | NOT NULL | 更新時間 |
| CreatedBy | NVARCHAR(100) | NOT NULL | 建立者 |
| UpdatedBy | NVARCHAR(100) | NOT NULL | 更新者 |

**索引**：
- `IX_ThreatFeeds_Name`：來源名稱索引
- `IX_ThreatFeeds_IsEnabled`：啟用狀態索引
- `IX_ThreatFeeds_Priority`：優先級索引

**Threats（威脅主表）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| Id | GUID | PK, NOT NULL | 威脅唯一識別碼 |
| CVE | NVARCHAR(50) | NULL, UNIQUE | CVE 編號 |
| ThreatFeedId | GUID | FK → ThreatFeeds.Id, NOT NULL | 威脅情資來源 ID |
| Title | NVARCHAR(500) | NOT NULL | 威脅標題 |
| Description | NVARCHAR(MAX) | NULL | 威脅描述 |
| CVSS_BaseScore | DECIMAL(3,1) | NULL | CVSS 基礎分數 |
| CVSS_Vector | NVARCHAR(200) | NULL | CVSS 向量字串 |
| Severity | NVARCHAR(20) | NULL | 嚴重程度（Critical/High/Medium/Low） |
| PublishedDate | DATETIME2 | NULL | 發布日期 |
| AffectedProducts | NVARCHAR(MAX) | NULL | 受影響產品（JSON 格式） |
| ThreatType | NVARCHAR(100) | NULL | 威脅類型（RCE/權限提升等） |
| TTPs | NVARCHAR(MAX) | NULL | TTPs（JSON 格式） |
| IOCs | NVARCHAR(MAX) | NULL | IOCs（JSON 格式） |
| SourceUrl | NVARCHAR(500) | NULL | 來源 URL |
| RawData | NVARCHAR(MAX) | NULL | 原始資料（JSON 格式） |
| Status | NVARCHAR(20) | NOT NULL | 狀態（New/Analyzing/Processed/Closed） |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |
| UpdatedAt | DATETIME2 | NOT NULL | 更新時間 |

**索引**：
- `IX_Threats_CVE`：CVE 編號索引（唯一）
- `IX_Threats_ThreatFeedId`：來源 ID 索引
- `IX_Threats_Status`：狀態索引
- `IX_Threats_CVSS_BaseScore`：CVSS 分數索引
- `IX_Threats_PublishedDate`：發布日期索引

#### 4.2.3 分析與評估模組 Schema

**PIRs（優先情資需求）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| Id | GUID | PK, NOT NULL | PIR 唯一識別碼 |
| Name | NVARCHAR(200) | NOT NULL | PIR 名稱 |
| Description | NVARCHAR(MAX) | NOT NULL | PIR 描述 |
| Priority | NVARCHAR(10) | NOT NULL | 優先級（高/中/低） |
| ConditionType | NVARCHAR(50) | NOT NULL | 條件類型（產品名稱/CVE/威脅類型等） |
| ConditionValue | NVARCHAR(MAX) | NOT NULL | 條件值 |
| IsEnabled | BIT | NOT NULL | 是否啟用 |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |
| UpdatedAt | DATETIME2 | NOT NULL | 更新時間 |
| CreatedBy | NVARCHAR(100) | NOT NULL | 建立者 |
| UpdatedBy | NVARCHAR(100) | NOT NULL | 更新者 |

**索引**：
- `IX_PIRs_IsEnabled`：啟用狀態索引
- `IX_PIRs_Priority`：優先級索引

**ThreatAssetAssociations（威脅資產關聯）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| Id | GUID | PK, NOT NULL | 關聯唯一識別碼 |
| ThreatId | GUID | FK → Threats.Id, NOT NULL | 威脅 ID |
| AssetId | GUID | FK → Assets.Id, NOT NULL | 資產 ID |
| MatchConfidence | DECIMAL(3,2) | NOT NULL | 匹配信心分數（0.0-1.0） |
| MatchType | NVARCHAR(50) | NOT NULL | 匹配類型（Exact/Fuzzy/VersionRange） |
| MatchDetails | NVARCHAR(MAX) | NULL | 匹配詳情（JSON 格式） |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |

**索引**：
- `IX_ThreatAssetAssociations_ThreatId`：威脅 ID 索引
- `IX_ThreatAssetAssociations_AssetId`：資產 ID 索引
- `IX_ThreatAssetAssociations_ThreatId_AssetId`：複合唯一索引（防止重複關聯）

**RiskAssessments（風險評估）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| Id | GUID | PK, NOT NULL | 風險評估唯一識別碼 |
| ThreatId | GUID | FK → Threats.Id, NOT NULL | 威脅 ID |
| ThreatAssetAssociationId | GUID | FK → ThreatAssetAssociations.Id, NOT NULL | 威脅資產關聯 ID |
| BaseCVSSScore | DECIMAL(3,1) | NOT NULL | 基礎 CVSS 分數 |
| AssetImportanceWeight | DECIMAL(3,2) | NOT NULL | 資產重要性加權（1.5/1.0/0.5） |
| AffectedAssetCount | INT | NOT NULL | 受影響資產數量 |
| PIRMatchWeight | DECIMAL(3,2) | NULL | PIR 符合度加權 |
| CisaKeVWeight | DECIMAL(3,2) | NULL | CISA KEV 加權 |
| FinalRiskScore | DECIMAL(4,2) | NOT NULL | 最終風險分數（0.0-10.0） |
| RiskLevel | NVARCHAR(20) | NOT NULL | 風險等級（Critical/High/Medium/Low） |
| CalculationDetails | NVARCHAR(MAX) | NULL | 計算詳情（JSON 格式） |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |
| UpdatedAt | DATETIME2 | NOT NULL | 更新時間 |

**索引**：
- `IX_RiskAssessments_ThreatId`：威脅 ID 索引
- `IX_RiskAssessments_RiskLevel`：風險等級索引
- `IX_RiskAssessments_FinalRiskScore`：風險分數索引

#### 4.2.4 報告與通知模組 Schema

**Reports（報告主表）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| Id | GUID | PK, NOT NULL | 報告唯一識別碼 |
| ReportType | NVARCHAR(50) | NOT NULL | 報告類型（CISO_Weekly/IT_Ticket） |
| Title | NVARCHAR(500) | NOT NULL | 報告標題 |
| FilePath | NVARCHAR(1000) | NOT NULL | 檔案路徑 |
| FileFormat | NVARCHAR(20) | NOT NULL | 檔案格式（HTML/PDF/JSON/TEXT） |
| GeneratedAt | DATETIME2 | NOT NULL | 生成時間 |
| PeriodStart | DATETIME2 | NULL | 報告期間開始 |
| PeriodEnd | DATETIME2 | NULL | 報告期間結束 |
| Summary | NVARCHAR(MAX) | NULL | AI 生成的摘要 |
| Metadata | NVARCHAR(MAX) | NULL | 報告元資料（JSON 格式） |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |

**索引**：
- `IX_Reports_ReportType`：報告類型索引
- `IX_Reports_GeneratedAt`：生成時間索引

**NotificationRules（通知規則）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| Id | GUID | PK, NOT NULL | 通知規則唯一識別碼 |
| NotificationType | NVARCHAR(50) | NOT NULL | 通知類型（Critical/HighRiskDaily/Weekly） |
| IsEnabled | BIT | NOT NULL | 是否啟用 |
| RiskScoreThreshold | DECIMAL(4,2) | NULL | 風險分數閾值 |
| SendTime | TIME | NULL | 發送時間 |
| Recipients | NVARCHAR(MAX) | NOT NULL | 收件人清單（JSON 格式） |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |
| UpdatedAt | DATETIME2 | NOT NULL | 更新時間 |
| CreatedBy | NVARCHAR(100) | NOT NULL | 建立者 |
| UpdatedBy | NVARCHAR(100) | NOT NULL | 更新者 |

**索引**：
- `IX_NotificationRules_NotificationType`：通知類型索引
- `IX_NotificationRules_IsEnabled`：啟用狀態索引

**Notifications（通知記錄）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| Id | GUID | PK, NOT NULL | 通知唯一識別碼 |
| NotificationRuleId | GUID | FK → NotificationRules.Id, NULL | 通知規則 ID |
| NotificationType | NVARCHAR(50) | NOT NULL | 通知類型 |
| Recipients | NVARCHAR(MAX) | NOT NULL | 收件人清單（JSON 格式） |
| Subject | NVARCHAR(500) | NOT NULL | 主旨 |
| Body | NVARCHAR(MAX) | NOT NULL | 內容 |
| SentAt | DATETIME2 | NOT NULL | 發送時間 |
| Status | NVARCHAR(20) | NOT NULL | 狀態（Sent/Failed） |
| ErrorMessage | NVARCHAR(MAX) | NULL | 錯誤訊息 |
| RelatedThreatId | GUID | FK → Threats.Id, NULL | 相關威脅 ID |
| RelatedReportId | GUID | FK → Reports.Id, NULL | 相關報告 ID |

**索引**：
- `IX_Notifications_SentAt`：發送時間索引
- `IX_Notifications_Status`：狀態索引
- `IX_Notifications_RelatedThreatId`：相關威脅 ID 索引

#### 4.2.5 系統管理模組 Schema

**Users（使用者）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| Id | GUID | PK, NOT NULL | 使用者唯一識別碼 |
| SubjectId | NVARCHAR(200) | NOT NULL, UNIQUE | IdP 提供的 Subject ID |
| Email | NVARCHAR(200) | NOT NULL, UNIQUE | Email 地址 |
| DisplayName | NVARCHAR(200) | NOT NULL | 顯示名稱 |
| IsActive | BIT | NOT NULL | 是否啟用 |
| LastLoginAt | DATETIME2 | NULL | 最後登入時間 |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |
| UpdatedAt | DATETIME2 | NOT NULL | 更新時間 |

**索引**：
- `IX_Users_SubjectId`：Subject ID 索引（唯一）
- `IX_Users_Email`：Email 索引（唯一）

**Roles（角色）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| Id | GUID | PK, NOT NULL | 角色唯一識別碼 |
| Name | NVARCHAR(100) | NOT NULL, UNIQUE | 角色名稱（CISO/IT_Admin/Analyst/Viewer） |
| Description | NVARCHAR(500) | NULL | 角色描述 |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |
| UpdatedAt | DATETIME2 | NOT NULL | 更新時間 |

**UserRoles（使用者角色關聯）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| UserId | GUID | FK → Users.Id, PK, NOT NULL | 使用者 ID |
| RoleId | GUID | FK → Roles.Id, PK, NOT NULL | 角色 ID |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |

**Permissions（權限）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| Id | GUID | PK, NOT NULL | 權限唯一識別碼 |
| Name | NVARCHAR(100) | NOT NULL, UNIQUE | 權限名稱 |
| Resource | NVARCHAR(200) | NOT NULL | 資源名稱 |
| Action | NVARCHAR(50) | NOT NULL | 動作（Read/Write/Delete） |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |

**RolePermissions（角色權限關聯）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| RoleId | GUID | FK → Roles.Id, PK, NOT NULL | 角色 ID |
| PermissionId | GUID | FK → Permissions.Id, PK, NOT NULL | 權限 ID |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |

**SystemConfigurations（系統設定）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| Id | GUID | PK, NOT NULL | 設定唯一識別碼 |
| Key | NVARCHAR(200) | NOT NULL, UNIQUE | 設定鍵 |
| Value | NVARCHAR(MAX) | NULL | 設定值 |
| Category | NVARCHAR(100) | NOT NULL | 設定類別 |
| Description | NVARCHAR(500) | NULL | 設定說明 |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |
| UpdatedAt | DATETIME2 | NOT NULL | 更新時間 |
| UpdatedBy | NVARCHAR(100) | NOT NULL | 更新者 |

**索引**：
- `IX_SystemConfigurations_Key`：設定鍵索引（唯一）
- `IX_SystemConfigurations_Category`：設定類別索引

**Schedules（排程）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| Id | GUID | PK, NOT NULL | 排程唯一識別碼 |
| Name | NVARCHAR(200) | NOT NULL | 排程名稱 |
| ScheduleType | NVARCHAR(50) | NOT NULL | 排程類型（ThreatCollection/ReportGeneration） |
| CronExpression | NVARCHAR(100) | NOT NULL | Cron 表達式 |
| IsEnabled | BIT | NOT NULL | 是否啟用 |
| LastRunTime | DATETIME2 | NULL | 最後執行時間 |
| NextRunTime | DATETIME2 | NULL | 下次執行時間 |
| LastRunStatus | NVARCHAR(20) | NULL | 最後執行狀態 |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |
| UpdatedAt | DATETIME2 | NOT NULL | 更新時間 |
| CreatedBy | NVARCHAR(100) | NOT NULL | 建立者 |
| UpdatedBy | NVARCHAR(100) | NOT NULL | 更新者 |

**索引**：
- `IX_Schedules_ScheduleType`：排程類型索引
- `IX_Schedules_IsEnabled`：啟用狀態索引
- `IX_Schedules_NextRunTime`：下次執行時間索引

**AuditLogs（稽核日誌）**

| 欄位名稱 | 資料類型 | 約束 | 說明 |
|---------|---------|------|------|
| Id | GUID | PK, NOT NULL | 稽核日誌唯一識別碼 |
| UserId | GUID | FK → Users.Id, NULL | 使用者 ID |
| Action | NVARCHAR(50) | NOT NULL | 操作類型（Create/Update/Delete/View） |
| ResourceType | NVARCHAR(100) | NOT NULL | 資源類型（Asset/Threat/Report 等） |
| ResourceId | GUID | NULL | 資源 ID |
| Details | NVARCHAR(MAX) | NULL | 操作詳情（JSON 格式） |
| IpAddress | NVARCHAR(50) | NULL | IP 位址 |
| UserAgent | NVARCHAR(500) | NULL | User Agent |
| CreatedAt | DATETIME2 | NOT NULL | 建立時間 |

**索引**：
- `IX_AuditLogs_UserId`：使用者 ID 索引
- `IX_AuditLogs_ResourceType`：資源類型索引
- `IX_AuditLogs_CreatedAt`：建立時間索引（用於時間範圍查詢）
- `IX_AuditLogs_UserId_CreatedAt`：複合索引（使用者操作歷史查詢）

### 4.3 資料遷移策略

#### 4.3.1 Entity Framework Core Migrations

本系統使用 **Entity Framework Core Migrations** 管理資料庫 Schema 變更，符合專案憲章 P12 的規範。

**遷移檔案命名規範**：
- 格式：`{Timestamp}_{MigrationName}`
- 範例：`20241121000001_InitialCreate`、`20241122000001_AddThreatAssetAssociation`

**遷移策略**：

1. **開發環境**
   - 每次 Schema 變更建立新的 Migration
   - 使用 `dotnet ef migrations add {MigrationName}`
   - 自動套用遷移（開發時）

2. **測試環境**
   - 執行所有待處理的 Migration
   - 驗證遷移腳本的正確性
   - 執行資料遷移測試

3. **生產環境**
   - 手動執行 Migration（需審核）
   - 先備份資料庫
   - 在維護視窗執行
   - 驗證遷移結果

#### 4.3.2 資料保留政策

根據需求規格，系統需實作資料保留政策：

1. **威脅記錄**：保留至少 2 年
2. **稽核日誌**：保留至少 2 年（符合 ISO 27001 要求）
3. **報告檔案**：保留至少 2 年
4. **通知記錄**：保留 1 年

**實作方式**：
- 建立排程作業定期清理過期資料
- 使用軟刪除（Soft Delete）標記，而非直接刪除
- 定期備份後再清理

#### 4.3.3 資料備份策略

1. **自動備份**
   - 每日自動備份資料庫
   - 保留最近 30 天的備份
   - 備份檔案加密儲存

2. **災難復原**
   - RTO（復原時間目標）：≤ 4 小時
   - RPO（復原點目標）：≤ 24 小時
   - 定期執行災難復原演練

---

## 5. API 設計

本系統採用 RESTful API 設計，遵循 OpenAPI 3.x 規格，確保 API 的一致性、可測試性與可維護性。

### 5.1 RESTful API 規格

#### 5.1.1 API 設計原則

1. **資源導向設計**
   - 使用名詞表示資源（如 `/api/v1/assets`、`/api/v1/threats`）
   - 使用 HTTP 動詞表示操作（GET、POST、PUT、DELETE、PATCH）

2. **URL 設計規範**
   - 基礎路徑：`/api/v1/`
   - 資源路徑：`/api/v1/{resource}`
   - 資源識別：`/api/v1/{resource}/{id}`
   - 子資源：`/api/v1/{resource}/{id}/{sub-resource}`

3. **HTTP 動詞語義**
   - `GET`：查詢資源（不改變狀態）
   - `POST`：建立新資源
   - `PUT`：完整更新資源
   - `PATCH`：部分更新資源
   - `DELETE`：刪除資源

4. **回應格式**
   - 成功回應：HTTP 200/201/204 + JSON 資料
   - 錯誤回應：HTTP 4xx/5xx + 錯誤訊息 JSON
   - 統一錯誤格式：
     ```json
     {
       "error": {
         "code": "ERROR_CODE",
         "message": "錯誤訊息",
         "details": {}
       }
     }
     ```

5. **分頁與排序**
   - 分頁參數：`?page=1&pageSize=20`
   - 排序參數：`?sortBy=name&sortOrder=asc`
   - 篩選參數：`?filter=field:value`

#### 5.1.2 API 版本控制

- **URL 路徑版本控制**：`/api/v1/`
- 未來版本：`/api/v2/`
- 版本號在 URL 中明確標示，便於管理與演進

#### 5.1.3 OpenAPI 3.x 規格

所有 API 端點必須提供 OpenAPI 3.x 規格文件，包含：
- 端點路徑與 HTTP 方法
- 請求參數與請求體結構
- 回應結構與狀態碼
- 驗證規則與約束條件
- 範例請求與回應

### 5.2 API 端點定義

#### 5.2.1 資產管理 API

**基礎路徑**：`/api/v1/assets`

| HTTP 方法 | 路徑 | 說明 | 對應使用者故事 |
|----------|------|------|---------------|
| GET | `/api/v1/assets` | 查詢資產清冊（支援分頁、排序、篩選） | US-003 |
| GET | `/api/v1/assets/{id}` | 取得單一資產詳情 | US-003 |
| POST | `/api/v1/assets` | 建立新資產 | US-002 |
| PUT | `/api/v1/assets/{id}` | 完整更新資產 | US-002 |
| PATCH | `/api/v1/assets/{id}` | 部分更新資產 | US-002 |
| DELETE | `/api/v1/assets/{id}` | 刪除資產 | US-002 |
| POST | `/api/v1/assets/import` | 匯入資產清冊（CSV） | US-001 |
| GET | `/api/v1/assets/import/preview` | 預覽匯入資料 | US-001 |

**請求/回應範例**：

```http
# 查詢資產清冊
GET /api/v1/assets?page=1&pageSize=20&sortBy=hostName&sortOrder=asc&filter=isPublicFacing:true
```

```json
{
  "data": [
    {
      "id": "guid",
      "item": 1,
      "ip": "10.6.82.31",
      "hostName": "VMware 主機",
      "operatingSystem": "VMware ESXi 7.0.3",
      "runningApplications": "VMware ESXi 7.0.4",
      "owner": "工程師",
      "dataSensitivity": "高",
      "isPublicFacing": false,
      "businessCriticality": "高",
      "createdAt": "2025-11-21T00:00:00Z",
      "updatedAt": "2025-11-21T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalCount": 100,
    "totalPages": 5
  }
}
```

```http
# 建立資產
POST /api/v1/assets
Content-Type: application/json

{
  "item": 1,
  "ip": "10.6.82.31",
  "hostName": "VMware 主機",
  "operatingSystem": "VMware ESXi 7.0.3",
  "runningApplications": "VMware ESXi 7.0.4",
  "owner": "工程師",
  "dataSensitivity": "高",
  "isPublicFacing": false,
  "businessCriticality": "高"
}
```

#### 5.2.2 優先情資需求 (PIR) API

**基礎路徑**：`/api/v1/pirs`

| HTTP 方法 | 路徑 | 說明 | 對應使用者故事 |
|----------|------|------|---------------|
| GET | `/api/v1/pirs` | 查詢 PIR 清單 | US-004 |
| GET | `/api/v1/pirs/{id}` | 取得單一 PIR 詳情 | US-004 |
| POST | `/api/v1/pirs` | 建立新 PIR | US-004 |
| PUT | `/api/v1/pirs/{id}` | 完整更新 PIR | US-004 |
| PATCH | `/api/v1/pirs/{id}` | 部分更新 PIR | US-004 |
| DELETE | `/api/v1/pirs/{id}` | 刪除 PIR | US-004 |
| PATCH | `/api/v1/pirs/{id}/toggle` | 啟用/停用 PIR | US-005 |

**請求/回應範例**：

```http
# 建立 PIR
POST /api/v1/pirs
Content-Type: application/json

{
  "name": "對外暴露威脅",
  "description": "任何影響「對外 (Y)」資產的高風險漏洞",
  "priority": "高",
  "conditionType": "威脅類型 + 資產屬性",
  "conditionValue": "資產屬性：是否對外 = Y; CVSS 分數：> 7.0; 威脅類型：RCE 或 權限提升",
  "isEnabled": true
}
```

#### 5.2.3 威脅情資來源 API

**基礎路徑**：`/api/v1/threat-feeds`

| HTTP 方法 | 路徑 | 說明 | 對應使用者故事 |
|----------|------|------|---------------|
| GET | `/api/v1/threat-feeds` | 查詢威脅情資來源清單 | US-006, US-007 |
| GET | `/api/v1/threat-feeds/{id}` | 取得單一來源詳情 | US-006 |
| POST | `/api/v1/threat-feeds` | 建立新來源訂閱 | US-006 |
| PUT | `/api/v1/threat-feeds/{id}` | 完整更新來源設定 | US-006 |
| PATCH | `/api/v1/threat-feeds/{id}` | 部分更新來源設定 | US-006 |
| DELETE | `/api/v1/threat-feeds/{id}` | 刪除來源訂閱 | US-006 |
| GET | `/api/v1/threat-feeds/{id}/status` | 查詢來源收集狀態 | US-007 |
| POST | `/api/v1/threat-feeds/{id}/collect` | 手動觸發收集作業 | US-008 |

**請求/回應範例**：

```http
# 建立威脅情資來源訂閱
POST /api/v1/threat-feeds
Content-Type: application/json

{
  "name": "CISA KEV",
  "priority": "P0",
  "isEnabled": true,
  "collectionFrequency": "每小時",
  "collectionStrategy": "API / JSON Feed - 最高優先級",
  "apiKey": null
}
```

#### 5.2.4 威脅情資 API

**基礎路徑**：`/api/v1/threats`

| HTTP 方法 | 路徑 | 說明 | 對應使用者故事 |
|----------|------|------|---------------|
| GET | `/api/v1/threats` | 查詢威脅清單（支援分頁、排序、篩選） | US-011 |
| GET | `/api/v1/threats/{id}` | 取得單一威脅詳情 | US-011 |
| GET | `/api/v1/threats/{id}/associations` | 取得威脅的資產關聯 | US-011 |
| GET | `/api/v1/threats/{id}/risk-assessment` | 取得威脅的風險評估 | US-013 |

**請求/回應範例**：

```http
# 查詢威脅清單
GET /api/v1/threats?page=1&pageSize=20&filter=riskLevel:Critical&sortBy=cvssBaseScore&sortOrder=desc
```

```json
{
  "data": [
    {
      "id": "guid",
      "cve": "CVE-2024-12345",
      "title": "Remote Code Execution Vulnerability",
      "cvssBaseScore": 9.8,
      "severity": "Critical",
      "status": "Processed",
      "publishedDate": "2024-11-20T00:00:00Z",
      "riskLevel": "Critical",
      "finalRiskScore": 9.5,
      "affectedAssetCount": 5
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalCount": 150,
    "totalPages": 8
  }
}
```

#### 5.2.5 風險評估 API

**基礎路徑**：`/api/v1/risk-assessments`

| HTTP 方法 | 路徑 | 說明 | 對應使用者故事 |
|----------|------|------|---------------|
| GET | `/api/v1/risk-assessments` | 查詢風險評估清單 | US-013 |
| GET | `/api/v1/risk-assessments/{id}` | 取得單一風險評估詳情 | US-013 |
| GET | `/api/v1/risk-assessments/threat/{threatId}` | 取得威脅的風險評估 | US-013 |
| GET | `/api/v1/risk-assessments/asset/{assetId}` | 取得資產的風險評估 | US-011 |

**請求/回應範例**：

```http
# 取得風險評估詳情
GET /api/v1/risk-assessments/{id}
```

```json
{
  "id": "guid",
  "threatId": "guid",
  "threatAssetAssociationId": "guid",
  "baseCVSSScore": 9.8,
  "assetImportanceWeight": 1.5,
  "affectedAssetCount": 5,
  "pirMatchWeight": 0.3,
  "cisaKeVWeight": 0.5,
  "finalRiskScore": 9.5,
  "riskLevel": "Critical",
  "calculationDetails": {
    "baseScore": 9.8,
    "weightedFactors": {
      "assetImportance": 1.5,
      "affectedAssetCount": 0.5,
      "pirMatch": 0.3,
      "cisaKeV": 0.5
    },
    "finalScore": 9.5
  }
}
```

#### 5.2.6 報告 API

**基礎路徑**：`/api/v1/reports`

| HTTP 方法 | 路徑 | 說明 | 對應使用者故事 |
|----------|------|------|---------------|
| GET | `/api/v1/reports` | 查詢報告清單（支援分頁、篩選） | US-029 |
| GET | `/api/v1/reports/{id}` | 取得單一報告詳情 | US-029 |
| GET | `/api/v1/reports/{id}/download` | 下載報告檔案 | US-029 |
| POST | `/api/v1/reports/generate` | 手動觸發報告生成 | US-015, US-017 |
| GET | `/api/v1/reports/ciso-weekly` | 查詢 CISO 週報清單 | US-029 |
| GET | `/api/v1/reports/it-tickets` | 查詢 IT 工單清單 | US-029 |

**請求/回應範例**：

```http
# 查詢報告清單
GET /api/v1/reports?reportType=CISO_Weekly&page=1&pageSize=10
```

```json
{
  "data": [
    {
      "id": "guid",
      "reportType": "CISO_Weekly",
      "title": "CISO 週報 - 2025-11-21",
      "filePath": "reports/2025/202511/CISO_Weekly_Report_2025-11-21.html",
      "fileFormat": "HTML",
      "generatedAt": "2025-11-21T09:00:00Z",
      "periodStart": "2025-11-14T00:00:00Z",
      "periodEnd": "2025-11-21T00:00:00Z",
      "summary": "本週發現 15 個嚴重威脅..."
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 10,
    "totalCount": 50,
    "totalPages": 5
  }
}
```

#### 5.2.7 通知規則 API

**基礎路徑**：`/api/v1/notification-rules`

| HTTP 方法 | 路徑 | 說明 | 對應使用者故事 |
|----------|------|------|---------------|
| GET | `/api/v1/notification-rules` | 查詢通知規則清單 | US-021 |
| GET | `/api/v1/notification-rules/{id}` | 取得單一通知規則詳情 | US-021 |
| POST | `/api/v1/notification-rules` | 建立新通知規則 | US-021 |
| PUT | `/api/v1/notification-rules/{id}` | 完整更新通知規則 | US-021 |
| PATCH | `/api/v1/notification-rules/{id}` | 部分更新通知規則 | US-021 |
| DELETE | `/api/v1/notification-rules/{id}` | 刪除通知規則 | US-021 |
| PATCH | `/api/v1/notification-rules/{id}/toggle` | 啟用/停用通知規則 | US-021 |

**請求/回應範例**：

```http
# 建立通知規則
POST /api/v1/notification-rules
Content-Type: application/json

{
  "notificationType": "Critical",
  "isEnabled": true,
  "riskScoreThreshold": 8.0,
  "sendTime": null,
  "recipients": ["ciso@example.com", "security@example.com"]
}
```

#### 5.2.8 系統管理 API

**基礎路徑**：`/api/v1/system`

**排程管理 API**：`/api/v1/system/schedules`

| HTTP 方法 | 路徑 | 說明 | 對應使用者故事 |
|----------|------|------|---------------|
| GET | `/api/v1/system/schedules` | 查詢排程清單 | US-025, US-026 |
| GET | `/api/v1/system/schedules/{id}` | 取得單一排程詳情 | US-025 |
| POST | `/api/v1/system/schedules` | 建立新排程 | US-025, US-026 |
| PUT | `/api/v1/system/schedules/{id}` | 完整更新排程 | US-025, US-026 |
| DELETE | `/api/v1/system/schedules/{id}` | 刪除排程 | US-025 |
| POST | `/api/v1/system/schedules/{id}/execute` | 手動觸發排程執行 | US-025, US-026 |

**系統設定 API**：`/api/v1/system/configurations`

| HTTP 方法 | 路徑 | 說明 | 對應使用者故事 |
|----------|------|------|---------------|
| GET | `/api/v1/system/configurations` | 查詢系統設定清單 | US-024 |
| GET | `/api/v1/system/configurations/{key}` | 取得單一設定值 | US-024 |
| PUT | `/api/v1/system/configurations/{key}` | 更新系統設定 | US-024 |

**狀態監控 API**：`/api/v1/system/status`

| HTTP 方法 | 路徑 | 說明 | 對應使用者故事 |
|----------|------|------|---------------|
| GET | `/api/v1/system/status` | 取得系統狀態 | US-027 |
| GET | `/api/v1/system/status/health` | 健康檢查端點 | US-027 |
| GET | `/api/v1/system/status/statistics` | 取得系統統計資訊 | US-028 |

**請求/回應範例**：

```http
# 健康檢查
GET /api/v1/system/status/health
```

```json
{
  "status": "Healthy",
  "checks": {
    "database": "Healthy",
    "redis": "Healthy",
    "externalServices": "Healthy"
  },
  "timestamp": "2025-11-21T10:00:00Z"
}
```

```http
# 取得系統統計資訊
GET /api/v1/system/status/statistics?timeRange=7d
```

```json
{
  "threatCount": 150,
  "criticalThreatCount": 5,
  "highThreatCount": 20,
  "mediumThreatCount": 50,
  "lowThreatCount": 75,
  "affectedAssetCount": 25,
  "riskDistribution": {
    "Critical": 5,
    "High": 20,
    "Medium": 50,
    "Low": 75
  },
  "timeRange": "7d"
}
```

#### 5.2.9 稽核日誌 API

**基礎路徑**：`/api/v1/audit-logs`

| HTTP 方法 | 路徑 | 說明 | 對應使用者故事 |
|----------|------|------|---------------|
| GET | `/api/v1/audit-logs` | 查詢稽核日誌（支援分頁、篩選） | - |
| GET | `/api/v1/audit-logs/{id}` | 取得單一日誌詳情 | - |

**請求/回應範例**：

```http
# 查詢稽核日誌
GET /api/v1/audit-logs?userId=guid&resourceType=Asset&action=Create&startDate=2025-11-01&endDate=2025-11-21&page=1&pageSize=50
```

### 5.3 身份驗證與授權

#### 5.3.1 身份驗證機制

**協議**：OIDC / OAuth 2.0

**實作方式**：
- 整合現有 IdP（Identity Provider）
- 使用 Bearer Token 進行 API 認證
- Token 透過 Authorization Header 傳遞

**認證流程**：

1. **前端登入流程**：
   - 使用者透過前端應用程式點擊登入
   - 前端重定向至 IdP 登入頁面
   - IdP 驗證使用者身份後，重定向回前端並提供授權碼
   - 前端使用授權碼向後端 API 交換 Access Token
   - 後端驗證 Token 並建立使用者會話

2. **API 認證流程**：
   - 前端在每個 API 請求的 Authorization Header 中包含 Access Token
   - 後端驗證 Token 的有效性與簽章
   - 驗證通過後，提取使用者資訊並進行授權檢查

**Token 格式**：
- JWT (JSON Web Token)
- 包含使用者識別碼、角色、權限等資訊
- Token 有效期：1 小時（可設定）

#### 5.3.2 授權機制

**授權模型**：角色基礎存取控制 (RBAC)

**角色定義**：

1. **CISO（資安官）**
   - 完整存取權限
   - 可檢視、設定、管理所有功能

2. **IT_Admin（IT 管理員）**
   - 資產管理：完整權限
   - 威脅情資來源：完整權限
   - 排程管理：完整權限
   - 報告：檢視權限
   - 系統設定：部分權限

3. **Analyst（資安分析師）**
   - 威脅情資：檢視權限
   - 風險評估：檢視權限
   - 報告：檢視權限
   - PIR：檢視權限

4. **Viewer（唯讀使用者）**
   - 所有資源：僅檢視權限
   - 無修改、刪除權限

**授權實作**：

1. **屬性基礎授權 (Attribute-Based Authorization)**
   - 在 Controller 或 Action 上使用 `[Authorize(Roles = "CISO,IT_Admin")]`
   - 在方法層級進行授權檢查

2. **資源基礎授權 (Resource-Based Authorization)**
   - 檢查使用者是否有權限存取特定資源
   - 例如：僅資產負責人可修改該資產

3. **政策基礎授權 (Policy-Based Authorization)**
   - 定義授權政策（Policies）
   - 在需要時檢查政策

**授權檢查範例**：

```python
from fastapi import APIRouter, Depends
from .auth import require_role, get_current_user

router = APIRouter()

@router.post("/api/v1/assets")
@require_role("CISO", "IT_Admin")
async def create_asset(request: CreateAssetRequest, 
                       current_user: User = Depends(get_current_user)):
    """建立資產（需要 CISO 或 IT_Admin 角色）"""
    # 建立資產邏輯
    pass

@router.get("/api/v1/threats")
@require_role("CISO", "IT_Admin", "Analyst")
async def get_threats(query: ThreatQueryRequest,
                      current_user: User = Depends(get_current_user)):
    """查詢威脅（需要 CISO、IT_Admin 或 Analyst 角色）"""
    # 查詢威脅邏輯
    pass
```

#### 5.3.3 API 安全措施

1. **HTTPS 強制**
   - 所有 API 端點必須透過 HTTPS 存取
   - 符合 P2：資料傳輸加密

2. **輸入驗證**
   - 所有輸入參數必須驗證
   - 防止 SQL 注入、XSS 等攻擊
   - 使用 Data Annotations 或 FluentValidation

3. **速率限制 (Rate Limiting)**
   - 防止 API 濫用
   - 每個使用者/IP 限制請求頻率
   - 例如：每分鐘最多 100 個請求

4. **CORS 設定**
   - 僅允許信任的來源存取 API
   - 設定適當的 CORS 政策

5. **錯誤處理**
   - 不洩露敏感資訊（如資料庫錯誤詳情）
   - 統一的錯誤回應格式
   - 記錄所有錯誤以供分析

---

## 6. 模組設計

本章節詳細說明各功能模組的設計與實作細節，包含核心類別、業務邏輯流程、模組間整合方式等。

### 6.1 基礎建設與情資定義模組

#### 6.1.1 模組職責

本模組對應「資產管理上下文」與部分「威脅情資上下文」，負責：
- 內部資產清冊管理（US-001, US-002, US-003）
- 優先情資需求 (PIR) 定義（US-004, US-005）
- 威脅情資來源訂閱管理（US-006, US-007）

#### 6.1.2 核心類別設計

**領域層 (Domain Layer)**

```python
# 聚合根
class Asset:
    """資產聚合根"""
    def __init__(self, id: str, host_name: str, ip: str, operating_system: str,
                 running_applications: str, owner: str, data_sensitivity: str,
                 is_public_facing: bool, business_criticality: str):
        self.id = id
        self.host_name = host_name
        self.ip = ip
        self.operating_system = operating_system
        self.running_applications = running_applications
        self.owner = owner
        self.data_sensitivity = DataSensitivity(data_sensitivity)
        self.is_public_facing = is_public_facing
        self.business_criticality = BusinessCriticality(business_criticality)
        self.products: list[AssetProduct] = []
        self._domain_events: list = []
    
    def update(self, host_name: str, ip: str, **kwargs):
        """更新資產資訊"""
        self.host_name = host_name
        self.ip = ip
        # 更新其他屬性
        for key, value in kwargs.items():
            setattr(self, key, value)
        # 發布領域事件
        self._domain_events.append(AssetUpdatedEvent(self.id))
    
    def add_product(self, product_name: str, product_version: str):
        """新增產品資訊"""
        product = AssetProduct(product_name, product_version)
        self.products.append(product)

# 值物件
class DataSensitivity:
    """資料敏感度值物件"""
    WEIGHTS = {"高": 1.5, "中": 1.0, "低": 0.5}
    
    def __init__(self, value: str):
        self.value = value
        self.weight = self.WEIGHTS.get(value, 1.0)

class BusinessCriticality:
    """業務關鍵性值物件"""
    WEIGHTS = {"高": 1.5, "中": 1.0, "低": 0.5}
    
    def __init__(self, value: str):
        self.value = value
        self.weight = self.WEIGHTS.get(value, 1.0)

class AssetProduct:
    """資產產品資訊"""
    def __init__(self, product_name: str, product_version: str = None):
        self.product_name = product_name
        self.product_version = product_version

# 領域服務
class AssetParsingService:
    """資產解析服務"""
    def parse_products(self, running_applications: str) -> list[AssetProduct]:
        """解析產品名稱與版本"""
        products = []
        # 解析邏輯：支援多種格式
        # 1. 標準格式：產品名稱 版本號
        # 2. 包含版本資訊：產品名稱 (版本資訊)
        # 3. 自行開發系統：保留完整描述
        # ... 實作解析邏輯
        return products
```

**應用層 (Application Layer)**

```python
from pydantic import BaseModel
from typing import Optional
from fastapi import Depends

# 請求模型
class CreateAssetRequest(BaseModel):
    """建立資產請求"""
    host_name: str
    ip: Optional[str] = None
    operating_system: str
    running_applications: str
    owner: str
    data_sensitivity: str
    is_public_facing: bool
    business_criticality: str

# 服務類別
class AssetService:
    """資產服務"""
    def __init__(self, repository, parsing_service, event_bus, audit_log_service):
        self.repository = repository
        self.parsing_service = parsing_service
        self.event_bus = event_bus
        self.audit_log_service = audit_log_service
    
    async def create_asset(self, request: CreateAssetRequest, user_id: str) -> str:
        """建立資產"""
        # 1. 建立資產聚合
        asset_id = str(uuid.uuid4())
        asset = Asset(
            id=asset_id,
            host_name=request.host_name,
            ip=request.ip,
            operating_system=request.operating_system,
            running_applications=request.running_applications,
            owner=request.owner,
            data_sensitivity=request.data_sensitivity,
            is_public_facing=request.is_public_facing,
            business_criticality=request.business_criticality
        )
        
        # 2. 解析產品資訊
        products = self.parsing_service.parse_products(request.running_applications)
        for product in products:
            asset.add_product(product.product_name, product.product_version)
        
        # 3. 儲存
        await self.repository.save(asset)
        
        # 4. 發布事件
        await self.event_bus.publish(AssetCreatedEvent(asset_id))
        
        # 5. 記錄稽核日誌
        await self.audit_log_service.log(user_id, "Create", "Asset", asset_id)
        
        return asset_id

# CSV 匯入服務
class AssetImportService:
    """資產匯入服務"""
    def __init__(self, asset_service, audit_log_service):
        self.asset_service = asset_service
        self.audit_log_service = audit_log_service
    
    async def import_from_csv(self, csv_file, user_id: str) -> dict:
        """從 CSV 匯入資產"""
        import csv
        
        # 1. 解析 CSV
        records = []
        reader = csv.DictReader(csv_file)
        for row in reader:
            records.append(row)
        
        # 2. 驗證資料
        validation_results = self._validate_records(records)
        
        # 3. 批次處理（每批 100 筆）
        results = []
        batch_size = 100
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_results = await self._process_batch(batch, user_id)
            results.extend(batch_results)
        
        # 4. 記錄稽核日誌
        await self.audit_log_service.log(user_id, "Import", "Asset", len(records))
        
        return {
            "total_count": len(records),
            "success_count": sum(1 for r in results if r["success"]),
            "failure_count": sum(1 for r in results if not r["success"])
        }
    
    def _validate_records(self, records: list) -> list:
        """驗證記錄"""
        # 驗證邏輯
        return []
    
    async def _process_batch(self, batch: list, user_id: str) -> list:
        """處理批次"""
        results = []
        for record in batch:
            try:
                request = CreateAssetRequest(**record)
                asset_id = await self.asset_service.create_asset(request, user_id)
                results.append({"success": True, "asset_id": asset_id})
            except Exception as e:
                results.append({"success": False, "error": str(e)})
        return results
```

#### 6.1.3 業務邏輯流程

**資產匯入流程**：

```
1. 使用者上傳 CSV 檔案
   ↓
2. 系統解析 CSV 並驗證格式
   ↓
3. 顯示預覽供使用者確認
   ↓
4. 使用者確認後，批次處理匯入
   ↓
5. 解析產品名稱與版本（AssetParsingService）
   ↓
6. 建立資產聚合並儲存
   ↓
7. 發布 AssetCreated 事件
   ↓
8. 記錄稽核日誌
```

**PIR 管理流程**：

```
1. 使用者建立/更新 PIR
   ↓
2. 驗證 PIR 條件格式
   ↓
3. 儲存 PIR
   ↓
4. 發布 PIRUpdated 事件（通知分析模組）
   ↓
5. 記錄稽核日誌
```

#### 6.1.4 模組間整合

- **發布事件**：`AssetCreated`、`AssetUpdated`、`AssetDeleted`、`PIRUpdated`
- **訂閱事件**：無（本模組為資料來源）
- **提供服務**：`IAssetQueryService`、`IPIRQueryService`

### 6.2 自動化收集與關聯分析模組

#### 6.2.1 模組職責

本模組對應「威脅情資上下文」與「分析與評估上下文」，負責：
- 自動化威脅情資收集（US-008, US-009）
- 威脅與資產關聯分析（US-010, US-011）
- 風險分數計算（US-012, US-013）
- 威脅資料儲存（US-014）

#### 6.2.2 核心類別設計

**領域層 (Domain Layer)**

```python
# 威脅聚合根
class Threat:
    """威脅聚合根"""
    def __init__(self, id: str, cve: str, threat_feed_id: str, title: str,
                 description: str, cvss_base_score: float, status: str):
        self.id = id
        self.cve = cve
        self.threat_feed_id = threat_feed_id
        self.title = title
        self.description = description
        self.cvss_base_score = cvss_base_score
        self.status = status
        self._domain_events: list = []
    
    def update_status(self, new_status: str):
        """更新威脅狀態"""
        self.status = new_status
        self._domain_events.append(ThreatStatusUpdatedEvent(self.id, new_status))

# 風險評估聚合根
class RiskAssessment:
    """風險評估聚合根"""
    def __init__(self, id: str, threat_id: str, threat_asset_association_id: str):
        self.id = id
        self.threat_id = threat_id
        self.threat_asset_association_id = threat_asset_association_id
        self.risk_score: float = 0.0
        self.risk_level: str = ""
        self._domain_events: list = []
    
    def calculate_risk_score(self, base_cvss_score: float, asset_importance_weight: float,
                           affected_asset_count: int, pir_match_weight: float = 0.0,
                           cisa_kev_weight: float = 0.0):
        """計算風險分數"""
        # 風險分數計算邏輯
        final_score = (base_cvss_score * asset_importance_weight +
                      (affected_asset_count / 10.0) * 0.1 +
                      pir_match_weight + cisa_kev_weight)
        
        self.risk_score = min(final_score, 10.0)  # 限制在 0-10 範圍
        self.risk_level = self._determine_risk_level(self.risk_score)
        self._domain_events.append(RiskAssessmentCompletedEvent(self.id, self.threat_id, self.risk_score))
    
    def _determine_risk_level(self, score: float) -> str:
        """決定風險等級"""
        if score >= 8.0:
            return "Critical"
        elif score >= 6.0:
            return "High"
        elif score >= 4.0:
            return "Medium"
        else:
            return "Low"

# 領域服務
class AssociationAnalysisService:
    """關聯分析服務"""
    def analyze(self, threat: Threat, assets: list[Asset]) -> list[dict]:
        """分析威脅與資產的關聯"""
        associations = []
        
        for asset in assets:
            match_result = self._match_threat_to_asset(threat, asset)
            if match_result["is_match"]:
                associations.append({
                    "threat_id": threat.id,
                    "asset_id": asset.id,
                    "confidence": match_result["confidence"],
                    "match_type": match_result["match_type"]
                })
        
        return associations
    
    def _match_threat_to_asset(self, threat: Threat, asset: Asset) -> dict:
        """模糊比對威脅與資產"""
        # 1. 產品名稱比對
        # 2. 版本範圍比對
        # 3. 作業系統比對
        # ... 實作比對邏輯
        return {"is_match": False, "confidence": 0.0, "match_type": ""}

class RiskCalculationService:
    """風險計算服務"""
    def calculate_risk(self, threat: Threat, association: dict, asset: Asset,
                      pirs: list) -> RiskAssessment:
        """計算風險評估"""
        # 1. 基礎 CVSS 分數
        base_score = threat.cvss_base_score
        
        # 2. 資產重要性加權
        asset_weight = (asset.data_sensitivity.weight * 
                       asset.business_criticality.weight)
        
        # 3. 受影響資產數量加權
        asset_count_weight = self._calculate_asset_count_weight(association)
        
        # 4. PIR 符合度加權
        pir_weight = self._check_pir_match(threat, pirs)
        
        # 5. CISA KEV 加權
        cisa_kev_weight = 0.5 if threat.is_in_cisa_kev else 0.0
        
        # 6. 建立風險評估
        risk_assessment = RiskAssessment(
            id=str(uuid.uuid4()),
            threat_id=threat.id,
            threat_asset_association_id=association["id"]
        )
        risk_assessment.calculate_risk_score(
            base_score, asset_weight, 1, pir_weight, cisa_kev_weight
        )
        
        return risk_assessment
    
    def _calculate_asset_count_weight(self, association: dict) -> float:
        """計算資產數量加權"""
        # 實作邏輯
        return 0.0
    
    def _check_pir_match(self, threat: Threat, pirs: list) -> float:
        """檢查 PIR 符合度"""
        # 實作邏輯
        return 0.0
```

**應用層 (Application Layer)**

```python
import asyncio
from typing import List

class ThreatCollectionService:
    """威脅收集服務"""
    def __init__(self, feed_repository, collection_service, threat_repository, event_bus):
        self.feed_repository = feed_repository
        self.collection_service = collection_service
        self.threat_repository = threat_repository
        self.event_bus = event_bus
    
    async def collect_threats(self):
        """收集威脅情資"""
        # 1. 取得啟用的威脅情資來源
        feeds = await self.feed_repository.get_enabled_feeds()
        
        # 2. 並行收集（最多 3 個同時執行）
        semaphore = asyncio.Semaphore(3)
        
        async def collect_feed(feed):
            async with semaphore:
                try:
                    # 收集威脅
                    threats = await self.collection_service.collect(feed)
                    
                    # 儲存威脅
                    for threat in threats:
                        await self.threat_repository.save(threat)
                    
                    # 發布事件
                    await self.event_bus.publish(ThreatCollectedEvent(feed.id, len(threats)))
                except Exception as e:
                    # 記錄錯誤
                    logger.error(f"收集威脅失敗: {e}")
        
        # 並行執行
        tasks = [collect_feed(feed) for feed in feeds]
        await asyncio.gather(*tasks)

class AnalysisService:
    """分析服務"""
    def __init__(self, threat_repository, asset_query_service, analysis_service,
                 risk_service, association_repository, risk_repository,
                 pir_repository, event_bus):
        self.threat_repository = threat_repository
        self.asset_query_service = asset_query_service
        self.analysis_service = analysis_service
        self.risk_service = risk_service
        self.association_repository = association_repository
        self.risk_repository = risk_repository
        self.pir_repository = pir_repository
        self.event_bus = event_bus
    
    async def perform_analysis(self, threat_id: str):
        """執行關聯分析"""
        # 1. 取得待分析的威脅
        threat = await self.threat_repository.get_by_id(threat_id)
        
        # 2. 取得所有資產
        assets = await self.asset_query_service.get_all()
        
        # 3. 執行關聯分析
        associations = self.analysis_service.analyze(threat, assets)
        
        # 4. 儲存關聯並計算風險
        for association in associations:
            association_id = await self.association_repository.save(association)
            association["id"] = association_id
            
            # 5. 計算風險分數
            asset = next(a for a in assets if a.id == association["asset_id"])
            pirs = await self.pir_repository.get_enabled_pirs()
            risk_assessment = self.risk_service.calculate_risk(
                threat, association, asset, pirs
            )
            
            await self.risk_repository.save(risk_assessment)
        
        # 6. 發布事件
        await self.event_bus.publish(RiskAssessmentCompletedEvent(threat_id))
```

#### 6.2.3 業務邏輯流程

**威脅收集流程**：

```
1. 排程觸發收集作業
   ↓
2. 取得啟用的威脅情資來源
   ↓
3. 並行收集（最多 3 個同時執行）
   ↓
4. 呼叫外部 API/RSS/Web 爬蟲
   ↓
5. 解析資料格式並標準化
   ↓
6. AI/NLP 處理非結構化資料（如需要）
   ↓
7. 建立威脅聚合並儲存
   ↓
8. 發布 ThreatCollected 事件
   ↓
9. 觸發關聯分析（訂閱事件）
```

**關聯分析與風險計算流程**：

```
1. 訂閱 ThreatCollected 事件
   ↓
2. 取得威脅詳情
   ↓
3. 取得所有資產（透過 IAssetQueryService）
   ↓
4. 執行關聯分析（模糊比對）
   ↓
5. 儲存威脅資產關聯
   ↓
6. 計算風險分數（考慮多個加權因子）
   ↓
7. 儲存風險評估結果
   ↓
8. 發布 RiskAssessmentCompleted 事件
```

#### 6.2.4 AI/NLP 整合

**威脅資訊提取服務**：

```python
import re
import httpx

class ThreatExtractionService:
    """威脅資訊提取服務"""
    def __init__(self, nlp_service_url: str):
        self.nlp_service_url = nlp_service_url
    
    async def extract(self, raw_text: str) -> dict:
        """提取威脅資訊"""
        # 1. 提取 CVE 編號（正則表達式）
        cve = self._extract_cve(raw_text)
        
        # 2. 呼叫 Python AI 服務提取其他資訊
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.nlp_service_url}/extract",
                json={"text": raw_text}
            )
            result = response.json()
        
        return {
            "cve": cve,
            "products": result.get("products", []),
            "ttps": result.get("ttps", []),
            "iocs": result.get("iocs", []),
            "confidence": result.get("confidence", 0.0)
        }
    
    def _extract_cve(self, text: str) -> str:
        """提取 CVE 編號"""
        pattern = r'CVE-\d{4}-\d{4,7}'
        matches = re.findall(pattern, text)
        return matches[0] if matches else None
```

#### 6.2.5 模組間整合

- **訂閱事件**：`AssetCreated`、`AssetUpdated`（觸發重新分析）
- **發布事件**：`ThreatCollected`、`RiskAssessmentCompleted`
- **使用服務**：`IAssetQueryService`、`IPIRQueryService`
- **提供服務**：`IThreatQueryService`、`IRiskAssessmentService`

### 6.3 報告生成與即時通知模組

#### 6.3.1 模組職責

本模組對應「報告與通知上下文」，負責：
- CISO 週報生成（US-015, US-016）
- IT 工單生成（US-017, US-018）
- 通知規則設定與發送（US-019, US-020, US-021）

#### 6.3.2 核心類別設計

**領域層 (Domain Layer)**

```python
from datetime import datetime
from typing import Optional, List

# 報告聚合根
class Report:
    """報告聚合根"""
    def __init__(self, id: str, report_type: str, title: str, file_path: str,
                 file_format: str, generated_at: datetime):
        self.id = id
        self.report_type = report_type
        self.title = title
        self.file_path = file_path
        self.file_format = file_format
        self.generated_at = generated_at
        self.summary: Optional[str] = None  # AI 生成的摘要
    
    def set_summary(self, summary: str):
        """設定摘要"""
        self.summary = summary

# 通知規則聚合根
class NotificationRule:
    """通知規則聚合根"""
    def __init__(self, id: str, notification_type: str, is_enabled: bool,
                 risk_score_threshold: Optional[float], send_time: Optional[str],
                 recipients: List[str]):
        self.id = id
        self.notification_type = notification_type
        self.is_enabled = is_enabled
        self.risk_score_threshold = risk_score_threshold
        self.send_time = send_time
        self.recipients = recipients
    
    def should_trigger(self, risk_assessment: RiskAssessment) -> bool:
        """檢查是否應該觸發通知"""
        if not self.is_enabled:
            return False
        
        if self.notification_type == "Critical":
            threshold = self.risk_score_threshold or 8.0
            return risk_assessment.risk_score >= threshold
        elif self.notification_type == "HighRiskDaily":
            return risk_assessment.risk_score >= 6.0
        elif self.notification_type == "Weekly":
            return True  # 由排程觸發
        return False

# 領域服務
class ReportGenerationService:
    """報告生成服務"""
    def __init__(self, threat_repository, risk_repository, ai_summary_service):
        self.threat_repository = threat_repository
        self.risk_repository = risk_repository
        self.ai_summary_service = ai_summary_service
    
    async def generate_ciso_weekly_report(self, period_start: datetime,
                                          period_end: datetime) -> Report:
        """生成 CISO 週報"""
        # 1. 收集資料
        threats = await self._get_threats_in_period(period_start, period_end)
        risk_assessments = await self._get_risk_assessments_in_period(period_start, period_end)
        
        # 2. 生成報告內容
        report_content = self._generate_report_content(threats, risk_assessments)
        
        # 3. AI 生成摘要
        summary = await self.ai_summary_service.generate_summary(report_content)
        
        # 4. 生成 HTML/PDF
        file_path = await self._generate_report_file(report_content, "HTML")
        
        # 5. 建立報告聚合
        report = Report(
            id=str(uuid.uuid4()),
            report_type="CISO_Weekly",
            title=f"CISO 週報 - {period_end.strftime('%Y-%m-%d')}",
            file_path=file_path,
            file_format="HTML",
            generated_at=datetime.now()
        )
        report.set_summary(summary)
        
        return report
    
    async def generate_it_ticket(self, risk_assessment: RiskAssessment) -> Report:
        """生成 IT 工單"""
        # 1. 收集技術資訊
        threat = await self.threat_repository.get_by_id(risk_assessment.threat_id)
        assets = await self._get_affected_assets(risk_assessment)
        
        # 2. 生成工單內容
        ticket_content = self._generate_ticket_content(threat, assets, risk_assessment)
        
        # 3. 生成 JSON/TEXT 檔案
        file_path = await self._generate_ticket_file(ticket_content)
        
        # 4. 建立報告聚合
        return Report(
            id=str(uuid.uuid4()),
            report_type="IT_Ticket",
            title=f"IT 工單 - {threat.cve}",
            file_path=file_path,
            file_format="JSON",
            generated_at=datetime.now()
        )

class NotificationService:
    """通知服務"""
    def __init__(self, email_service, notification_repository, event_bus):
        self.email_service = email_service
        self.notification_repository = notification_repository
        self.event_bus = event_bus
    
    async def send_notification(self, rule: NotificationRule, content: dict):
        """發送通知"""
        # 1. 建立通知記錄
        notification = {
            "id": str(uuid.uuid4()),
            "notification_rule_id": rule.id,
            "notification_type": rule.notification_type,
            "recipients": rule.recipients,
            "subject": content["subject"],
            "body": content["body"],
            "sent_at": datetime.now(),
            "status": "Pending"
        }
        
        # 2. 發送通知（Email）
        try:
            await self.email_service.send(
                rule.recipients,
                content["subject"],
                content["body"]
            )
            notification["status"] = "Sent"
        except Exception as e:
            notification["status"] = "Failed"
            notification["error_message"] = str(e)
        
        # 3. 儲存通知記錄
        await self.notification_repository.save(notification)
        
        # 4. 發布事件
        await self.event_bus.publish(NotificationSentEvent(notification["id"]))
```

**應用層 (Application Layer)**

```python
class ReportService:
    """報告服務"""
    def __init__(self, report_generation_service, report_repository, event_bus):
        self.report_generation_service = report_generation_service
        self.report_repository = report_repository
        self.event_bus = event_bus
    
    async def generate_report(self, report_type: str, **kwargs) -> str:
        """生成報告"""
        if report_type == "CISO_Weekly":
            report = await self.report_generation_service.generate_ciso_weekly_report(
                kwargs["period_start"], kwargs["period_end"]
            )
        elif report_type == "IT_Ticket":
            report = await self.report_generation_service.generate_it_ticket(
                kwargs["risk_assessment"]
            )
        else:
            raise ValueError(f"不支援的報告類型: {report_type}")
        
        await self.report_repository.save(report)
        await self.event_bus.publish(ReportGeneratedEvent(report.id))
        
        return report.id

class NotificationService:
    """通知服務"""
    def __init__(self, notification_service, rule_repository):
        self.notification_service = notification_service
        self.rule_repository = rule_repository
    
    async def send_notification_for_risk(self, risk_assessment: RiskAssessment,
                                        notification_type: str):
        """根據風險評估發送通知"""
        # 1. 取得通知規則
        rules = await self.rule_repository.get_enabled_rules(notification_type)
        
        # 2. 檢查是否應該觸發
        for rule in rules:
            if rule.should_trigger(risk_assessment):
                # 3. 生成通知內容
                content = self._generate_notification_content(risk_assessment)
                
                # 4. 發送通知
                await self.notification_service.send_notification(rule, content)
```

#### 6.3.3 業務邏輯流程

**CISO 週報生成流程**：

```
1. 排程觸發（每週一上午 9:00）
   ↓
2. 收集本週威脅情資與風險評估
   ↓
3. 統計分析（威脅數量、風險分布等）
   ↓
4. AI 生成業務風險描述
   ↓
5. 生成 HTML/PDF 報告
   ↓
6. 儲存報告檔案（reports/yyyy/yyyymm/）
   ↓
7. 儲存報告記錄
   ↓
8. 發送 Email 通知收件人
   ↓
9. 發布 ReportGenerated 事件
```

**嚴重威脅即時通知流程**：

```
1. 訂閱 RiskAssessmentCompleted 事件
   ↓
2. 檢查風險分數是否 ≥ 8.0
   ↓
3. 取得啟用的嚴重威脅通知規則
   ↓
4. 生成通知內容
   ↓
5. 發送 Email 通知
   ↓
6. 儲存通知記錄
   ↓
7. 發布 NotificationSent 事件
```

#### 6.3.4 AI 摘要生成

**AI 摘要服務**：

```python
import httpx

class AISummaryService:
    """AI 摘要服務"""
    def __init__(self, nlp_service_url: str):
        self.nlp_service_url = nlp_service_url
    
    async def generate_summary(self, content: str, target_length: int = 200,
                              language: str = "zh-TW", style: str = "executive") -> str:
        """生成摘要"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.nlp_service_url}/summarize",
                json={
                    "content": content,
                    "target_length": target_length,
                    "language": language,
                    "style": style
                }
            )
            result = response.json()
            return result["summary"]
    
    async def generate_business_risk_description(self, threat: Threat) -> str:
        """生成業務風險描述"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.nlp_service_url}/translate-to-business",
                json={"technical_description": threat.description}
            )
            result = response.json()
            return result["description"]
```

#### 6.3.5 模組間整合

- **訂閱事件**：`RiskAssessmentCompleted`（觸發通知）
- **發布事件**：`ReportGenerated`、`NotificationSent`
- **使用服務**：`IRiskAssessmentService`、`IThreatQueryService`
- **提供服務**：`IReportQueryService`

### 6.4 Web 管理界面模組

#### 6.4.1 模組職責

本模組對應「系統管理上下文」與前端 UI，負責：
- 身份驗證與授權（US-022, US-023）
- 系統設定管理（US-024）
- 排程管理（US-025, US-026）
- 狀態監控（US-027, US-028, US-029）

#### 6.4.2 前端架構設計

**技術堆疊**：
- Next.js 14+ (App Router)
- React 18+
- TypeScript 5+
- Tailwind CSS 3+

**專案結構**：

```
frontend/
├── app/                    # Next.js App Router
│   ├── (auth)/            # 身份驗證路由組
│   ├── (dashboard)/       # 儀表板路由組
│   │   ├── assets/        # 資產管理頁面
│   │   ├── threats/       # 威脅情資頁面
│   │   ├── reports/       # 報告頁面
│   │   └── settings/      # 系統設定頁面
│   └── api/               # API Routes（如需要）
│
├── components/            # React 元件
│   ├── ui/               # 基礎 UI 元件
│   ├── forms/            # 表單元件
│   ├── tables/           # 表格元件
│   └── charts/           # 圖表元件
│
├── lib/                   # 工具函式庫
│   ├── api/              # API 客戶端
│   ├── auth/             # 身份驗證
│   └── utils/            # 工具函式
│
└── types/                # TypeScript 型別定義
```

#### 6.4.3 核心功能實作

**身份驗證流程**：

```typescript
// lib/auth/auth.ts
export async function signIn() {
  // 1. 重定向至 IdP 登入頁面
  const authUrl = `${idpUrl}/authorize?client_id=${clientId}&redirect_uri=${redirectUri}`;
  window.location.href = authUrl;
}

export async function handleCallback(code: string) {
  // 2. 使用授權碼交換 Access Token
  const response = await fetch('/api/auth/token', {
    method: 'POST',
    body: JSON.stringify({ code })
  });
  
  const { accessToken } = await response.json();
  
  // 3. 儲存 Token
  localStorage.setItem('accessToken', accessToken);
  
  // 4. 取得使用者資訊
  const user = await getUserInfo(accessToken);
  
  return user;
}
```

**API 客戶端**：

```typescript
// lib/api/client.ts
class ApiClient {
  private baseUrl = '/api/v1';
  private accessToken: string | null = null;
  
  async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const headers = {
      'Content-Type': 'application/json',
      ...(this.accessToken && { Authorization: `Bearer ${this.accessToken}` })
    };
    
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers
    });
    
    if (!response.ok) {
      throw new ApiError(response.status, await response.json());
    }
    
    return response.json();
  }
  
  // 資產管理 API
  async getAssets(params: AssetQueryParams) {
    return this.request<PaginatedResponse<Asset>>('/assets', {
      method: 'GET',
      // 處理查詢參數
    });
  }
  
  async createAsset(data: CreateAssetRequest) {
    return this.request<Asset>('/assets', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
}
```

**表單處理（明確的交易儲存）**：

```typescript
// components/forms/AssetForm.tsx
export function AssetForm() {
  const [formData, setFormData] = useState<AssetFormData>({});
  const [isDirty, setIsDirty] = useState(false);
  
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    // 批次提交變更
    await apiClient.createAsset(formData);
    
    setIsDirty(false);
  };
  
  const handleCancel = () => {
    // 取消變更
    setFormData({});
    setIsDirty(false);
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* 表單欄位 */}
      <div className="flex gap-2">
        <button type="submit" disabled={!isDirty}>
          儲存
        </button>
        <button type="button" onClick={handleCancel} disabled={!isDirty}>
          取消
        </button>
      </div>
    </form>
  );
}
```

#### 6.4.4 後端整合

**身份驗證中介軟體**：

```python
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class AuthenticationMiddleware:
    """身份驗證中介軟體"""
    def __init__(self, token_validator):
        self.token_validator = token_validator
    
    async def __call__(self, request: Request, call_next):
        # 1. 提取 Token
        token = self._extract_token(request)
        if not token:
            raise HTTPException(status_code=401, detail="未提供 Token")
        
        # 2. 驗證 Token 有效性
        principal = await self.token_validator.validate(token)
        if not principal:
            raise HTTPException(status_code=401, detail="Token 無效")
        
        # 3. 設定使用者上下文
        request.state.user = principal
        
        response = await call_next(request)
        return response
    
    def _extract_token(self, request: Request) -> str:
        """從請求中提取 Token"""
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            return authorization[7:]
        return None

# 授權裝飾器
def require_role(*roles: str):
    """角色授權裝飾器"""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user = request.state.user
            if not user or user.role not in roles:
                raise HTTPException(status_code=403, detail="權限不足")
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# 使用範例
@require_role("CISO", "IT_Admin")
async def create_asset(request: CreateAssetRequest, current_user: User):
    """建立資產（需要 CISO 或 IT_Admin 角色）"""
    # 實作邏輯
    pass
```

#### 6.4.5 模組間整合

- **使用服務**：所有其他模組的 API 端點
- **提供服務**：身份驗證、授權、稽核日誌記錄
- **整合方式**：透過 RESTful API 呼叫

---

## 7. AI/ML 整合設計

本系統使用 AI/ML 技術處理非結構化威脅情資、提取關鍵資訊，並生成易於理解的報告摘要。AI/ML 功能以獨立 Python 服務實作，透過 RESTful API 與主系統整合。

### 7.1 NLP 處理架構

#### 7.1.1 AI 服務架構

**設計原則**：
- **獨立服務**：AI/ML 功能以獨立 Python 服務實作，不影響主系統效能
- **RESTful API 整合**：透過 HTTP API 與主系統通訊
- **簡單設計**：使用成熟的 NLP 函式庫，避免過度複雜的模型訓練

**架構圖**：

```
主系統 (FastAPI)
    ↓ HTTP Request
AI/ML 服務 (FastAPI + Python)
    ├── NLP 處理模組
    │   ├── spaCy (實體識別)
    │   ├── transformers (預訓練模型)
    │   └── regex (正則表達式)
    └── 模型管理
        └── 模型載入與快取
```

#### 7.1.2 AI 服務技術堆疊

**核心技術**：
- **框架**：FastAPI（與主系統一致）
- **NLP 函式庫**：
  - **spaCy 3.x**：實體識別、命名實體識別（NER）
  - **transformers**（Hugging Face）：預訓練模型（BERT、GPT）
  - **regex**：正則表達式（CVE 編號識別）

**模型選擇**：
- **中文處理**：spaCy 中文模型（zh_core_web_sm）或 transformers 的中文 BERT 模型
- **摘要生成**：使用 transformers 的 T5 或 GPT 模型
- **實體識別**：spaCy NER 模型

#### 7.1.3 AI 服務 API 設計

**基礎路徑**：`/api/v1/ai`

**主要端點**：

| HTTP 方法 | 路徑 | 說明 |
|----------|------|------|
| POST | `/api/v1/ai/extract` | 提取威脅資訊 |
| POST | `/api/v1/ai/summarize` | 生成摘要 |
| POST | `/api/v1/ai/translate-to-business` | 轉換為業務語言 |
| GET | `/api/v1/ai/health` | 健康檢查 |

**請求/回應範例**：

```python
# 提取威脅資訊
POST /api/v1/ai/extract
Content-Type: application/json

{
  "text": "TWCERT 通報：發現針對 Windows Server 的 CVE-2024-12345 漏洞..."
}

# 回應
{
  "cve": "CVE-2024-12345",
  "products": [
    {"name": "Windows Server", "version": null}
  ],
  "ttps": ["T1566.001", "T1059.001"],
  "iocs": {
    "ips": ["192.168.1.100"],
    "domains": ["malicious.example.com"]
  },
  "confidence": 0.85
}
```

#### 7.1.4 AI 服務實作架構

**專案結構**：

```
ai-service/
├── app/
│   ├── main.py              # FastAPI 應用程式入口
│   ├── models/              # 資料模型
│   │   ├── request.py       # 請求模型
│   │   └── response.py     # 回應模型
│   ├── services/            # 服務層
│   │   ├── nlp_service.py  # NLP 處理服務
│   │   ├── extraction_service.py  # 資訊提取服務
│   │   └── summary_service.py     # 摘要生成服務
│   ├── processors/          # 處理器
│   │   ├── cve_extractor.py
│   │   ├── product_extractor.py
│   │   ├── ttp_extractor.py
│   │   └── ioc_extractor.py
│   └── models/              # ML 模型管理
│       └── model_loader.py
├── requirements.txt
└── Dockerfile
```

**核心服務類別**：

```python
# services/nlp_service.py
import spacy
from transformers import pipeline

class NLPService:
    """NLP 處理服務"""
    def __init__(self):
        # 載入 spaCy 模型
        self.nlp = spacy.load("zh_core_web_sm")
        # 載入 transformers 模型
        self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    
    def extract_entities(self, text: str) -> dict:
        """提取實體"""
        doc = self.nlp(text)
        entities = {
            "products": [],
            "organizations": [],
            "locations": []
        }
        for ent in doc.ents:
            if ent.label_ == "PRODUCT":
                entities["products"].append(ent.text)
        return entities
```

### 7.2 威脅資訊提取

#### 7.2.1 CVE 編號識別

**實作方式**：正則表達式 + 驗證

```python
# processors/cve_extractor.py
import re
from typing import Optional, List

class CVEExtractor:
    """CVE 編號提取器"""
    CVE_PATTERN = r'CVE-\d{4}-\d{4,7}'
    
    def extract(self, text: str) -> Optional[str]:
        """提取 CVE 編號"""
        matches = re.findall(self.CVE_PATTERN, text, re.IGNORECASE)
        if matches:
            # 驗證格式並返回第一個匹配
            return matches[0].upper()
        return None
    
    def extract_all(self, text: str) -> List[str]:
        """提取所有 CVE 編號"""
        matches = re.findall(self.CVE_PATTERN, text, re.IGNORECASE)
        return [m.upper() for m in matches]
```

#### 7.2.2 產品名稱與版本提取

**實作方式**：spaCy NER + 規則匹配

```python
# processors/product_extractor.py
import spacy
import re
from typing import List, Dict

class ProductExtractor:
    """產品名稱與版本提取器"""
    def __init__(self):
        self.nlp = spacy.load("zh_core_web_sm")
        # 常見產品關鍵字
        self.product_keywords = [
            "Windows Server", "VMware", "SQL Server", "Apache", "MySQL",
            "Delphi", "EEP", "Ruby On Rails"
        ]
    
    def extract(self, text: str) -> List[Dict]:
        """提取產品名稱與版本"""
        products = []
        
        # 1. 使用關鍵字匹配
        for keyword in self.product_keywords:
            if keyword.lower() in text.lower():
                version = self._extract_version(text, keyword)
                products.append({
                    "name": keyword,
                    "version": version,
                    "confidence": 0.8
                })
        
        # 2. 使用 spaCy NER（如需要）
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == "PRODUCT":
                version = self._extract_version(text, ent.text)
                products.append({
                    "name": ent.text,
                    "version": version,
                    "confidence": 0.7
                })
        
        return products
    
    def _extract_version(self, text: str, product_name: str) -> Optional[str]:
        """提取版本號"""
        # 版本號模式：v1.0, 1.0, 7.0.3, 2024 等
        version_patterns = [
            rf'{re.escape(product_name)}\s*[vV]?(\d+\.\d+(?:\.\d+)?)',
            rf'{re.escape(product_name)}\s+(\d+\.\d+(?:\.\d+)?)',
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
```

#### 7.2.3 TTPs 識別

**實作方式**：關鍵字匹配 + 規則

```python
# processors/ttp_extractor.py
from typing import List

class TTPExtractor:
    """TTPs 提取器"""
    # MITRE ATT&CK TTP 關鍵字對應
    TTP_KEYWORDS = {
        "T1566.001": ["釣魚", "phishing", "email"],
        "T1059.001": ["命令執行", "command execution", "powershell"],
        "T1078": ["帳號存取", "account access", "credential"],
        "T1021": ["遠端服務", "remote service", "RDP"],
    }
    
    def extract(self, text: str) -> List[str]:
        """提取 TTPs"""
        ttps = []
        text_lower = text.lower()
        
        for ttp_id, keywords in self.TTP_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    ttps.append(ttp_id)
                    break
        
        return list(set(ttps))  # 去重
```

#### 7.2.4 IOC 提取

**實作方式**：正則表達式 + 驗證

```python
# processors/ioc_extractor.py
import re
from typing import Dict, List
from ipaddress import ip_address, AddressValueError

class IOCExtractor:
    """IOC 提取器"""
    IP_PATTERN = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    DOMAIN_PATTERN = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
    HASH_PATTERN = r'\b[a-fA-F0-9]{32,64}\b'  # MD5/SHA256
    
    def extract(self, text: str) -> Dict:
        """提取 IOCs"""
        return {
            "ips": self._extract_ips(text),
            "domains": self._extract_domains(text),
            "hashes": self._extract_hashes(text)
        }
    
    def _extract_ips(self, text: str) -> List[str]:
        """提取 IP 位址"""
        matches = re.findall(self.IP_PATTERN, text)
        valid_ips = []
        for ip in matches:
            try:
                ip_address(ip)  # 驗證 IP 格式
                valid_ips.append(ip)
            except AddressValueError:
                continue
        return list(set(valid_ips))
    
    def _extract_domains(self, text: str) -> List[str]:
        """提取網域"""
        matches = re.findall(self.DOMAIN_PATTERN, text)
        # 過濾常見的誤判（如 email 地址）
        domains = [d for d in matches if not d.endswith('.com') or '@' not in d]
        return list(set(domains))
    
    def _extract_hashes(self, text: str) -> List[str]:
        """提取檔案雜湊值"""
        matches = re.findall(self.HASH_PATTERN, text)
        # 過濾長度符合的雜湊值（MD5: 32, SHA256: 64）
        hashes = [h for h in matches if len(h) in [32, 40, 64]]
        return list(set(hashes))
```

#### 7.2.5 整合提取服務

```python
# services/extraction_service.py
from processors.cve_extractor import CVEExtractor
from processors.product_extractor import ProductExtractor
from processors.ttp_extractor import TTPExtractor
from processors.ioc_extractor import IOCExtractor

class ExtractionService:
    """威脅資訊提取服務"""
    def __init__(self):
        self.cve_extractor = CVEExtractor()
        self.product_extractor = ProductExtractor()
        self.ttp_extractor = TTPExtractor()
        self.ioc_extractor = IOCExtractor()
    
    def extract(self, text: str) -> dict:
        """提取所有威脅資訊"""
        # 1. 提取 CVE 編號
        cve = self.cve_extractor.extract(text)
        
        # 2. 提取產品名稱與版本
        products = self.product_extractor.extract(text)
        
        # 3. 提取 TTPs
        ttps = self.ttp_extractor.extract(text)
        
        # 4. 提取 IOCs
        iocs = self.ioc_extractor.extract(text)
        
        # 5. 計算整體信心分數
        confidence = self._calculate_confidence(cve, products, ttps, iocs)
        
        return {
            "cve": cve,
            "products": products,
            "ttps": ttps,
            "iocs": iocs,
            "confidence": confidence
        }
    
    def _calculate_confidence(self, cve, products, ttps, iocs) -> float:
        """計算信心分數"""
        score = 0.0
        
        if cve:
            score += 0.3
        if products:
            score += 0.3
        if ttps:
            score += 0.2
        if iocs:
            score += 0.2
        
        return min(score, 1.0)
```

#### 7.2.6 API 端點實作

```python
# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from services.extraction_service import ExtractionService

app = FastAPI()
extraction_service = ExtractionService()

class ExtractRequest(BaseModel):
    text: str

class ExtractResponse(BaseModel):
    cve: str | None
    products: list
    ttps: list
    iocs: dict
    confidence: float

@app.post("/api/v1/ai/extract", response_model=ExtractResponse)
async def extract_threat_info(request: ExtractRequest):
    """提取威脅資訊"""
    result = extraction_service.extract(request.text)
    return ExtractResponse(**result)
```

### 7.3 報告摘要生成

#### 7.3.1 摘要生成策略

**使用場景**：
- CISO 週報摘要（US-015-4）
- 威脅摘要（將技術描述轉換為業務語言）

**技術選擇**：
- **摘要模型**：使用 transformers 的 T5 或 BART 模型
- **語言**：支援正體中文
- **風格**：管理層風格（executive style）

#### 7.3.2 摘要生成服務

```python
# services/summary_service.py
from transformers import pipeline
from typing import Optional

class SummaryService:
    """摘要生成服務"""
    def __init__(self):
        # 載入摘要模型（支援中文）
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            device=0 if torch.cuda.is_available() else -1
        )
    
    def generate_summary(self, content: str, target_length: int = 200,
                        language: str = "zh-TW", style: str = "executive") -> str:
        """生成摘要"""
        # 1. 如果內容過長，先分段處理
        if len(content) > 1024:
            chunks = self._split_content(content, max_length=1024)
            summaries = []
            for chunk in chunks:
                summary = self._summarize_chunk(chunk, target_length // len(chunks))
                summaries.append(summary)
            return " ".join(summaries)
        else:
            return self._summarize_chunk(content, target_length)
    
    def _summarize_chunk(self, text: str, max_length: int) -> str:
        """摘要單一區塊"""
        result = self.summarizer(
            text,
            max_length=max_length,
            min_length=max_length // 2,
            do_sample=False
        )
        return result[0]["summary_text"]
    
    def _split_content(self, content: str, max_length: int) -> list:
        """分割內容為多個區塊"""
        chunks = []
        words = content.split()
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) > max_length:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def translate_to_business_language(self, technical_description: str) -> str:
        """將技術描述轉換為業務語言"""
        # 使用提示工程（Prompt Engineering）
        prompt = f"""將以下技術性的資安威脅描述轉換為易於 CISO 和高管理解的業務風險描述：

技術描述：{technical_description}

業務風險描述："""
        
        # 使用 GPT 或 T5 模型生成
        result = self._generate_with_prompt(prompt)
        return result
    
    def _generate_with_prompt(self, prompt: str) -> str:
        """使用提示生成內容"""
        # 實作提示生成邏輯
        # 可以使用 OpenAI API 或本地模型
        pass
```

#### 7.3.3 API 端點實作

```python
# app/main.py (續)
from services.summary_service import SummaryService

summary_service = SummaryService()

class SummarizeRequest(BaseModel):
    content: str
    target_length: int = 200
    language: str = "zh-TW"
    style: str = "executive"

class SummarizeResponse(BaseModel):
    summary: str

@app.post("/api/v1/ai/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    """生成摘要"""
    summary = summary_service.generate_summary(
        request.content,
        request.target_length,
        request.language,
        request.style
    )
    return SummarizeResponse(summary=summary)

class TranslateRequest(BaseModel):
    technical_description: str

class TranslateResponse(BaseModel):
    description: str

@app.post("/api/v1/ai/translate-to-business", response_model=TranslateResponse)
async def translate_to_business(request: TranslateRequest):
    """轉換為業務語言"""
    description = summary_service.translate_to_business_language(
        request.technical_description
    )
    return TranslateResponse(description=description)
```

#### 7.3.4 模型管理與優化

**模型載入策略**：
- 服務啟動時載入模型（避免首次請求延遲）
- 使用模型快取（避免重複載入）
- 支援模型熱更新（不中斷服務）

**效能優化**：
- 使用 GPU 加速（如可用）
- 批次處理多個請求
- 快取常見請求的結果

**錯誤處理**：
- 模型載入失敗時回退到規則基礎方法
- 處理超時與資源限制
- 記錄處理日誌

#### 7.3.5 主系統整合

**主系統呼叫 AI 服務**：

```python
# 在主系統中（威脅情資模組）
import httpx

class ThreatExtractionService:
    """威脅資訊提取服務（主系統端）"""
    def __init__(self, ai_service_url: str):
        self.ai_service_url = ai_service_url
    
    async def extract(self, raw_text: str) -> dict:
        """提取威脅資訊"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.ai_service_url}/api/v1/ai/extract",
                    json={"text": raw_text}
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                # 記錄錯誤並回退到規則基礎方法
                logger.error(f"AI 服務呼叫失敗: {e}")
                return self._fallback_extraction(raw_text)
    
    def _fallback_extraction(self, text: str) -> dict:
        """回退到規則基礎提取"""
        # 僅使用正則表達式提取 CVE
        cve = re.search(r'CVE-\d{4}-\d{4,7}', text)
        return {
            "cve": cve.group(0) if cve else None,
            "products": [],
            "ttps": [],
            "iocs": {},
            "confidence": 0.5
        }
```

#### 7.3.6 AI 服務部署

**容器化配置**：

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式
COPY . .

# 下載 spaCy 模型
RUN python -m spacy download zh_core_web_sm

# 啟動服務
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

**環境變數配置**：
- `MODEL_CACHE_DIR`：模型快取目錄
- `GPU_ENABLED`：是否啟用 GPU
- `MAX_BATCH_SIZE`：最大批次大小

#### 7.3.7 監控與日誌

**AI 服務監控**：
- 處理時間監控
- 模型載入狀態
- 請求成功率
- 資源使用量（CPU、記憶體、GPU）

**日誌記錄**：
- 記錄所有 AI 處理請求（輸入、輸出、處理時間）
- 記錄模型載入與錯誤
- 記錄信心分數分布（用於模型評估）

---

## 8. 測試策略

本系統的測試策略遵循專案憲章 P7 的規範，確保所有新功能具備相應的測試，並達到至少 80% 的單元測試覆蓋率。測試策略包含單元測試、整合測試、端對端測試與效能測試。

### 8.1 單元測試

#### 8.1.1 測試框架與工具

**技術選擇**：
- **測試框架**：pytest 7.0+
- **測試覆蓋率工具**：pytest-cov
- **Mock 工具**：pytest-mock、unittest.mock
- **斷言庫**：pytest 內建斷言

**測試覆蓋率目標**：
- 整體覆蓋率：≥ 80%
- 核心業務邏輯：≥ 90%
- 領域服務：≥ 85%

#### 8.1.2 單元測試範圍

**必須測試的項目**：

1. **領域層 (Domain Layer)**
   - 聚合根的業務邏輯方法
   - 值物件的計算邏輯
   - 領域服務的業務規則

2. **應用層 (Application Layer)**
   - 服務類別的方法
   - 命令處理邏輯
   - 資料驗證邏輯

3. **基礎設施層 (Infrastructure Layer)**
   - Repository 的資料存取邏輯
   - 外部服務整合的封裝
   - 資料轉換邏輯

#### 8.1.3 單元測試範例

**領域層測試**：

```python
# tests/domain/test_asset.py
import pytest
from domain.asset import Asset, DataSensitivity, BusinessCriticality

class TestAsset:
    """資產聚合根測試"""
    
    def test_create_asset(self):
        """測試建立資產"""
        asset = Asset(
            id="test-id",
            host_name="測試主機",
            ip="10.6.82.31",
            operating_system="Windows Server 2016",
            running_applications="SQL Server 2017",
            owner="工程師",
            data_sensitivity="高",
            is_public_facing=False,
            business_criticality="高"
        )
        
        assert asset.id == "test-id"
        assert asset.host_name == "測試主機"
        assert asset.data_sensitivity.weight == 1.5
    
    def test_add_product(self):
        """測試新增產品資訊"""
        asset = Asset(...)
        asset.add_product("SQL Server", "2017")
        
        assert len(asset.products) == 1
        assert asset.products[0].product_name == "SQL Server"
        assert asset.products[0].product_version == "2017"
    
    def test_update_asset(self):
        """測試更新資產"""
        asset = Asset(...)
        asset.update(host_name="新主機名稱", ip="10.6.82.32")
        
        assert asset.host_name == "新主機名稱"
        assert asset.ip == "10.6.82.32"
        assert len(asset._domain_events) == 1

class TestDataSensitivity:
    """資料敏感度值物件測試"""
    
    @pytest.mark.parametrize("value,expected_weight", [
        ("高", 1.5),
        ("中", 1.0),
        ("低", 0.5),
        ("未知", 1.0)
    ])
    def test_weight_calculation(self, value, expected_weight):
        """測試權重計算"""
        sensitivity = DataSensitivity(value)
        assert sensitivity.weight == expected_weight
```

**應用層測試**：

```python
# tests/application/test_asset_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from application.asset_service import AssetService
from application.models import CreateAssetRequest

class TestAssetService:
    """資產服務測試"""
    
    @pytest.fixture
    def mock_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_parsing_service(self):
        return MagicMock()
    
    @pytest.fixture
    def mock_event_bus(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_audit_log(self):
        return AsyncMock()
    
    @pytest.fixture
    def asset_service(self, mock_repository, mock_parsing_service,
                     mock_event_bus, mock_audit_log):
        return AssetService(
            mock_repository,
            mock_parsing_service,
            mock_event_bus,
            mock_audit_log
        )
    
    @pytest.mark.asyncio
    async def test_create_asset(self, asset_service, mock_repository,
                               mock_parsing_service, mock_event_bus):
        """測試建立資產"""
        # 準備測試資料
        request = CreateAssetRequest(
            host_name="測試主機",
            ip="10.6.82.31",
            operating_system="Windows Server 2016",
            running_applications="SQL Server 2017",
            owner="工程師",
            data_sensitivity="高",
            is_public_facing=False,
            business_criticality="高"
        )
        
        # Mock 解析服務
        mock_parsing_service.parse_products.return_value = [
            {"product_name": "SQL Server", "product_version": "2017"}
        ]
        
        # 執行測試
        asset_id = await asset_service.create_asset(request, "user-id")
        
        # 驗證結果
        assert asset_id is not None
        mock_repository.save.assert_called_once()
        mock_event_bus.publish.assert_called_once()
```

**基礎設施層測試**：

```python
# tests/infrastructure/test_asset_repository.py
import pytest
from unittest.mock import AsyncMock
from infrastructure.asset_repository import AssetRepository

class TestAssetRepository:
    """資產 Repository 測試"""
    
    @pytest.fixture
    def mock_db_session(self):
        return AsyncMock()
    
    @pytest.fixture
    def repository(self, mock_db_session):
        return AssetRepository(mock_db_session)
    
    @pytest.mark.asyncio
    async def test_save_asset(self, repository, mock_db_session):
        """測試儲存資產"""
        asset = Asset(...)
        
        await repository.save(asset)
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
```

#### 8.1.4 測試組織結構

**測試目錄結構**：

```
tests/
├── conftest.py              # pytest 配置與共用 fixtures
├── unit/                    # 單元測試
│   ├── domain/             # 領域層測試
│   ├── application/        # 應用層測試
│   └── infrastructure/     # 基礎設施層測試
├── integration/            # 整合測試
├── e2e/                    # 端對端測試
└── performance/            # 效能測試
```

**pytest 配置**：

```python
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    -v
```

#### 8.1.5 測試資料管理

**Fixtures 使用**：
- 使用 pytest fixtures 管理測試資料
- 共用 fixtures 放在 `conftest.py`
- 使用工廠模式建立測試物件

**測試資料隔離**：
- 每個測試使用獨立的測試資料庫
- 使用交易回滾確保測試隔離
- 測試後清理測試資料

### 8.2 整合測試

#### 8.2.1 整合測試範圍

**測試項目**：

1. **API 整合測試**
   - API 端點的功能測試
   - 請求/回應格式驗證
   - 錯誤處理測試

2. **資料庫整合測試**
   - Repository 與資料庫的整合
   - 交易處理
   - 資料遷移測試

3. **外部服務整合測試**
   - 威脅情資來源 API 整合
   - AI 服務整合
   - Email 服務整合

4. **模組間整合測試**
   - 事件發布與訂閱
   - 服務間呼叫
   - 資料流測試

#### 8.2.2 整合測試範例

**API 整合測試**：

```python
# tests/integration/test_asset_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestAssetAPI:
    """資產 API 整合測試"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        # 模擬身份驗證 Token
        return {"Authorization": "Bearer test-token"}
    
    def test_create_asset(self, client, auth_headers):
        """測試建立資產 API"""
        response = client.post(
            "/api/v1/assets",
            json={
                "host_name": "測試主機",
                "ip": "10.6.82.31",
                "operating_system": "Windows Server 2016",
                "running_applications": "SQL Server 2017",
                "owner": "工程師",
                "data_sensitivity": "高",
                "is_public_facing": False,
                "business_criticality": "高"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["host_name"] == "測試主機"
    
    def test_get_assets(self, client, auth_headers):
        """測試查詢資產 API"""
        response = client.get(
            "/api/v1/assets?page=1&pageSize=20",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
```

**資料庫整合測試**：

```python
# tests/integration/test_asset_repository_integration.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from infrastructure.asset_repository import AssetRepository
from domain.asset import Asset

class TestAssetRepositoryIntegration:
    """資產 Repository 整合測試"""
    
    @pytest.fixture
    async def db_session(self):
        # 使用測試資料庫
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            # 建立資料表
            await conn.run_sync(Base.metadata.create_all)
        
        async_session = sessionmaker(engine, class_=AsyncSession)
        async with async_session() as session:
            yield session
            await session.rollback()
    
    @pytest.mark.asyncio
    async def test_save_and_retrieve_asset(self, db_session):
        """測試儲存與查詢資產"""
        repository = AssetRepository(db_session)
        
        # 建立資產
        asset = Asset(...)
        asset_id = await repository.save(asset)
        
        # 查詢資產
        retrieved = await repository.get_by_id(asset_id)
        
        assert retrieved is not None
        assert retrieved.id == asset_id
        assert retrieved.host_name == asset.host_name
```

**事件整合測試**：

```python
# tests/integration/test_event_integration.py
import pytest
from unittest.mock import AsyncMock

class TestEventIntegration:
    """事件整合測試"""
    
    @pytest.mark.asyncio
    async def test_asset_created_event(self):
        """測試資產建立事件發布與訂閱"""
        # 建立事件匯流排
        event_bus = EventBus()
        
        # 訂閱事件
        handler_called = False
        async def handler(event):
            nonlocal handler_called
            handler_called = True
        
        event_bus.subscribe(AssetCreatedEvent, handler)
        
        # 發布事件
        await event_bus.publish(AssetCreatedEvent("asset-id"))
        
        # 驗證處理器被呼叫
        assert handler_called
```

#### 8.2.3 測試環境設定

**測試資料庫**：
- 使用 SQLite 記憶體資料庫（快速、隔離）
- 或使用 Docker 容器化的測試資料庫
- 每個測試使用獨立資料庫實例

**Mock 外部服務**：
- 使用 httpx 的 MockTransport 模擬 HTTP 服務
- 使用 pytest-httpx 模擬外部 API
- 避免在整合測試中呼叫真實外部服務

### 8.3 端對端測試

#### 8.3.1 端對端測試範圍

**測試場景**：

1. **完整使用者流程**
   - 資產匯入流程（US-001）
   - 威脅收集與分析流程（US-008, US-010）
   - 報告生成流程（US-015）
   - 通知發送流程（US-019）

2. **跨模組流程**
   - 資產建立 → 威脅收集 → 關聯分析 → 風險計算 → 報告生成
   - 威脅收集 → 風險評估 → 通知發送

3. **錯誤處理流程**
   - API 錯誤處理
   - 外部服務失敗處理
   - 資料驗證錯誤處理

#### 8.3.2 端對端測試範例

**完整流程測試**：

```python
# tests/e2e/test_threat_analysis_flow.py
import pytest
from fastapi.testclient import TestClient

class TestThreatAnalysisFlow:
    """威脅分析完整流程測試"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def test_asset_id(self, client):
        """建立測試資產"""
        response = client.post(
            "/api/v1/assets",
            json={...},
            headers={"Authorization": "Bearer test-token"}
        )
        return response.json()["id"]
    
    def test_complete_threat_analysis_flow(self, client, test_asset_id):
        """測試完整威脅分析流程"""
        # 1. 建立威脅情資來源
        feed_response = client.post(
            "/api/v1/threat-feeds",
            json={
                "name": "CISA KEV",
                "priority": "P0",
                "is_enabled": True,
                "collection_frequency": "每小時"
            }
        )
        feed_id = feed_response.json()["id"]
        
        # 2. 手動觸發威脅收集
        collect_response = client.post(
            f"/api/v1/threat-feeds/{feed_id}/collect"
        )
        assert collect_response.status_code == 200
        
        # 3. 等待關聯分析完成（模擬非同步處理）
        import time
        time.sleep(1)
        
        # 4. 查詢威脅清單
        threats_response = client.get("/api/v1/threats")
        assert threats_response.status_code == 200
        threats = threats_response.json()["data"]
        assert len(threats) > 0
        
        # 5. 查詢風險評估
        threat_id = threats[0]["id"]
        risk_response = client.get(f"/api/v1/threats/{threat_id}/risk-assessment")
        assert risk_response.status_code == 200
```

#### 8.3.3 端對端測試工具

**測試工具選擇**：
- **API 測試**：FastAPI TestClient
- **瀏覽器測試**：Playwright 或 Cypress（如需要）
- **測試資料準備**：使用 fixtures 與工廠模式

**測試執行策略**：
- 端對端測試在 CI/CD 中執行
- 使用 Docker Compose 啟動完整測試環境
- 測試後自動清理環境

### 8.4 效能測試

#### 8.4.1 效能測試範圍

**測試項目**：

1. **API 回應時間測試**
   - 單一請求回應時間
   - 並發請求處理能力
   - 負載測試

2. **資料庫效能測試**
   - 查詢效能（大量資料）
   - 批次操作效能
   - 索引效能驗證

3. **威脅收集效能測試**
   - 並行收集效能
   - 大量威脅處理能力

4. **報告生成效能測試**
   - 週報生成時間
   - 大量資料報告生成

#### 8.4.2 效能測試範例

**API 效能測試**：

```python
# tests/performance/test_api_performance.py
import pytest
import asyncio
from fastapi.testclient import TestClient
import time

class TestAPIPerformance:
    """API 效能測試"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_asset_list_performance(self, client):
        """測試資產清單查詢效能"""
        # 準備測試資料（1000 筆資產）
        # ...
        
        start_time = time.time()
        response = client.get("/api/v1/assets?page=1&pageSize=20")
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed_time < 2.0  # 符合 NFR-001：2 秒內回應
    
    def test_concurrent_requests(self, client):
        """測試並發請求處理"""
        import concurrent.futures
        
        def make_request():
            return client.get("/api/v1/assets")
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]
        
        elapsed_time = time.time() - start_time
        
        # 驗證所有請求成功
        assert all(r.status_code == 200 for r in results)
        # 驗證總處理時間（10 個並發請求應在合理時間內完成）
        assert elapsed_time < 5.0
```

**資料庫效能測試**：

```python
# tests/performance/test_database_performance.py
import pytest
import time

class TestDatabasePerformance:
    """資料庫效能測試"""
    
    @pytest.mark.asyncio
    async def test_large_dataset_query(self, db_session):
        """測試大量資料查詢效能"""
        # 準備 10,000 筆測試資料
        # ...
        
        repository = AssetRepository(db_session)
        
        start_time = time.time()
        assets = await repository.get_all(page=1, page_size=20)
        elapsed_time = time.time() - start_time
        
        assert len(assets) == 20
        assert elapsed_time < 1.0  # 符合 NFR-001
    
    @pytest.mark.asyncio
    async def test_batch_import_performance(self, db_session):
        """測試批次匯入效能"""
        repository = AssetRepository(db_session)
        
        # 準備 1000 筆資料
        assets = [Asset(...) for _ in range(1000)]
        
        start_time = time.time()
        await repository.batch_save(assets)
        elapsed_time = time.time() - start_time
        
        # 驗證批次匯入時間（符合 AC-001-5：至少 1000 筆）
        assert elapsed_time < 60.0  # 1 分鐘內完成
```

#### 8.4.3 效能測試工具

**工具選擇**：
- **負載測試**：Locust 或 Apache Bench (ab)
- **效能監控**：pytest-benchmark
- **資源監控**：psutil

**效能基準**：
- 根據 spec.md 中的 NFR-001 定義效能基準
- 記錄基準測試結果
- 在 CI/CD 中執行效能回歸測試

#### 8.4.4 效能測試報告

**測試報告內容**：
- 回應時間統計（平均、中位數、P95、P99）
- 吞吐量（每秒請求數）
- 資源使用量（CPU、記憶體）
- 與效能基準的比較

### 8.5 測試自動化

#### 8.5.1 CI/CD 整合

**測試執行策略**：
- **每次提交**：執行單元測試與快速整合測試
- **Pull Request**：執行完整測試套件（單元 + 整合）
- **主分支合併**：執行完整測試套件 + 端對端測試
- **發布前**：執行完整測試套件 + 效能測試

**CI/CD 配置範例**：

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run unit tests
      run: pytest tests/unit --cov=app --cov-report=xml
    
    - name: Run integration tests
      run: pytest tests/integration
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

#### 8.5.2 測試資料管理

**測試資料策略**：
- 使用 fixtures 管理測試資料
- 使用工廠模式建立測試物件
- 測試資料與生產資料完全隔離

**測試資料清理**：
- 每個測試後自動清理
- 使用交易回滾確保隔離
- 定期清理測試資料庫

### 8.6 測試覆蓋率要求

**覆蓋率目標**（符合 NFR-011）：
- **整體覆蓋率**：≥ 80%
- **核心業務邏輯**：≥ 90%
- **領域服務**：≥ 85%
- **API 端點**：100%（所有端點至少有一個測試）

**覆蓋率報告**：
- 使用 pytest-cov 生成覆蓋率報告
- 在 CI/CD 中檢查覆蓋率
- 覆蓋率不足時阻止合併

### 8.7 測試最佳實踐

1. **測試命名**：使用描述性名稱，清楚說明測試目的
2. **測試隔離**：每個測試獨立執行，不依賴其他測試
3. **快速執行**：單元測試應快速執行（< 1 秒）
4. **可維護性**：使用 fixtures 與工廠模式減少重複程式碼
5. **測試資料**：使用最小必要的測試資料
6. **錯誤訊息**：提供清晰的錯誤訊息，便於除錯

---

## 9. 部署計畫

本系統採用容器化部署策略，使用 Docker 進行應用程式封裝與部署，確保環境一致性與部署簡化。部署計畫遵循專案憲章 P11（容器化）與 P13（可觀測性）的規範。

### 9.1 容器化策略

#### 9.1.1 容器架構設計

**容器劃分**：

系統由以下容器組成：

1. **主應用程式容器**（backend）
   - FastAPI 應用程式
   - 所有業務模組
   - 單一容器部署（模組化單體）

2. **前端應用程式容器**（frontend）
   - Next.js 應用程式
   - 靜態資源

3. **AI/ML 服務容器**（ai-service）
   - Python AI 服務
   - NLP 處理功能

4. **資料庫容器**（database）
   - SQLite（開發環境）
   - 或 MS SQL Server（生產環境）

5. **Redis 容器**（cache）
   - 快取服務
   - 事件匯流排（可選）

6. **反向代理容器**（nginx）
   - HTTP/HTTPS 終止
   - 負載平衡（如需要）
   - SSL/TLS 憑證管理

#### 9.1.2 Docker 配置

**主應用程式 Dockerfile**：

```dockerfile
# backend/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式
COPY . .

# 設定環境變數
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 暴露埠號
EXPOSE 8000

# 啟動應用程式
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**前端 Dockerfile**：

```dockerfile
# frontend/Dockerfile
# 建置階段
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# 生產階段
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000

CMD ["node", "server.js"]
```

**AI 服務 Dockerfile**：

```dockerfile
# ai-service/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 下載 spaCy 模型
RUN python -m spacy download zh_core_web_sm

# 複製應用程式
COPY . .

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

#### 9.1.3 Docker Compose 配置

**開發環境配置**：

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/aetim.db
      - REDIS_URL=redis://redis:6379
      - AI_SERVICE_URL=http://ai-service:8001
    volumes:
      - ./backend:/app
      - ./data:/app/data
    depends_on:
      - redis
      - ai-service

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend

  ai-service:
    build: ./ai-service
    ports:
      - "8001:8001"
    environment:
      - MODEL_CACHE_DIR=/app/models
    volumes:
      - ./ai-models:/app/models

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend

volumes:
  redis-data:
```

**生產環境配置**：

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build: ./backend
    restart: always
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
      - AI_SERVICE_URL=http://ai-service:8001
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - redis
      - ai-service
      - database
    networks:
      - aetim-network

  frontend:
    build: ./frontend
    restart: always
    environment:
      - NEXT_PUBLIC_API_URL=${API_URL}
    networks:
      - aetim-network

  ai-service:
    build: ./ai-service
    restart: always
    environment:
      - MODEL_CACHE_DIR=/app/models
      - GPU_ENABLED=${GPU_ENABLED:-false}
    volumes:
      - ai-models:/app/models
    networks:
      - aetim-network

  database:
    image: mcr.microsoft.com/mssql/server:2022-latest
    restart: always
    environment:
      - ACCEPT_EULA=Y
      - SA_PASSWORD=${DB_PASSWORD}
      - MSSQL_PID=Standard
    volumes:
      - db-data:/var/opt/mssql
    networks:
      - aetim-network

  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis-data:/data
    networks:
      - aetim-network

  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    networks:
      - aetim-network

volumes:
  db-data:
  redis-data:
  ai-models:

networks:
  aetim-network:
    driver: bridge
```

#### 9.1.4 多階段建置優化

**優化策略**：
- 使用多階段建置減少映像檔大小
- 分離建置與執行環境
- 快取依賴安裝層

**範例**：

```dockerfile
# 多階段建置範例
FROM python:3.10-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.10-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 9.2 環境配置

#### 9.2.1 環境變數管理

**環境變數分類**：

1. **資料庫配置**
   - `DATABASE_URL`：資料庫連線字串
   - `DB_POOL_SIZE`：連線池大小

2. **Redis 配置**
   - `REDIS_URL`：Redis 連線字串
   - `REDIS_PASSWORD`：Redis 密碼（如需要）

3. **AI 服務配置**
   - `AI_SERVICE_URL`：AI 服務 URL
   - `AI_SERVICE_TIMEOUT`：請求超時時間

4. **身份驗證配置**
   - `OIDC_ISSUER`：IdP Issuer URL
   - `OIDC_CLIENT_ID`：Client ID
   - `OIDC_CLIENT_SECRET`：Client Secret

5. **應用程式配置**
   - `LOG_LEVEL`：日誌級別（DEBUG/INFO/WARN/ERROR）
   - `ENVIRONMENT`：環境名稱（development/staging/production）
   - `API_URL`：API 基礎 URL

6. **安全配置**
   - `SECRET_KEY`：應用程式密鑰
   - `ALLOWED_ORIGINS`：允許的 CORS 來源

**環境變數檔案**：

```bash
# .env.example
# 資料庫
DATABASE_URL=sqlite+aiosqlite:///./data/aetim.db

# Redis
REDIS_URL=redis://localhost:6379

# AI 服務
AI_SERVICE_URL=http://localhost:8001
AI_SERVICE_TIMEOUT=30

# 身份驗證
OIDC_ISSUER=https://idp.example.com
OIDC_CLIENT_ID=aetim-client
OIDC_CLIENT_SECRET=your-secret

# 應用程式
LOG_LEVEL=INFO
ENVIRONMENT=development
API_URL=http://localhost:8000

# 安全
SECRET_KEY=your-secret-key
ALLOWED_ORIGINS=http://localhost:3000
```

#### 9.2.2 配置管理

**配置載入策略**：

```python
# app/config.py
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """應用程式設定"""
    # 資料庫
    database_url: str
    db_pool_size: int = 10
    
    # Redis
    redis_url: str
    redis_password: str | None = None
    
    # AI 服務
    ai_service_url: str
    ai_service_timeout: int = 30
    
    # 身份驗證
    oidc_issuer: str
    oidc_client_id: str
    oidc_client_secret: str
    
    # 應用程式
    log_level: str = "INFO"
    environment: str = "development"
    api_url: str
    
    # 安全
    secret_key: str
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

#### 9.2.3 環境區分

**開發環境**：
- 使用 SQLite 資料庫
- 啟用 DEBUG 日誌
- 使用開發用 IdP
- 關閉 HTTPS（本地開發）

**測試環境**：
- 使用測試資料庫
- 啟用 INFO 日誌
- 使用測試用 IdP
- 啟用 HTTPS

**生產環境**：
- 使用 MS SQL Server
- 啟用 WARN/ERROR 日誌
- 使用生產用 IdP
- 強制 HTTPS
- 啟用所有安全措施

### 9.3 監控與日誌

#### 9.3.1 日誌記錄策略

**結構化日誌實作**（符合 P13）：

```python
# app/logging_config.py
import logging
import json
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    """結構化日誌格式化器"""
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加額外欄位
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        # 添加例外資訊
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)

# 設定日誌
def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
```

**日誌級別使用**：
- **DEBUG**：詳細除錯資訊（僅開發環境）
- **INFO**：一般資訊（操作記錄、請求記錄）
- **WARN**：警告訊息（非關鍵錯誤）
- **ERROR**：錯誤訊息（需要處理的問題）
- **FATAL**：嚴重錯誤（系統無法繼續運作）

#### 9.3.2 健康檢查實作

**健康檢查端點**（符合 P13）：

```python
# app/health.py
from fastapi import APIRouter, status
from typing import Dict
import asyncio

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict:
    """健康檢查端點"""
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # 檢查資料庫
    try:
        await check_database()
        checks["checks"]["database"] = "healthy"
    except Exception as e:
        checks["checks"]["database"] = f"unhealthy: {str(e)}"
        checks["status"] = "unhealthy"
    
    # 檢查 Redis
    try:
        await check_redis()
        checks["checks"]["redis"] = "healthy"
    except Exception as e:
        checks["checks"]["redis"] = f"unhealthy: {str(e)}"
        checks["status"] = "unhealthy"
    
    # 檢查 AI 服務
    try:
        await check_ai_service()
        checks["checks"]["ai_service"] = "healthy"
    except Exception as e:
        checks["checks"]["ai_service"] = f"unhealthy: {str(e)}"
        checks["status"] = "degraded"  # AI 服務失敗不影響主要功能
    
    status_code = status.HTTP_200_OK if checks["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return checks, status_code
```

#### 9.3.3 指標監控

**關鍵效能指標（KPI）端點**：

```python
# app/metrics.py
from fastapi import APIRouter
from typing import Dict

router = APIRouter()

@router.get("/metrics")
async def get_metrics() -> Dict:
    """取得關鍵效能指標"""
    return {
        "threat_collection": {
            "success_rate": 0.95,
            "average_duration": 120.5,
            "total_collected": 1500
        },
        "api": {
            "average_response_time": 0.5,
            "requests_per_minute": 100,
            "error_rate": 0.01
        },
        "database": {
            "query_count": 5000,
            "average_query_time": 0.1
        }
    }
```

**Prometheus 格式指標**（可選）：

```python
# app/prometheus_metrics.py
from prometheus_client import Counter, Histogram, generate_latest

# 定義指標
api_requests_total = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
api_request_duration = Histogram('api_request_duration_seconds', 'API request duration')

@router.get("/metrics/prometheus")
async def prometheus_metrics():
    """Prometheus 格式指標"""
    return Response(generate_latest(), media_type="text/plain")
```

#### 9.3.4 日誌收集與儲存

**日誌收集策略**：

1. **本地日誌檔案**
   - 應用程式日誌寫入本地檔案
   - 日誌輪轉（按大小或時間）
   - 保留最近 30 天的日誌

2. **中央日誌系統**（生產環境）
   - 使用 ELK Stack（Elasticsearch、Logstash、Kibana）
   - 或使用雲端日誌服務（如 AWS CloudWatch）
   - 日誌統一收集與分析

**日誌輪轉配置**：

```python
# 使用 logging.handlers.RotatingFileHandler
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'logs/aetim.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=10
)
handler.setFormatter(StructuredFormatter())
logger.addHandler(handler)
```

#### 9.3.5 分佈式追蹤

**追蹤實作**（符合 P13）：

```python
# app/tracing.py
import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar('request_id', default=None)

class TracingMiddleware:
    """追蹤中介軟體"""
    async def __call__(self, request: Request, call_next):
        # 生成追蹤 ID
        trace_id = str(uuid.uuid4())
        request_id_var.set(trace_id)
        
        # 將追蹤 ID 加入請求標頭
        request.state.trace_id = trace_id
        
        # 記錄請求開始
        logger.info("Request started", extra={
            "trace_id": trace_id,
            "method": request.method,
            "path": request.url.path
        })
        
        # 處理請求
        start_time = time.time()
        response = await call_next(request)
        elapsed_time = time.time() - start_time
        
        # 記錄請求結束
        logger.info("Request completed", extra={
            "trace_id": trace_id,
            "status_code": response.status_code,
            "elapsed_time": elapsed_time
        })
        
        # 將追蹤 ID 加入回應標頭
        response.headers["X-Trace-Id"] = trace_id
        
        return response
```

#### 9.3.6 監控儀表板

**監控項目**：
- 系統健康狀態
- API 回應時間與錯誤率
- 威脅收集成功率
- 資料庫連線狀態
- 資源使用量（CPU、記憶體、磁碟）

**監控工具選擇**：
- **Grafana**：視覺化監控儀表板
- **Prometheus**：指標收集與查詢
- **ELK Stack**：日誌分析

### 9.4 部署流程

#### 9.4.1 部署步驟

**開發環境部署**：

```bash
# 1. 建置映像檔
docker-compose build

# 2. 啟動服務
docker-compose up -d

# 3. 執行資料庫遷移
docker-compose exec backend alembic upgrade head

# 4. 檢查服務狀態
docker-compose ps
docker-compose logs -f
```

**生產環境部署**：

```bash
# 1. 建置映像檔
docker-compose -f docker-compose.prod.yml build

# 2. 停止舊服務
docker-compose -f docker-compose.prod.yml down

# 3. 備份資料庫
docker-compose -f docker-compose.prod.yml exec database \
  /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P $DB_PASSWORD \
  -Q "BACKUP DATABASE aetim TO DISK='/var/opt/mssql/backup/aetim.bak'"

# 4. 啟動新服務
docker-compose -f docker-compose.prod.yml up -d

# 5. 執行資料庫遷移
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 6. 檢查健康狀態
curl http://localhost/health
```

#### 9.4.2 滾動更新策略

**更新策略**：
- 使用 Docker Compose 的滾動更新
- 先更新後端服務
- 再更新前端服務
- 確保服務可用性

**回滾策略**：
- 保留前一個版本的映像檔
- 快速切換回舊版本
- 資料庫遷移支援向下相容

#### 9.4.3 備份與復原

**備份策略**（符合 NFR-003）：

1. **資料庫備份**
   - 每日自動備份
   - 保留最近 30 天的備份
   - 備份檔案加密儲存

2. **應用程式備份**
   - 配置檔案備份
   - 報告檔案備份
   - 日誌檔案備份

**備份腳本範例**：

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d)

# 備份資料庫
docker-compose exec -T database \
  /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P $DB_PASSWORD \
  -Q "BACKUP DATABASE aetim TO DISK='/var/opt/mssql/backup/aetim_${DATE}.bak'"

# 備份報告檔案
tar -czf ${BACKUP_DIR}/reports_${DATE}.tar.gz /app/data/reports

# 備份配置檔案
tar -czf ${BACKUP_DIR}/config_${DATE}.tar.gz /app/config

# 刪除 30 天前的備份
find ${BACKUP_DIR} -name "*.bak" -mtime +30 -delete
find ${BACKUP_DIR} -name "*.tar.gz" -mtime +30 -delete
```

**災難復原計畫**（符合 NFR-003）：
- **RTO（復原時間目標）**：≤ 4 小時
- **RPO（復原點目標）**：≤ 24 小時
- 定期執行災難復原演練

---

## 10. 開發時程

本開發時程基於專案範圍（29 個使用者故事、4 個主要模組）與技術複雜度（AI/ML、DDD、模組化單體）制定。時程規劃遵循專案憲章 P0（規格驅動開發）的原則，採用增量交付方式，確保每個階段都能產出可驗證的價值。

### 10.1 階段劃分

開發時程分為 5 個主要階段，每個階段約 4-6 週，總計約 20-24 週（5-6 個月）。

#### 10.1.1 階段 1：基礎建設與核心功能（4-5 週）

**目標**：建立系統基礎架構與核心資料管理功能

**主要工作項目**：

1. **專案初始化與基礎架構**（1 週）
   - 建立專案結構（模組化單體架構）
   - 設定開發環境（Docker、資料庫、Redis）
   - 建立 CI/CD 流程
   - 設定日誌與監控基礎設施

2. **資料庫設計與實作**（1 週）
   - 實作資料庫 Schema
   - 建立 Entity Framework Core 模型
   - 實作資料庫遷移
   - 建立測試資料

3. **基礎建設與情資定義模組 - 資產管理**（1.5 週）
   - 實作資產領域模型（Domain Layer）
   - 實作資產 Repository（Infrastructure Layer）
   - 實作資產服務（Application Layer）
   - 實作資產 API 端點
   - 實作資產匯入功能（CSV 解析）
   - 實作前端資產管理介面

4. **基礎建設與情資定義模組 - PIR 與威脅來源管理**（1.5 週）
   - 實作 PIR 領域模型與服務
   - 實作威脅情資來源管理
   - 實作 PIR 與威脅來源 API
   - 實作前端管理介面

**交付成果**：
- ✅ 可運行的基礎架構（Docker Compose）
- ✅ 完整的資料庫 Schema
- ✅ 資產管理功能（US-001, US-002, US-003）
- ✅ PIR 管理功能（US-004, US-005）
- ✅ 威脅來源管理功能（US-006, US-007）
- ✅ 單元測試覆蓋率 ≥ 80%

**里程碑**：M1 - 基礎建設完成

---

#### 10.1.2 階段 2：威脅收集與 AI 處理（5-6 週）

**目標**：實作自動化威脅收集與 AI 資訊提取功能

**主要工作項目**：

1. **AI/ML 服務開發**（2 週）
   - 建立 AI 服務專案結構
   - 實作 CVE 編號提取器
   - 實作產品名稱與版本提取器
   - 實作 TTPs 與 IOC 提取器
   - 實作整合提取服務
   - 實作 AI 服務 API
   - 測試與優化 AI 提取準確度

2. **威脅情資收集引擎**（2 週）
   - 實作威脅領域模型
   - 實作威脅收集服務（支援多來源）
   - 實作 CISA KEV 收集器
   - 實作 NVD 收集器
   - 實作 VMware VMSA 收集器
   - 實作 MSRC 收集器
   - 實作 TWCERT 收集器（使用 AI 處理非結構化內容）
   - 實作收集排程與任務管理
   - 實作錯誤處理與重試機制

3. **威脅資料儲存與查詢**（1 週）
   - 實作威脅 Repository
   - 實作威脅 API 端點
   - 實作前端威脅清單與詳細頁面
   - 實作威脅搜尋與篩選功能

4. **整合測試與優化**（1 週）
   - 整合 AI 服務與主系統
   - 端對端測試威脅收集流程
   - 效能測試與優化
   - 錯誤處理完善

**交付成果**：
- ✅ AI/ML 服務（獨立容器）
- ✅ 威脅自動收集功能（US-008）
- ✅ AI 資訊提取功能（US-009）
- ✅ 威脅資料管理功能（US-014）
- ✅ 威脅查詢介面
- ✅ 整合測試通過

**里程碑**：M2 - 威脅收集與 AI 處理完成

---

#### 10.1.3 階段 3：關聯分析與風險計算（4-5 週）

**目標**：實作威脅與資產關聯分析與風險分數計算

**主要工作項目**：

1. **關聯分析引擎**（2 週）
   - 實作關聯分析服務
   - 實作產品名稱比對邏輯（精確與模糊比對）
   - 實作版本範圍比對邏輯
   - 實作威脅-資產關聯建立
   - 實作關聯分析 API
   - 實作前端關聯分析視覺化

2. **風險分數計算引擎**（1.5 週）
   - 實作風險計算服務
   - 實作 CVSS 基礎分數計算
   - 實作加權因子計算（資產重要性、受影響數量、PIR 符合度、CISA KEV）
   - 實作風險分數分類
   - 實作風險計算歷史記錄
   - 實作風險計算 API

3. **風險評估介面**（1 週）
   - 實作前端風險評估顯示
   - 實作風險分數計算詳情頁面
   - 實作風險趨勢分析

4. **測試與優化**（0.5 週）
   - 關聯分析準確度測試
   - 風險計算邏輯驗證
   - 效能測試

**交付成果**：
- ✅ 威脅-資產關聯分析功能（US-010, US-011）
- ✅ 風險分數計算功能（US-012, US-013）
- ✅ 風險評估介面
- ✅ 關聯分析視覺化

**里程碑**：M3 - 關聯分析與風險計算完成

---

#### 10.1.4 階段 4：報告生成與通知（4-5 週）

**目標**：實作報告生成與通知機制

**主要工作項目**：

1. **報告生成服務**（2 週）
   - 實作報告領域模型
   - 實作 CISO 週報生成服務
   - 實作報告模板（HTML、PDF）
   - 實作 AI 摘要生成（整合 AI 服務）
   - 實作報告排程管理
   - 實作報告儲存與查詢

2. **IT 工單生成**（1 週）
   - 實作工單生成服務
   - 實作工單格式（TEXT、JSON）
   - 實作工單匯出功能
   - 實作工單狀態管理

3. **通知機制**（1 週）
   - 實作通知規則管理
   - 實作 Email 通知服務
   - 實作嚴重威脅即時通知
   - 實作每日高風險威脅摘要
   - 實作通知排程

4. **報告與通知介面**（1 週）
   - 實作前端報告管理介面
   - 實作前端通知規則設定介面
   - 實作歷史報告檢視

**交付成果**：
- ✅ CISO 週報生成功能（US-015, US-016）
- ✅ IT 工單生成功能（US-017, US-018）
- ✅ 通知機制（US-019, US-020, US-021）
- ✅ 報告與通知管理介面

**里程碑**：M4 - 報告生成與通知完成

---

#### 10.1.5 階段 5：Web 管理界面與系統整合（4-5 週）

**目標**：完成 Web 管理界面與系統整合功能

**主要工作項目**：

1. **身份驗證與授權**（1.5 週）
   - 實作 OIDC/OAuth 2.0 整合
   - 實作 RBAC 授權機制
   - 實作前端登入介面
   - 實作權限檢查中介軟體

2. **系統管理功能**（1.5 週）
   - 實作系統設定管理
   - 實作排程管理（威脅收集、週報）
   - 實作系統狀態監控介面
   - 實作稽核日誌查詢介面

3. **統計與儀表板**（1 週）
   - 實作威脅統計 API
   - 實作前端儀表板
   - 實作威脅趨勢圖表
   - 實作資產統計

4. **系統整合與優化**（1 週）
   - 端對端測試所有功能
   - 效能優化
   - 安全性檢查
   - 文件整理

**交付成果**：
- ✅ 身份驗證與授權功能（US-022, US-023）
- ✅ 系統管理功能（US-024, US-025, US-026, US-027）
- ✅ 統計與儀表板（US-028, US-029）
- ✅ 完整的系統整合
- ✅ 系統文件

**里程碑**：M5 - 系統完成

---

### 10.2 里程碑

#### 10.2.1 里程碑定義

| 里程碑 | 名稱 | 預期完成時間 | 主要交付成果 |
|--------|------|------------|------------|
| M1 | 基礎建設完成 | 第 4-5 週 | 資產管理、PIR 管理、威脅來源管理 |
| M2 | 威脅收集與 AI 處理完成 | 第 9-11 週 | 威脅自動收集、AI 資訊提取 |
| M3 | 關聯分析與風險計算完成 | 第 13-14 週 | 關聯分析、風險分數計算 |
| M4 | 報告生成與通知完成 | 第 17-18 週 | 週報生成、工單生成、通知機制 |
| M5 | 系統完成 | 第 21-24 週 | 完整系統、文件、部署 |

#### 10.2.2 里程碑驗收標準

**M1 驗收標準**：
- ✅ 所有資產管理功能（US-001, US-002, US-003）通過測試
- ✅ PIR 管理功能（US-004, US-005）通過測試
- ✅ 威脅來源管理功能（US-006, US-007）通過測試
- ✅ 單元測試覆蓋率 ≥ 80%
- ✅ 基礎架構可正常運行

**M2 驗收標準**：
- ✅ 威脅自動收集功能（US-008）通過測試
- ✅ AI 資訊提取功能（US-009）通過測試（準確度 ≥ 80%）
- ✅ 威脅資料儲存功能（US-014）通過測試
- ✅ 至少支援 3 個威脅來源的收集
- ✅ AI 服務可獨立運行

**M3 驗收標準**：
- ✅ 關聯分析功能（US-010, US-011）通過測試
- ✅ 風險分數計算功能（US-012, US-013）通過測試
- ✅ 關聯分析準確度 ≥ 90%
- ✅ 風險分數計算邏輯正確

**M4 驗收標準**：
- ✅ 週報生成功能（US-015, US-016）通過測試
- ✅ 工單生成功能（US-017, US-018）通過測試
- ✅ 通知機制（US-019, US-020, US-021）通過測試
- ✅ 報告格式正確（HTML、PDF）

**M5 驗收標準**：
- ✅ 所有使用者故事（US-001 至 US-029）通過測試
- ✅ 身份驗證與授權功能正常
- ✅ 系統管理功能完整
- ✅ 端對端測試通過
- ✅ 效能測試符合 NFR-001
- ✅ 系統文件完整
- ✅ 部署文件完整

### 10.3 時程風險與緩解措施

#### 10.3.1 主要風險

1. **AI/ML 服務開發延遲**
   - **風險**：AI 資訊提取準確度不足，需要額外調優
   - **影響**：可能延遲 M2 里程碑 1-2 週
   - **緩解措施**：
     - 優先使用規則基礎方法作為回退機制
     - 分階段實作 AI 功能（先實作 CVE 提取，再實作其他功能）
     - 預留額外調優時間

2. **外部 API 整合複雜度**
   - **風險**：威脅來源 API 格式變更或限制
   - **影響**：可能延遲威脅收集功能
   - **緩解措施**：
     - 優先實作標準化 API（如 NVD、CISA KEV）
     - 使用 Mock 服務進行開發
     - 實作錯誤處理與重試機制

3. **效能問題**
   - **風險**：大量資料處理效能不足
   - **影響**：可能無法滿足 NFR-001 要求
   - **緩解措施**：
     - 早期進行效能測試
     - 使用資料庫索引優化查詢
     - 使用 Redis 快取
     - 實作批次處理

4. **測試覆蓋率不足**
   - **風險**：無法達到 80% 測試覆蓋率
   - **影響**：可能延遲交付
   - **緩解措施**：
     - 採用 TDD（測試驅動開發）
     - 每個功能開發時同步撰寫測試
     - 定期檢查覆蓋率

#### 10.3.2 時程緩衝

- **每個階段預留 1 週緩衝時間**：用於處理未預期的問題與優化
- **總時程預留 2-4 週緩衝**：用於系統整合、文件整理與部署準備

### 10.4 資源需求

#### 10.4.1 人力資源

**開發團隊建議配置**：
- **後端開發工程師**：2 人（負責 API、業務邏輯、資料庫）
- **前端開發工程師**：1 人（負責 Web 界面）
- **AI/ML 工程師**：1 人（負責 AI 服務開發）
- **測試工程師**：1 人（負責測試案例撰寫與執行）
- **DevOps 工程師**：0.5 人（負責 CI/CD、部署）

**總計**：約 5.5 人

#### 10.4.2 技術資源

- **開發環境**：Docker、資料庫（SQLite/MS SQL Server）、Redis
- **CI/CD 環境**：GitHub Actions 或類似服務
- **監控工具**：日誌收集系統、監控儀表板
- **測試環境**：獨立的測試資料庫與服務

### 10.5 開發流程

#### 10.5.1 迭代開發流程

每個階段採用 2 週迭代（Sprint）方式：

1. **Sprint 規劃**：定義本迭代要完成的功能
2. **開發**：實作功能與測試
3. **Code Review**：程式碼審查
4. **測試**：單元測試、整合測試
5. **Sprint Review**：展示完成的功能
6. **Retrospective**：檢討與改進

#### 10.5.2 品質保證

- **每日 Stand-up**：同步進度與問題
- **每週進度檢視**：檢查時程與里程碑進度
- **Code Review**：所有程式碼必須經過審查
- **測試驅動**：優先撰寫測試案例
- **文件同步**：開發時同步更新文件

### 10.6 時程甘特圖（概要）

```
週次    1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24
階段1   ████████████
階段2                     ████████████████
階段3                                       ████████████
階段4                                                 ████████████
階段5                                                           ████████████
M1     █
M2               █
M3                         █
M4                                   █
M5                                             █
```

**說明**：
- 每個階段約 4-5 週
- 階段間可能有重疊（部分功能可並行開發）
- 里程碑在階段完成時達成

---

## 11. 風險管理

本專案採用系統化的風險管理方法，識別、評估、應對與監控專案執行過程中可能面臨的風險。風險管理遵循專案憲章 H3（合規要求）的原則，確保專案能夠達成 ISO 27001:2022 A.5.7 合規目標。

### 11.1 風險識別

#### 11.1.1 技術風險

**R-001：AI/ML 資訊提取準確度不足**

- **風險描述**：AI 服務從非結構化內容（如 TWCERT 通報）提取威脅資訊的準確度可能無法達到預期（目標 ≥ 80%），導致威脅資訊遺漏或錯誤。
- **風險類別**：技術風險
- **發生機率**：中（40%）
- **影響程度**：高
- **風險等級**：高
- **影響範圍**：US-009（AI 資訊提取）、威脅收集品質

**R-002：外部威脅來源 API 變更或限制**

- **風險描述**：外部威脅情資來源（CISA KEV、NVD、VMware VMSA、MSRC、TWCERT）可能變更 API 格式、增加速率限制或停止服務，導致威脅收集功能失效。
- **風險類別**：技術風險
- **發生機率**：中（30%）
- **影響程度**：高
- **風險等級**：高
- **影響範圍**：US-008（自動化威脅收集）

**R-003：系統效能無法滿足非功能性需求**

- **風險描述**：系統在處理大量資料（10,000 筆資產、100,000 筆威脅記錄）時，可能無法滿足 NFR-001 的效能要求（API 回應時間 ≤ 2 秒）。
- **風險類別**：技術風險
- **發生機率**：中（35%）
- **影響程度**：中
- **風險等級**：中
- **影響範圍**：NFR-001（效能要求）、使用者體驗

**R-004：資料庫效能瓶頸**

- **風險描述**：隨著威脅記錄累積（2 年保留期間），資料庫查詢效能可能下降，影響系統回應時間。
- **風險類別**：技術風險
- **發生機率**：中（40%）
- **影響程度**：中
- **風險等級**：中
- **影響範圍**：NFR-001（效能要求）、資料查詢功能

**R-005：AI 服務資源消耗過高**

- **風險描述**：AI/ML 服務處理大量非結構化內容時，可能消耗過多 CPU/記憶體資源，影響系統整體效能。
- **風險類別**：技術風險
- **發生機率**：低（25%）
- **影響程度**：中
- **風險等級**：中
- **影響範圍**：系統整體效能、部署成本

#### 11.1.2 安全性風險

**R-006：資料外洩風險**

- **風險描述**：系統儲存敏感的資產資訊與威脅情資，若未妥善保護，可能發生資料外洩，違反 ISO 27001:2022 要求。
- **風險類別**：安全性風險
- **發生機率**：低（20%）
- **影響程度**：極高
- **風險等級**：高
- **影響範圍**：NFR-004（資料加密）、合規要求

**R-007：身份驗證與授權漏洞**

- **風險描述**：OIDC/OAuth 2.0 整合或 RBAC 實作不當，可能導致未授權存取或權限提升。
- **風險類別**：安全性風險
- **發生機率**：低（25%）
- **影響程度**：極高
- **風險等級**：高
- **影響範圍**：US-022（身份驗證）、US-023（授權）、系統安全性

**R-008：輸入驗證不足導致安全漏洞**

- **風險描述**：系統未充分驗證使用者輸入，可能導致 SQL 注入、XSS、CSRF 等安全漏洞。
- **風險類別**：安全性風險
- **發生機率**：中（30%）
- **影響程度**：高
- **風險等級**：高
- **影響範圍**：NFR-006（輸入驗證）、系統安全性

#### 11.1.3 專案管理風險

**R-009：開發時程延遲**

- **風險描述**：由於技術複雜度、需求變更或資源不足，專案可能無法在預期時程（20-24 週）內完成。
- **風險類別**：專案管理風險
- **發生機率**：中（40%）
- **影響程度**：中
- **風險等級**：中
- **影響範圍**：專案交付時程、資源配置

**R-010：關鍵人員離職或不可用**

- **風險描述**：關鍵開發人員（特別是 AI/ML 工程師）離職或長期不可用，可能影響專案進度。
- **風險類別**：專案管理風險
- **發生機率**：低（20%）
- **影響程度**：高
- **風險等級**：中
- **影響範圍**：專案進度、技術知識傳承

**R-011：需求變更或範圍擴張**

- **風險描述**：專案執行過程中，利害關係人提出新的需求或變更現有需求，可能導致範圍擴張與時程延遲。
- **風險類別**：專案管理風險
- **發生機率**：中（35%）
- **影響程度**：中
- **風險等級**：中
- **影響範圍**：專案範圍、時程、資源

#### 11.1.4 合規風險

**R-012：無法達成 ISO 27001:2022 A.5.7 合規要求**

- **風險描述**：系統實作可能無法完全滿足 ISO 27001:2022 A.5.7（威脅情資）控制要求，導致合規失敗。
- **風險類別**：合規風險
- **發生機率**：低（25%）
- **影響程度**：極高
- **風險等級**：高
- **影響範圍**：專案目標、合規認證

**R-013：稽核日誌不完整或可篡改**

- **風險描述**：稽核日誌實作不完整或缺乏防篡改機制，可能無法滿足 NFR-005 要求，影響合規審計。
- **風險類別**：合規風險
- **發生機率**：低（20%）
- **影響程度**：高
- **風險等級**：中
- **影響範圍**：NFR-005（稽核日誌）、合規審計

#### 11.1.5 運維風險

**R-014：系統可用性無法達到 99%**

- **風險描述**：系統可能因硬體故障、軟體錯誤或外部服務中斷，無法達到 NFR-003 的可用性要求（99%）。
- **風險類別**：運維風險
- **發生機率**：中（30%）
- **影響程度**：中
- **風險等級**：中
- **影響範圍**：NFR-003（可用性）、服務品質

**R-015：備份與復原機制失效**

- **風險描述**：備份機制可能失效或復原程序不當，導致資料遺失或無法在 RTO/RPO 時間內復原。
- **風險類別**：運維風險
- **發生機率**：低（20%）
- **影響程度**：高
- **風險等級**：中
- **影響範圍**：NFR-003（災難復原）、資料安全

### 11.2 風險評估

#### 11.2.1 風險等級定義

**風險等級計算**：風險等級 = 發生機率 × 影響程度

| 風險等級 | 說明 | 應對策略 |
|---------|------|---------|
| **極高** | 必須立即處理，可能導致專案失敗 | 避免或減輕 |
| **高** | 需要積極應對，可能造成重大影響 | 減輕或轉移 |
| **中** | 需要監控與管理，可能造成中等影響 | 減輕或接受 |
| **低** | 可接受，持續監控即可 | 接受 |

#### 11.2.2 風險矩陣

| 影響程度 | 極高 | 高 | 中 | 低 |
|---------|------|-----|-----|-----|
| **極高** | 極高 | 極高 | 高 | 中 |
| **高** | 極高 | 高 | 高 | 中 |
| **中** | 高 | 高 | 中 | 低 |
| **低** | 中 | 中 | 低 | 低 |

**機率定義**：
- 極高：≥ 60%
- 高：40-59%
- 中：20-39%
- 低：< 20%

**影響程度定義**：
- 極高：導致專案失敗或無法達成核心目標
- 高：造成重大延遲或功能缺失
- 中：造成中等延遲或部分功能受影響
- 低：造成輕微延遲或影響有限

### 11.3 風險應對策略

#### 11.3.1 高風險應對策略

**R-001：AI/ML 資訊提取準確度不足**

- **應對策略**：減輕（Mitigate）
- **具體措施**：
  1. **分階段實作**：優先實作規則基礎方法（CVE 編號、產品名稱提取），確保基本功能可用
  2. **回退機制**：AI 服務失敗時自動回退到規則基礎方法
  3. **準確度監控**：實作準確度監控機制，持續追蹤提取結果
  4. **人工審核**：對低信心分數（< 0.7）的提取結果進行人工審核
  5. **模型優化**：預留時間進行模型調優與訓練
- **負責人**：AI/ML 工程師
- **監控指標**：提取準確度、信心分數分布、回退次數

**R-002：外部威脅來源 API 變更或限制**

- **應對策略**：減輕（Mitigate）
- **具體措施**：
  1. **標準化介面**：建立標準化的資料收集介面，隔離外部 API 變更影響
  2. **Mock 服務**：開發時使用 Mock 服務，減少對外部 API 的依賴
  3. **錯誤處理**：實作完善的錯誤處理與重試機制
  4. **監控告警**：監控 API 呼叫狀態，異常時立即告警
  5. **備用方案**：準備手動匯入機制作為備用方案
- **負責人**：後端開發工程師
- **監控指標**：API 呼叫成功率、錯誤率、重試次數

**R-006：資料外洩風險**

- **應對策略**：減輕（Mitigate）
- **具體措施**：
  1. **資料加密**：實作完整的資料加密機制（at-rest 與 in-transit）
  2. **存取控制**：嚴格實作 RBAC，確保最小權限原則
  3. **安全審計**：定期進行安全審計與滲透測試
  4. **資料分類**：對敏感資料進行分類標記與保護
  5. **安全培訓**：對開發團隊進行安全開發培訓
- **負責人**：全體開發團隊、DevOps 工程師
- **監控指標**：安全審計結果、存取日誌異常、資料外洩事件

**R-007：身份驗證與授權漏洞**

- **應對策略**：減輕（Mitigate）
- **具體措施**：
  1. **使用成熟框架**：使用經過驗證的 OIDC/OAuth 2.0 函式庫
  2. **安全審計**：進行身份驗證與授權邏輯的安全審計
  3. **滲透測試**：定期進行滲透測試，發現潛在漏洞
  4. **最小權限**：嚴格實作最小權限原則
  5. **日誌監控**：監控異常登入與權限使用行為
- **負責人**：後端開發工程師、安全審計人員
- **監控指標**：異常登入次數、權限提升嘗試、安全審計結果

**R-008：輸入驗證不足導致安全漏洞**

- **應對策略**：減輕（Mitigate）
- **具體措施**：
  1. **使用框架驗證**：使用 Pydantic 等框架進行輸入驗證
  2. **安全檢查清單**：建立安全開發檢查清單（OWASP Top 10）
  3. **程式碼審查**：所有程式碼必須經過安全審查
  4. **自動化掃描**：使用 SAST/DAST 工具進行自動化安全掃描
  5. **安全測試**：進行專門的安全測試（SQL 注入、XSS 等）
- **負責人**：全體開發團隊
- **監控指標**：安全掃描結果、漏洞數量、修復時間

**R-012：無法達成 ISO 27001:2022 A.5.7 合規要求**

- **應對策略**：避免（Avoid）
- **具體措施**：
  1. **需求對齊**：確保所有需求與 ISO 27001:2022 A.5.7 控制要求對齊
  2. **合規檢查**：在每個里程碑進行合規檢查
  3. **專家諮詢**：邀請合規專家進行審查與指導
  4. **文件完整**：確保所有合規相關文件完整
  5. **測試驗證**：進行合規測試，驗證控制實作
- **負責人**：專案負責人、系統分析師
- **監控指標**：合規檢查結果、控制實作完成度

#### 11.3.2 中風險應對策略

**R-003：系統效能無法滿足非功能性需求**

- **應對策略**：減輕（Mitigate）
- **具體措施**：
  1. **早期效能測試**：在開發早期進行效能測試
  2. **效能基準**：建立效能基準並持續監控
  3. **優化措施**：使用資料庫索引、Redis 快取、批次處理等優化措施
  4. **負載測試**：進行負載測試，驗證系統在預期負載下的效能
- **負責人**：後端開發工程師、測試工程師
- **監控指標**：API 回應時間、資料庫查詢時間、系統資源使用率

**R-004：資料庫效能瓶頸**

- **應對策略**：減輕（Mitigate）
- **具體措施**：
  1. **索引優化**：建立適當的資料庫索引
  2. **查詢優化**：優化慢查詢，使用 EXPLAIN 分析
  3. **資料歸檔**：實作資料歸檔機制，定期清理舊資料
  4. **讀寫分離**：如需要，考慮讀寫分離
- **負責人**：後端開發工程師
- **監控指標**：資料庫查詢時間、索引使用率、資料庫大小

**R-009：開發時程延遲**

- **應對策略**：減輕（Mitigate）
- **具體措施**：
  1. **時程緩衝**：每個階段預留 1 週緩衝時間
  2. **優先級管理**：優先實作核心功能，非核心功能可延後
  3. **資源調整**：必要時增加開發資源
  4. **範圍管理**：嚴格控制需求變更，避免範圍擴張
- **負責人**：專案經理
- **監控指標**：里程碑達成率、時程偏差、資源使用率

**R-014：系統可用性無法達到 99%**

- **應對策略**：減輕（Mitigate）
- **具體措施**：
  1. **高可用架構**：設計高可用架構（容器化、自動重啟）
  2. **健康檢查**：實作完善的健康檢查與自動恢復機制
  3. **監控告警**：建立監控與告警機制
  4. **災難復原**：實作災難復原計畫與演練
- **負責人**：DevOps 工程師
- **監控指標**：系統可用性、停機時間、MTTR（平均修復時間）

#### 11.3.3 低風險應對策略

**R-005：AI 服務資源消耗過高**

- **應對策略**：接受（Accept）
- **具體措施**：
  1. **資源監控**：監控 AI 服務資源使用情況
  2. **批次處理**：使用批次處理減少資源消耗
  3. **模型優化**：優化模型大小與推理速度
- **負責人**：AI/ML 工程師
- **監控指標**：CPU/記憶體使用率、處理時間

**R-010：關鍵人員離職或不可用**

- **應對策略**：減輕（Mitigate）
- **具體措施**：
  1. **知識文件**：建立完整的技術文件
  2. **知識分享**：定期進行知識分享會議
  3. **備援人員**：培養備援人員
- **負責人**：專案經理
- **監控指標**：文件完整度、知識分享頻率

### 11.4 風險監控與追蹤

#### 11.4.1 風險監控機制

**定期風險審查**：
- **頻率**：每 2 週（Sprint Review 時）
- **參與人員**：專案經理、技術負責人、開發團隊代表
- **審查內容**：
  - 既有風險狀態更新
  - 新風險識別
  - 風險應對措施執行狀況
  - 風險等級調整

**風險儀表板**：
- 建立風險追蹤儀表板，記錄所有風險的狀態
- 包含：風險 ID、描述、等級、狀態、負責人、應對措施、監控指標

#### 11.4.2 風險追蹤表

| 風險 ID | 風險描述 | 等級 | 狀態 | 負責人 | 應對策略 | 監控指標 | 最後更新 |
|--------|---------|------|------|--------|---------|---------|---------|
| R-001 | AI/ML 資訊提取準確度不足 | 高 | 監控中 | AI/ML 工程師 | 減輕 | 提取準確度、信心分數 | - |
| R-002 | 外部威脅來源 API 變更 | 高 | 監控中 | 後端開發工程師 | 減輕 | API 呼叫成功率 | - |
| R-003 | 系統效能無法滿足需求 | 中 | 監控中 | 後端開發工程師 | 減輕 | API 回應時間 | - |
| ... | ... | ... | ... | ... | ... | ... | ... |

**風險狀態**：
- **未發生**：風險尚未發生，持續監控
- **監控中**：風險已識別，應對措施執行中
- **已緩解**：風險已透過應對措施降低至可接受範圍
- **已發生**：風險已發生，正在處理
- **已關閉**：風險已解決或不再適用

#### 11.4.3 風險升級機制

**升級條件**：
- 風險等級從「中」提升至「高」或「極高」
- 風險應對措施無效，需要調整策略
- 風險已發生，需要緊急處理

**升級流程**：
1. 識別需要升級的風險
2. 通知專案負責人與利害關係人
3. 召開緊急風險處理會議
4. 制定新的應對策略
5. 更新風險追蹤表

### 11.5 風險應急計畫

#### 11.5.1 緊急風險處理流程

**觸發條件**：
- 極高風險發生
- 高風險發生且影響專案核心目標
- 系統安全漏洞被發現

**處理流程**：
1. **立即通知**：通知專案負責人與相關人員（30 分鐘內）
2. **緊急會議**：召開緊急風險處理會議（2 小時內）
3. **制定方案**：制定緊急應對方案（4 小時內）
4. **執行措施**：執行緊急應對措施
5. **持續監控**：持續監控風險狀態
6. **事後檢討**：風險處理後進行事後檢討

#### 11.5.2 關鍵風險應急方案

**R-001 應急方案**（AI 提取準確度嚴重不足）：
- 立即啟用規則基礎方法作為主要提取機制
- 暫停 AI 服務，進行緊急調優
- 增加人工審核流程

**R-002 應急方案**（外部 API 完全失效）：
- 啟用手動匯入機制
- 尋找替代資料來源
- 通知利害關係人服務受限

**R-006 應急方案**（資料外洩事件）：
- 立即隔離受影響系統
- 通知資安團隊與管理層
- 啟動事件回應流程
- 進行損害評估與修復

---

## 12. 憲章遵循檢查

本章節依據專案憲章（Project Constitution v2.2.0）的所有原則，逐一檢查本實作計畫（plan.md）的遵循情況，確保所有設計與決策符合憲章規範。

### 12.1 核心原則遵循檢查

#### 12.1.1 P0：規格驅動開發 (SDD)

**憲章要求**：
- Phase 1: 規格 (SPEC)
- Phase 2: 計畫 (PLAN)
- Phase 3: 任務 (Tasks)
- Phase 4: 執行 (EXECUTE)
- Phase 5: 驗收 (REVIEW)

**遵循情況**：✅ **完全遵循**

**證據**：
- 本文件為 Phase 2: 計畫 (PLAN) 階段產出
- 所有設計基於 `spec.md`（Phase 1 產出）中的使用者故事與需求
- 第 10 章「開發時程」定義了後續階段（Phase 3-5）的規劃
- 所有模組設計可追溯至 `spec.md` 中的使用者故事

**參考章節**：
- 第 1 章「目的」明確說明本文件為 Phase 2 產出
- 第 6 章「模組設計」中所有功能模組對應 `spec.md` 的使用者故事

---

#### 12.1.2 P1：簡潔優先於複雜 (Simplicity over Complexity)

**憲章要求**：偏好清晰、簡單、直接的解決方案，複雜性必須提供充分的理由與文件化說明。

**遵循情況**：✅ **完全遵循**

**證據**：
- **架構選擇**：採用模組化單體而非微服務，降低複雜度（第 3.1 節）
- **技術選擇**：使用成熟的技術堆疊，避免過度複雜的解決方案（第 3.4 節）
- **AI/ML 設計**：使用成熟的 NLP 函式庫（spaCy、transformers），避免複雜的模型訓練（第 7.1 節）
- **模組設計**：簡化的 Python 類別設計，避免過度抽象（第 6 章）

**複雜性說明**：
- 模組化單體架構的複雜性已在第 3.3 節詳細說明理由
- DDD 有界上下文的劃分已在第 3.2 節說明理由

**參考章節**：
- 第 3.1 節「架構模式」：說明模組化單體的選擇理由
- 第 3.4 節「技術堆疊選擇」：說明技術選擇的簡潔性考量
- 第 7.1 節「NLP 處理架構」：說明 AI 服務的簡單設計

---

#### 12.1.3 P2：設計即安全 (Security by Design)

**憲章要求**：
1. 身份驗證：必須使用 OIDC/OAuth 2.0
2. 授權：必須採用 RBAC
3. 合規性：必須產生稽核日誌（ISO 27001:2022）
4. 數據加密：at-rest 與 in-transit 加密

**遵循情況**：✅ **完全遵循**

**證據**：

1. **身份驗證**：
   - 第 5.3 節「身份驗證與授權」定義 OIDC/OAuth 2.0 整合
   - 第 9.2 節「環境配置」包含 OIDC 配置

2. **授權**：
   - 第 5.3 節定義 RBAC 實作
   - 第 6.4 節「Web 管理界面模組」包含授權中介軟體設計

3. **稽核日誌**：
   - 第 4.2 節「資料庫 Schema」定義 `AuditLogs` 表
   - 第 5.2 節「API 端點定義」包含稽核日誌查詢端點
   - 第 6 章各模組設計包含稽核日誌記錄

4. **數據加密**：
   - 第 9.2 節「環境配置」定義 TLS 配置
   - 第 9.3 節「監控與日誌」包含安全配置
   - NFR-004（資料加密）已在需求文件中定義

**參考章節**：
- 第 5.3 節「身份驗證與授權」
- 第 4.2 節「資料庫 Schema」（AuditLogs 表）
- 第 9.2 節「環境配置」（安全配置）

---

#### 12.1.4 P3：清晰與可測試性 (Clarity and Testability)

**憲章要求**：
1. 每個使用者故事必須具有明確、可測試的驗收條件
2. 程式碼必須可進行單元測試與整合測試

**遵循情況**：✅ **完全遵循**

**證據**：
- **驗收條件**：所有使用者故事的驗收條件已在 `spec.md` 中定義（AC-001-1 至 AC-029-X）
- **測試策略**：第 8 章「測試策略」完整定義測試範圍與類型
  - 第 8.1 節：單元測試（覆蓋率 ≥ 80%）
  - 第 8.2 節：整合測試
  - 第 8.3 節：端對端測試
  - 第 8.4 節：效能測試
- **可測試設計**：第 6 章「模組設計」中的類別設計支援依賴注入，便於測試

**參考章節**：
- 第 8 章「測試策略」（完整測試計畫）
- 第 6 章「模組設計」（可測試的類別設計）

---

#### 12.1.5 P4：漸進式價值交付 (Incremental Value Delivery)

**憲章要求**：必須以小型、可驗證且獨立的增量交付價值，所有任務必須可追溯至使用者故事。

**遵循情況**：✅ **完全遵循**

**證據**：
- **階段劃分**：第 10.1 節「階段劃分」將開發分為 5 個階段，每個階段產出可驗證的價值
- **里程碑**：第 10.2 節「里程碑」定義 5 個里程碑（M1-M5），每個里程碑對應特定使用者故事
- **可追溯性**：第 6 章「模組設計」中所有功能模組明確對應 `spec.md` 中的使用者故事
  - 基礎建設模組：US-001 至 US-007
  - 自動化收集模組：US-008 至 US-014
  - 報告生成模組：US-015 至 US-021
  - Web 管理界面模組：US-022 至 US-029

**參考章節**：
- 第 10.1 節「階段劃分」（增量交付規劃）
- 第 10.2 節「里程碑」（可驗證的交付成果）
- 第 6 章「模組設計」（使用者故事對應）

---

#### 12.1.6 P5：主要語言（zh-TW）

**憲章要求**：所有專案產出物必須使用正體中文（zh-TW）撰寫。

**遵循情況**：✅ **完全遵循**

**證據**：
- 本文件（plan.md）完全使用正體中文撰寫
- 所有章節標題、內容、程式碼註解均使用正體中文
- 技術術語提供中英文對照（如：領域驅動設計 (DDD)）

**參考章節**：
- 全文

---

### 12.2 設計與品質原則遵循檢查

#### 12.2.1 P6：程式碼品質標準

**憲章要求**：程式碼必須遵循既定的風格與最佳實踐，所有程式碼在合併前必須經由程式碼審查。

**遵循情況**：✅ **完全遵循**

**證據**：
- **程式碼風格**：第 6 章「模組設計」中的 Python 類別設計遵循 Python 命名慣例（PEP 8）
- **Code Review**：第 10.5 節「開發流程」定義 Code Review 流程
- **Lint 檢查**：NFR-010（程式碼品質）要求所有程式碼通過 Lint 檢查

**參考章節**：
- 第 6 章「模組設計」（程式碼範例）
- 第 10.5 節「開發流程」（Code Review 流程）

---

#### 12.2.2 P7：嚴謹測試標準

**憲章要求**：所有新功能必須具備相應的測試，測試的範圍與類型必須記載於 plan.md 文件中。

**遵循情況**：✅ **完全遵循**

**證據**：
- **測試策略**：第 8 章「測試策略」完整定義測試範圍與類型
  - 單元測試（第 8.1 節）
  - 整合測試（第 8.2 節）
  - 端對端測試（第 8.3 節）
  - 效能測試（第 8.4 節）
- **測試覆蓋率**：第 8.6 節「測試覆蓋率要求」定義覆蓋率目標（≥ 80%）
- **測試自動化**：第 8.5 節「測試自動化」定義 CI/CD 整合

**參考章節**：
- 第 8 章「測試策略」（完整測試計畫）

---

#### 12.2.3 P8：一致的使用者體驗

**憲章要求**：
1. 必須使用統一的設計系統和共用組件庫
2. 明確的交易儲存：不得採用即時儲存，必須提供「儲存」或「確認」按鈕

**遵循情況**：✅ **完全遵循**

**證據**：
- **設計系統**：第 3.4 節「技術堆疊選擇」定義前端使用 Next.js + React + Tailwind CSS，確保一致的設計語言
- **明確儲存**：雖然本文件（plan.md）主要關注後端設計，但前端設計應遵循此原則（需在 tasks.md 階段確認）

**參考章節**：
- 第 3.4 節「技術堆疊選擇」（前端技術堆疊）

**備註**：前端 UI/UX 的具體實作細節將在 tasks.md 階段定義，屆時需確保遵循明確交易儲存原則。

---

#### 12.2.4 P9：效能要求

**憲章要求**：所有與效能相關的非功能性需求必須在 spec.md 中明確定義。

**遵循情況**：✅ **完全遵循**

**證據**：
- **效能需求**：`spec.md` 中已定義 NFR-001（效能要求）
  - API 回應時間 ≤ 2 秒
  - 支援至少 10,000 筆資產記錄
  - 支援至少 100,000 筆威脅記錄
  - 支援至少 10 個並行使用者
- **效能測試**：第 8.4 節「效能測試」定義效能測試策略
- **效能優化**：第 3.4 節「技術堆疊選擇」包含 Redis 快取，第 4.2 節「資料庫 Schema」定義索引

**參考章節**：
- 第 8.4 節「效能測試」
- 第 3.4 節「技術堆疊選擇」（Redis 快取）
- 第 4.2 節「資料庫 Schema」（索引定義）

---

### 12.3 架構與技術原則遵循檢查

#### 12.3.1 P10：架構設計

**憲章要求**：
1. 嚴格遵循 DDD 方法論，基於有界上下文劃分
2. 採用模組化單體架構
3. 非即時性跨模組操作必須使用事件/訊息佇列

**遵循情況**：✅ **完全遵循**

**證據**：

1. **DDD 方法論**：
   - 第 3.2 節「有界上下文劃分」定義 5 個有界上下文
   - 第 6 章「模組設計」遵循 DDD 分層架構（Domain、Application、Infrastructure）

2. **模組化單體**：
   - 第 3.1 節「架構模式」明確選擇模組化單體
   - 第 3.3 節「模組化單體設計」詳細說明模組結構

3. **非同步通訊**：
   - 第 3.3 節「模組化單體設計」定義事件匯流排機制
   - 第 3.4 節「技術堆疊選擇」包含 RabbitMQ/Redis Pub/Sub
   - 第 6 章各模組設計包含事件發布與訂閱

**參考章節**：
- 第 3.1 節「架構模式」
- 第 3.2 節「有界上下文劃分」
- 第 3.3 節「模組化單體設計」

---

#### 12.3.2 P11：技術堆疊

**憲章要求**：必須在指定技術堆疊內開發。

**遵循情況**：✅ **完全遵循**

**證據**：
- **前端**：第 3.4 節選擇 Next.js 14+ / React 18+ / TypeScript / Tailwind CSS ✅
- **後端**：第 3.4 節選擇 Python 3.10+ / FastAPI（符合 Python 要求）✅
- **資料庫**：第 3.4 節選擇 SQLite / MS SQL Server 2022+ ✅
- **API 規格**：第 5.1 節定義 RESTful API（OpenAPI 3.x）✅
- **緩存**：第 3.4 節選擇 Redis ✅
- **容器化**：第 9.1 節定義 Docker 容器化 ✅

**技術堆疊對照表**：

| 憲章要求 | 本計畫選擇 | 狀態 |
|---------|-----------|------|
| 前端：Next.js 14+ / React 18+ / TypeScript / Tailwind CSS | Next.js 14+ / React 18+ / TypeScript / Tailwind CSS | ✅ |
| 後端：ASP.NET Core 8+ / C# 12 / Python | Python 3.10+ / FastAPI | ✅（使用 Python） |
| 資料庫：SQLite / MS SQL Server 2022+ | SQLite / MS SQL Server 2022+ | ✅ |
| API：RESTful (OpenAPI 3.x) | RESTful (OpenAPI 3.x) | ✅ |
| 緩存：Redis | Redis | ✅ |
| 容器化：Docker | Docker | ✅ |

**參考章節**：
- 第 3.4 節「技術堆疊選擇」

---

#### 12.3.3 P12：數據治理

**憲章要求**：
1. 單一事實來源 (SSoT)：每個數據實體必須有唯一的「擁有者」模組，禁止跨模組直接存取資料庫
2. 資料庫變更：禁止手動變更生產資料庫，必須透過資料庫遷移工具

**遵循情況**：✅ **完全遵循**

**證據**：

1. **單一事實來源 (SSoT)**：
   - 第 4.1 節「資料模型」明確說明 SSoT 原則
   - 第 3.3 節「模組化單體設計」定義模組職責，每個模組擁有自己的資料實體
   - 第 6 章「模組設計」中，各模組透過 Repository 模式存取資料，禁止跨模組直接存取

2. **資料庫遷移**：
   - 第 4.3 節「資料遷移策略」定義使用 Entity Framework Core Migrations（或 Python 的 Alembic）
   - 第 9.4 節「部署流程」包含資料庫遷移步驟

**參考章節**：
- 第 4.1 節「資料模型」（SSoT 原則）
- 第 4.3 節「資料遷移策略」
- 第 6 章「模組設計」（Repository 模式）

---

#### 12.3.4 P13：可觀測性

**憲章要求**：
1. 日誌：必須使用結構化日誌，統一發送到中央日誌系統
2. 指標：必須暴露健康檢查端點和關鍵效能指標
3. 追蹤：跨模組的 API 呼叫必須實作分佈式追蹤

**遵循情況**：✅ **完全遵循**

**證據**：

1. **結構化日誌**：
   - 第 9.3.1 節「日誌記錄策略」定義結構化日誌（JSON 格式）
   - 第 9.3.4 節「日誌收集與儲存」定義中央日誌系統整合

2. **健康檢查與指標**：
   - 第 9.3.2 節「健康檢查實作」定義 `/health` 端點
   - 第 9.3.3 節「指標監控」定義 `/metrics` 端點與 KPI 監控

3. **分佈式追蹤**：
   - 第 9.3.5 節「分佈式追蹤」定義追蹤 ID 與追蹤中介軟體
   - 第 5.2 節「API 端點定義」包含追蹤 ID 在回應標頭中

**參考章節**：
- 第 9.3 節「監控與日誌」（完整可觀測性設計）

---

### 12.4 治理原則遵循檢查

#### 12.4.1 H1：修訂程序

**憲章要求**：任何對憲章的修改必須透過 Pull Request 提出，並經專案負責人核准。

**遵循情況**：✅ **不適用於本文件**

**說明**：本文件（plan.md）為實作計畫，不涉及憲章修訂。憲章修訂應遵循 H1 程序。

---

#### 12.4.2 H2：版本管理

**憲章要求**：版本號管理規則。

**遵循情況**：✅ **遵循**

**證據**：
- 本文件（plan.md）包含版本資訊（v1.0.0）
- 文件狀態標記為「草案 (Draft)」

**參考章節**：
- 文件標題（版本：v1.0.0）

---

#### 12.4.3 H3：合規要求

**憲章要求**：所有功能計畫文件（plan.md）必須包含「憲章遵循檢查」章節。

**H4：驗收報告要求**：Phase 4（執行階段）的所有任務完成後，必須建立對應的驗收報告。

**遵循情況**：✅ **完全遵循**

**證據**：
- 本章節（第 12 章）即為「憲章遵循檢查」章節
- **H4：驗收報告要求**：所有 Phase 4（執行階段）的任務完成後，必須在 `系統建置與驗證報告/` 資料夾下建立對應的驗收報告，確保任務完成狀態、驗收條件、測試結果都有完整的文件記錄。詳細規範請參考 `系統建置與驗證報告/README.md`。
- 逐一檢查所有憲章原則（P0-P13、H1-H4）
- 提供遵循證據與參考章節

**參考章節**：
- 本章節（第 12 章）

---

### 12.5 遵循檢查總結

#### 12.5.1 遵循狀態統計

| 原則類別 | 原則數量 | 完全遵循 | 部分遵循 | 未遵循 |
|---------|---------|---------|---------|--------|
| 核心原則 (P0-P5) | 6 | 6 | 0 | 0 |
| 設計與品質原則 (P6-P9) | 4 | 4 | 0 | 0 |
| 架構與技術原則 (P10-P13) | 4 | 4 | 0 | 0 |
| 治理原則 (H1-H4) | 4 | 4 | 0 | 0 |
| **總計** | **18** | **18** | **0** | **0** |

#### 12.5.2 遵循率

**總遵循率：100%** ✅

所有憲章原則均已在本實作計畫中得到遵循與落實。

#### 12.5.3 關鍵遵循證據摘要

1. **SDD 流程**：本文件為 Phase 2 產出，基於 spec.md 制定
2. **DDD 架構**：完整的有界上下文劃分與模組化單體設計
3. **安全設計**：OIDC/OAuth 2.0、RBAC、稽核日誌、資料加密
4. **測試策略**：完整的測試計畫（單元、整合、端對端、效能）
5. **技術堆疊**：完全符合憲章指定的技術堆疊
6. **數據治理**：SSoT 原則與資料庫遷移工具
7. **可觀測性**：結構化日誌、健康檢查、分佈式追蹤

#### 12.5.4 後續行動

1. **Phase 3: 任務 (Tasks)**：在 tasks.md 階段，需確保所有任務遵循憲章原則
2. **Phase 4: 執行 (EXECUTE)**：開發過程中持續檢查憲章遵循情況
3. **Phase 5: 驗收 (REVIEW)**：驗收時再次確認憲章遵循

---

## 13. 參考文件

本章節列出本實作計畫（plan.md）所參考的所有文件、標準、規範與技術文件，供開發團隊與利害關係人查閱。

### 13.1 專案內部文件

#### 13.1.1 專案憲章

- **文件名稱**：`1.專案憲章 Project Constitution.md`
- **版本**：v2.1.0
- **核准日期**：2025-11-09
- **說明**：定義專案的不可協商原則與規範，包含核心原則、設計與品質原則、架構與技術原則、治理原則。本實作計畫嚴格遵循所有憲章原則。
- **參考章節**：第 12 章「憲章遵循檢查」

#### 13.1.2 系統需求規格文件

- **文件名稱**：`系統需求設計與分析/spec.md`
- **版本**：v1.0.0
- **撰寫日期**：2025-11-21
- **說明**：定義系統的完整需求規格，包含 29 個使用者故事（US-001 至 US-029）、100+ 個驗收條件、非功能性需求。本實作計畫基於此文件制定。
- **參考章節**：全文，特別是第 6 章「模組設計」對應 spec.md 的使用者故事

#### 13.1.3 專案概述文件

- **文件名稱**：`0.AI代理人自動化威脅情資管理系統.md`
- **版本**：v1.0
- **說明**：專案的基本資訊與核心功能概述，說明專案目的、目標與核心功能。
- **參考章節**：第 1 章「目的」

#### 13.1.4 專案資料文件

- **資產清單**：`系統需求設計與分析/資產清單.csv`
  - 說明：內部資產清冊範例，用於定義資產匯入格式
  - 參考章節：第 4.2 節「資料庫 Schema」（Assets 表）

- **優先情資需求**：`系統需求設計與分析/定義優先情資需求-PIR-2.csv`
  - 說明：結構化的優先情資需求定義，符合 spec.md 7.2 格式
  - 參考章節：第 4.2 節「資料庫 Schema」（PIRs 表）

- **威脅情資來源選擇**：`系統需求設計與分析/選擇與對應情資來源-Threat Feed Selection.csv`
  - 說明：威脅情資來源訂閱清單，包含優先級、對應 PIR、收集策略
  - 參考章節：第 4.2 節「資料庫 Schema」（ThreatFeeds 表）

---

### 13.2 國際標準與合規要求

#### 13.2.1 ISO 27001:2022

- **標準名稱**：ISO/IEC 27001:2022 - Information security management systems
- **相關控制項**：A.5.7 (Threat Intelligence)
- **說明**：資訊安全管理系統標準，本系統旨在達成 A.5.7 控制項的合規要求。
- **參考章節**：
  - 第 1 章「目的」（合規目標）
  - 第 11 章「風險管理」（合規風險）
  - 第 12 章「憲章遵循檢查」（P2 設計即安全）

#### 13.2.2 CVSS 標準

- **標準名稱**：Common Vulnerability Scoring System
- **版本**：CVSS v3.1
- **官方文件**：https://www.first.org/cvss/
- **說明**：通用漏洞評分系統，用於評估漏洞的嚴重程度。本系統使用 CVSS 分數作為風險計算的基礎。
- **參考章節**：
  - 第 6.2 節「自動化收集與關聯分析模組」（風險分數計算）
  - 第 4.2 節「資料庫 Schema」（Threats 表的 cvss_score 欄位）

#### 13.2.3 CVE 標準

- **標準名稱**：Common Vulnerabilities and Exposures
- **官方網站**：https://cve.mitre.org/
- **說明**：公開已知資訊安全漏洞與暴露的標準化識別碼。本系統使用 CVE 編號識別威脅。
- **參考章節**：
  - 第 7.2 節「威脅資訊提取」（CVE 編號識別）
  - 第 4.2 節「資料庫 Schema」（Threats 表的 cve_id 欄位）

#### 13.2.4 MITRE ATT&CK

- **框架名稱**：MITRE ATT&CK Framework
- **官方網站**：https://attack.mitre.org/
- **說明**：攻擊者的戰術、技術和程序（TTPs）知識庫。本系統使用 TTPs 識別攻擊模式。
- **參考章節**：
  - 第 7.2 節「威脅資訊提取」（TTPs 識別）
  - 第 4.2 節「資料庫 Schema」（Threats 表的 ttps 欄位）

---

### 13.3 技術標準與規範

#### 13.3.1 RESTful API 規範

- **標準名稱**：REST (Representational State Transfer)
- **API 規格**：OpenAPI 3.x
- **官方文件**：https://swagger.io/specification/
- **說明**：本系統採用 RESTful API 設計，使用 OpenAPI 3.x 規格描述 API。
- **參考章節**：
  - 第 5.1 節「RESTful API 規格」
  - 第 5.2 節「API 端點定義」

#### 13.3.2 OIDC/OAuth 2.0

- **標準名稱**：
  - OpenID Connect (OIDC) 1.0
  - OAuth 2.0 Authorization Framework
- **官方文件**：
  - OIDC: https://openid.net/specs/openid-connect-core-1_0.html
  - OAuth 2.0: https://oauth.net/2/
- **說明**：身份驗證與授權協議，本系統使用 OIDC/OAuth 2.0 進行統一身份驗證。
- **參考章節**：
  - 第 5.3 節「身份驗證與授權」
  - 第 6.4 節「Web 管理界面模組」（身份驗證整合）

#### 13.3.3 RBAC 模型

- **標準名稱**：Role-Based Access Control
- **參考標準**：NIST RBAC Model
- **說明**：角色基礎存取控制模型，本系統採用 RBAC 進行授權管理。
- **參考章節**：
  - 第 5.3 節「身份驗證與授權」（RBAC 實作）
  - 第 4.2 節「資料庫 Schema」（Roles、Permissions、UserRoles 表）

---

### 13.4 架構與設計方法論

#### 13.4.1 領域驅動設計 (DDD)

- **方法論名稱**：Domain-Driven Design
- **作者**：Eric Evans
- **參考書籍**：《Domain-Driven Design: Tackling Complexity in the Heart of Software》
- **說明**：本系統嚴格遵循 DDD 方法論，使用有界上下文劃分領域模型。
- **參考章節**：
  - 第 3.1 節「架構模式」（DDD 方法論）
  - 第 3.2 節「有界上下文劃分」
  - 第 6 章「模組設計」（領域模型設計）

#### 13.4.2 模組化單體架構

- **架構模式**：Modular Monolith
- **參考資料**：
  - 《Monolith to Microservices》by Sam Newman
  - 《Modular Monolith Primer》by Kamil Grzybek
- **說明**：本系統採用模組化單體架構，確保模組間界線清晰，未來可演進為微服務。
- **參考章節**：
  - 第 3.1 節「架構模式」（模組化單體選擇）
  - 第 3.3 節「模組化單體設計」

#### 13.4.3 CQRS 與事件驅動架構

- **模式名稱**：
  - CQRS (Command Query Responsibility Segregation)
  - Event-Driven Architecture
- **說明**：本系統使用事件驅動架構進行模組間非同步通訊。
- **參考章節**：
  - 第 3.3 節「模組化單體設計」（事件匯流排）
  - 第 6 章「模組設計」（事件發布與訂閱）

---

### 13.5 技術文件與框架

#### 13.5.1 前端技術

- **Next.js**
  - 官方文件：https://nextjs.org/docs
  - 版本：14+
  - 說明：React 框架，用於建構前端應用程式

- **React**
  - 官方文件：https://react.dev/
  - 版本：18+
  - 說明：使用者介面函式庫

- **TypeScript**
  - 官方文件：https://www.typescriptlang.org/docs/
  - 說明：型別安全的 JavaScript 超集

- **Tailwind CSS**
  - 官方文件：https://tailwindcss.com/docs
  - 說明：實用優先的 CSS 框架

**參考章節**：第 3.4 節「技術堆疊選擇」（前端技術）

#### 13.5.2 後端技術

- **Python**
  - 官方文件：https://docs.python.org/3/
  - 版本：3.10+
  - 說明：主要程式語言

- **FastAPI**
  - 官方文件：https://fastapi.tiangolo.com/
  - 說明：現代、快速的 Web 框架

- **Pydantic**
  - 官方文件：https://docs.pydantic.dev/
  - 說明：資料驗證函式庫

- **SQLAlchemy**
  - 官方文件：https://www.sqlalchemy.org/
  - 說明：Python ORM 框架

- **Alembic**
  - 官方文件：https://alembic.sqlalchemy.org/
  - 說明：資料庫遷移工具

**參考章節**：第 3.4 節「技術堆疊選擇」（後端技術）

#### 13.5.3 資料庫技術

- **SQLite**
  - 官方文件：https://www.sqlite.org/docs.html
  - 說明：輕量級關聯式資料庫（開發環境）

- **Microsoft SQL Server**
  - 官方文件：https://docs.microsoft.com/sql/
  - 版本：2022+
  - 說明：企業級關聯式資料庫（生產環境）

**參考章節**：第 3.4 節「技術堆疊選擇」（資料庫技術）

#### 13.5.4 容器化與部署

- **Docker**
  - 官方文件：https://docs.docker.com/
  - 說明：容器化平台

- **Docker Compose**
  - 官方文件：https://docs.docker.com/compose/
  - 說明：多容器應用程式定義工具

**參考章節**：
  - 第 9.1 節「容器化策略」
  - 第 9.4 節「部署流程」

#### 13.5.5 AI/ML 技術

- **spaCy**
  - 官方文件：https://spacy.io/usage
  - 說明：自然語言處理函式庫

- **transformers (Hugging Face)**
  - 官方文件：https://huggingface.co/docs/transformers/
  - 說明：預訓練模型函式庫

**參考章節**：
  - 第 7.1 節「NLP 處理架構」
  - 第 7.2 節「威脅資訊提取」

---

### 13.6 威脅情資來源文件

#### 13.6.1 CISA KEV

- **全名**：Known Exploited Vulnerabilities Catalog
- **官方網站**：https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- **API 文件**：https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- **說明**：美國網路安全與基礎設施安全局維護的已知遭利用漏洞清單。

#### 13.6.2 NVD

- **全名**：National Vulnerability Database
- **官方網站**：https://nvd.nist.gov/
- **API 文件**：https://nvd.nist.gov/developers/vulnerabilities
- **說明**：美國國家標準與技術研究院維護的漏洞資料庫。

#### 13.6.3 VMware VMSA

- **全名**：VMware Security Advisories
- **官方網站**：https://www.vmware.com/security/advisories.html
- **RSS Feed**：https://www.vmware.com/security/advisories.xml
- **說明**：VMware 安全公告。

#### 13.6.4 MSRC

- **全名**：Microsoft Security Response Center
- **官方網站**：https://msrc.microsoft.com/
- **API 文件**：https://api.msrc.microsoft.com/
- **說明**：微軟安全回應中心。

#### 13.6.5 TWCERT/CC

- **全名**：台灣電腦網路危機處理暨協調中心
- **官方網站**：https://www.twcert.org.tw/
- **說明**：台灣資安事件通報與協調中心。

**參考章節**：
  - 第 6.2 節「自動化收集與關聯分析模組」（威脅收集服務）
  - 第 7.2 節「威脅資訊提取」（非結構化內容處理）

---

### 13.7 測試與品質保證

#### 13.7.1 pytest

- **官方文件**：https://docs.pytest.org/
- **說明**：Python 測試框架

#### 13.7.2 pytest-cov

- **官方文件**：https://pytest-cov.readthedocs.io/
- **說明**：pytest 測試覆蓋率外掛

#### 13.7.3 Playwright / Cypress

- **Playwright**：https://playwright.dev/
- **Cypress**：https://docs.cypress.io/
- **說明**：端對端測試工具（可選）

**參考章節**：第 8 章「測試策略」

---

### 13.8 監控與可觀測性

#### 13.8.1 結構化日誌

- **標準**：JSON Logging Format
- **說明**：本系統使用 JSON 格式的結構化日誌。

#### 13.8.2 OpenTelemetry

- **官方文件**：https://opentelemetry.io/docs/
- **說明**：分佈式追蹤標準（可選）

#### 13.8.3 Prometheus

- **官方文件**：https://prometheus.io/docs/
- **說明**：指標監控系統（可選）

**參考章節**：
  - 第 9.3 節「監控與日誌」
  - 第 9.3.3 節「指標監控」（Prometheus 格式）

---

### 13.9 安全最佳實踐

#### 13.9.1 OWASP Top 10

- **官方網站**：https://owasp.org/www-project-top-ten/
- **說明**：Web 應用程式安全風險 Top 10，本系統需防範這些風險。

#### 13.9.2 安全開發指南

- **OWASP ASVS**：Application Security Verification Standard
- **官方網站**：https://owasp.org/www-project-application-security-verification-standard/
- **說明**：應用程式安全驗證標準

**參考章節**：
  - 第 11 章「風險管理」（R-008：輸入驗證不足）
  - 第 5.3 節「身份驗證與授權」（安全措施）

---

### 13.10 文件版本資訊

| 文件類型 | 文件名稱 | 版本 | 最後更新日期 |
|---------|---------|------|------------|
| 專案憲章 | `1.專案憲章 Project Constitution.md` | v2.2.0 | 2025-11-21 |
| 需求規格 | `系統需求設計與分析/spec.md` | v1.0.0 | 2025-11-21 |
| 實作計畫 | `系統需求設計與分析/plan.md` | v1.0.0 | 2025-11-21 |
| 專案概述 | `0.AI代理人自動化威脅情資管理系統.md` | v1.0 | - |

---

### 13.11 參考文件使用說明

1. **開發階段**：開發團隊應參考技術文件與框架文件進行實作
2. **設計階段**：系統設計應參考架構與設計方法論文檔
3. **測試階段**：測試團隊應參考測試工具文件撰寫測試案例
4. **部署階段**：DevOps 團隊應參考容器化與部署文件進行部署
5. **合規檢查**：應參考 ISO 27001:2022 標準確保合規

---

**第 13 章：參考文件完成**

---

## 文件結束

**文件狀態**：已核准 (Approved)  
**Phase 2: 計畫 (PLAN) 階段已完成**  
**當前階段**：Phase 3: 任務 (Tasks) - 進行中  
**相關文件**：`系統需求設計與分析/tasks.md`

