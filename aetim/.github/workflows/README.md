# GitHub Actions 工作流程說明

本目錄包含所有 CI/CD 工作流程配置。

## 工作流程

### 1. test.yml
**用途**：執行所有測試並檢查測試覆蓋率

**觸發條件**：
- Push 到 main 或 develop 分支
- Pull Request 到 main 或 develop 分支

**工作內容**：
- 後端測試（Python/FastAPI）
- 前端測試（Next.js/TypeScript）
- AI 服務測試（Python）

**覆蓋率要求**：≥ 80%

### 2. lint.yml
**用途**：執行程式碼品質檢查

**觸發條件**：
- Push 到 main 或 develop 分支
- Pull Request 到 main 或 develop 分支

**工作內容**：
- 後端 Lint（Black、Ruff、mypy）
- 前端 Lint（ESLint）
- AI 服務 Lint（Black、Ruff）

### 3. build.yml
**用途**：建置 Docker 映像檔

**觸發條件**：
- Push 到 main 分支
- 推送版本標籤（v*）
- Pull Request 到 main 分支

**工作內容**：
- 建置後端 Docker 映像檔
- 建置前端 Docker 映像檔
- 建置 AI 服務 Docker 映像檔

### 4. ci.yml
**用途**：整合所有 CI 檢查

**觸發條件**：
- Push 到 main 或 develop 分支
- Pull Request 到 main 或 develop 分支

**工作內容**：
- 協調執行測試與 Lint 工作流程

## 使用方式

### 本地執行測試
```bash
# 後端測試
cd backend
pytest

# 前端測試
cd frontend
npm run lint
npm run type-check

# AI 服務測試
cd ai_service
pytest
```

### 本地執行 Lint
```bash
# 後端 Lint
cd backend
black --check .
ruff check .
mypy .

# 前端 Lint
cd frontend
npm run lint
```

### 使用 Pre-commit Hooks
```bash
# 安裝 pre-commit
pip install pre-commit

# 安裝 hooks
pre-commit install

# 手動執行所有 hooks
pre-commit run --all-files
```

## 注意事項

1. **測試覆蓋率**：所有新功能必須達到 ≥ 80% 的測試覆蓋率
2. **程式碼品質**：所有程式碼必須通過 Lint 檢查
3. **類型檢查**：TypeScript 程式碼必須通過類型檢查
4. **CI 失敗**：如果 CI 失敗，PR 將無法合併

