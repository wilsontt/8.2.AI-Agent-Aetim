# 開發文件

## 概述

本文件說明 AETIM 系統的開發環境設定、開發規範、測試流程等。

## 開發環境設定

### 1. 前置需求

- **Python**：3.10+
- **Node.js**：18+
- **Docker**：20.10+（可選）
- **Git**：2.0+

### 2. 後端開發環境

#### 2.1 設定虛擬環境

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

#### 2.2 安裝依賴

```bash
pip install -r requirements.txt
```

#### 2.3 設定環境變數

建立 `.env` 檔案：

```env
# 資料庫設定
DATABASE_URL=sqlite+aiosqlite:///./data/aetim.db
# Redis 設定
REDIS_URL=redis://localhost:6379/0
# 日誌設定
LOG_LEVEL=DEBUG
```

#### 2.4 執行資料庫遷移

```bash
alembic upgrade head
```

#### 2.5 初始化資料

```bash
python scripts/seed_roles_and_permissions.py
```

### 3. 前端開發環境

#### 3.1 安裝依賴

```bash
cd frontend
npm install
```

#### 3.2 設定環境變數

建立 `.env.local` 檔案：

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

#### 3.3 啟動開發伺服器

```bash
npm run dev
```

### 4. AI 服務開發環境

#### 4.1 設定虛擬環境

```bash
cd ai_service
python3 -m venv .venv
source .venv/bin/activate
```

#### 4.2 安裝依賴

```bash
pip install -r requirements.txt
```

#### 4.3 啟動開發伺服器

```bash
uvicorn app.main:app --reload --port 8001
```

## 開發規範

### 1. 程式碼風格

#### 1.1 Python

- **格式化工具**：Black
- **Lint 工具**：Ruff
- **型別檢查**：mypy

```bash
# 格式化
black .

# Lint
ruff check .

# 型別檢查
mypy .
```

#### 1.2 TypeScript

- **格式化工具**：Prettier
- **Lint 工具**：ESLint

```bash
# 格式化
npm run format

# Lint
npm run lint
```

### 2. 命名規範

#### 2.1 Python

- **變數與函式**：camelCase
- **類別**：PascalCase
- **常數**：UPPER_SNAKE_CASE

#### 2.2 TypeScript

- **變數與函式**：camelCase
- **類別與介面**：PascalCase
- **常數**：UPPER_SNAKE_CASE

### 3. 程式碼註解

#### 3.1 Python

使用 JSDoc 風格的 docstring：

```python
def function_name(param1: str, param2: int) -> bool:
    """
    函式說明
    
    Args:
        param1: 參數 1 說明
        param2: 參數 2 說明
    
    Returns:
        回傳值說明
    
    Raises:
        ValueError: 錯誤說明
    """
    pass
```

#### 3.2 TypeScript

使用 JSDoc 註解：

```typescript
/**
 * 函式說明
 * 
 * @param param1 - 參數 1 說明
 * @param param2 - 參數 2 說明
 * @returns 回傳值說明
 */
function functionName(param1: string, param2: number): boolean {
  return true;
}
```

## 測試

### 1. 後端測試

#### 1.1 執行測試

```bash
cd backend
pytest
```

#### 1.2 測試覆蓋率

```bash
pytest --cov=. --cov-report=html
```

#### 1.3 執行特定測試

```bash
# 單元測試
pytest tests/unit/

# 整合測試
pytest tests/integration/

# 端對端測試
pytest tests/e2e/
```

### 2. 前端測試

#### 2.1 執行測試

```bash
cd frontend
npm test
```

#### 2.2 端對端測試

```bash
npm run test:e2e
```

## Git 工作流程

### 1. 分支策略

- **main**：生產環境程式碼
- **develop**：開發環境程式碼
- **feature/**：功能開發分支
- **bugfix/**：錯誤修復分支

### 2. Commit 訊息規範

```
<type>(<scope>): <subject>

<body>

<footer>
```

範例：

```
feat(assets): 新增資產匯入功能

實作 CSV 檔案匯入功能，支援批次匯入資產。

Closes #123
```

### 3. Pull Request

- 提供清楚的描述
- 連結相關 Issue
- 確保測試通過
- 確保 Lint 通過

## 相關文件

- **API 文件**：`docs/API.md`
- **系統架構文件**：`docs/ARCHITECTURE.md`
- **專案憲章**：`系統需求設計與分析/1.專案憲章 Project Constitution.md`

