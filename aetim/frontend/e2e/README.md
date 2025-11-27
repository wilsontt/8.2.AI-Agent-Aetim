# 端對端測試文件

本目錄包含 AETIM 系統的端對端測試。

## 測試框架

- **Playwright**：用於前端端對端測試
- **Pytest**：用於後端端對端測試

## 測試結構

### 前端測試（Playwright）

- `auth.spec.ts`：身份驗證與授權流程測試
- `dashboard.spec.ts`：儀表板功能測試
- `audit-logs.spec.ts`：稽核日誌查詢介面測試
- `settings.spec.ts`：系統設定管理測試
- `api-e2e.spec.ts`：API 端對端測試

### 後端測試（Pytest）

- `test_complete_workflow.py`：完整工作流程測試

## 執行測試

### 前端測試

```bash
cd frontend
npx playwright install
npx playwright test
```

### 後端測試

```bash
cd backend
pytest tests/e2e/
```

## 測試報告

測試報告會生成在以下位置：

- HTML 報告：`frontend/test-results/playwright-report/index.html`
- JSON 報告：`frontend/test-results/results.json`
- JUnit 報告：`frontend/test-results/junit.xml`

## CI/CD 整合

測試可以在 CI/CD 流程中自動執行。請參考 `.github/workflows/` 目錄中的工作流程設定。

