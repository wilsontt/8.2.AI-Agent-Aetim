# API 文件

## 概述

AETIM API 提供 RESTful API 介面，用於存取系統的所有功能。所有 API 端點都遵循 OpenAPI 3.0 規格。

## 基礎資訊

- **Base URL**：`http://localhost:8000/api/v1`
- **API 版本**：v1
- **認證方式**：OAuth 2.0 / OIDC
- **資料格式**：JSON

## API 文件

### 互動式 API 文件

系統提供互動式 API 文件，可在以下位置存取：

- **Swagger UI**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc
- **OpenAPI JSON**：http://localhost:8000/openapi.json

### API 端點分類

#### 1. 身份驗證與授權

- `GET /api/v1/auth/authorize` - 取得授權 URL
- `POST /api/v1/auth/callback` - OAuth2 回調處理
- `POST /api/v1/auth/logout` - 登出
- `GET /api/v1/auth/me` - 取得當前使用者資訊
- `GET /api/v1/auth/permissions` - 取得使用者權限

#### 2. 資產管理

- `GET /api/v1/assets` - 取得資產清單
- `GET /api/v1/assets/{asset_id}` - 取得資產詳情
- `POST /api/v1/assets` - 建立資產
- `PUT /api/v1/assets/{asset_id}` - 更新資產
- `DELETE /api/v1/assets/{asset_id}` - 刪除資產
- `POST /api/v1/assets/import` - 匯入資產（CSV）

#### 3. 威脅情資

- `GET /api/v1/threats` - 取得威脅清單
- `GET /api/v1/threats/{threat_id}` - 取得威脅詳情
- `PUT /api/v1/threats/{threat_id}/status` - 更新威脅狀態

#### 4. 威脅來源管理

- `GET /api/v1/threat-feeds` - 取得威脅來源清單
- `POST /api/v1/threat-feeds` - 建立威脅來源
- `PUT /api/v1/threat-feeds/{feed_id}` - 更新威脅來源
- `DELETE /api/v1/threat-feeds/{feed_id}` - 刪除威脅來源
- `POST /api/v1/threat-feeds/{feed_id}/toggle` - 啟用/停用威脅來源

#### 5. 優先情資需求 (PIR)

- `GET /api/v1/pirs` - 取得 PIR 清單
- `POST /api/v1/pirs` - 建立 PIR
- `PUT /api/v1/pirs/{pir_id}` - 更新 PIR
- `DELETE /api/v1/pirs/{pir_id}` - 刪除 PIR
- `POST /api/v1/pirs/{pir_id}/toggle` - 啟用/停用 PIR

#### 6. 報告管理

- `GET /api/v1/reports` - 取得報告清單
- `GET /api/v1/reports/{report_id}` - 取得報告詳情
- `POST /api/v1/reports/generate` - 生成報告
- `GET /api/v1/reports/{report_id}/download` - 下載報告

#### 7. 系統管理

- `GET /api/v1/system-configuration` - 取得系統設定
- `PUT /api/v1/system-configuration/{key}` - 更新系統設定
- `POST /api/v1/system-configuration/batch` - 批次更新系統設定
- `DELETE /api/v1/system-configuration/{key}` - 刪除系統設定

#### 8. 系統狀態

- `GET /api/v1/system-status` - 取得系統狀態
- `GET /api/v1/system-status/health` - 健康檢查

#### 9. 統計資料

- `GET /api/v1/statistics/threats/trend` - 威脅數量趨勢
- `GET /api/v1/statistics/threats/risk-distribution` - 風險分數分布
- `GET /api/v1/statistics/threats/affected-assets` - 受影響資產統計
- `GET /api/v1/statistics/threats/sources` - 威脅來源統計
- `GET /api/v1/statistics/assets` - 資產統計

#### 10. 稽核日誌

- `GET /api/v1/audit-logs` - 取得稽核日誌清單
- `GET /api/v1/audit-logs/{audit_log_id}` - 取得稽核日誌詳情
- `GET /api/v1/audit-logs/export/csv` - 匯出稽核日誌（CSV）
- `GET /api/v1/audit-logs/export/json` - 匯出稽核日誌（JSON）

## 認證

### OAuth 2.0 / OIDC 流程

1. **取得授權 URL**
   ```http
   GET /api/v1/auth/authorize
   ```

2. **使用者導向到 IdP 登入**

3. **處理回調**
   ```http
   POST /api/v1/auth/callback
   Content-Type: application/json
   
   {
     "code": "authorization_code",
     "state": "state_value"
   }
   ```

4. **使用 Access Token**
   ```http
   GET /api/v1/assets
   Authorization: Bearer {access_token}
   ```

## API 使用範例

### 範例 1：取得資產清單

```bash
curl -X GET "http://localhost:8000/api/v1/assets?page=1&page_size=20" \
  -H "Authorization: Bearer {access_token}"
```

### 範例 2：建立資產

```bash
curl -X POST "http://localhost:8000/api/v1/assets" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "host_name": "測試主機",
    "operating_system": "Windows Server 2016",
    "running_applications": "Microsoft SQL Server 2017",
    "owner": "測試使用者",
    "data_sensitivity": "高",
    "is_public_facing": false,
    "business_criticality": "高"
  }'
```

### 範例 3：取得威脅統計

```bash
curl -X GET "http://localhost:8000/api/v1/statistics/threats/trend?interval=day&start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer {access_token}"
```

### 範例 4：匯出稽核日誌

```bash
curl -X GET "http://localhost:8000/api/v1/audit-logs/export/csv?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer {access_token}" \
  -o audit_logs.csv
```

## 錯誤處理

### 錯誤回應格式

```json
{
  "detail": "錯誤訊息"
}
```

### 常見錯誤碼

- `400 Bad Request` - 請求參數錯誤
- `401 Unauthorized` - 未認證或 Token 無效
- `403 Forbidden` - 無權限存取
- `404 Not Found` - 資源不存在
- `422 Unprocessable Entity` - 驗證錯誤
- `429 Too Many Requests` - 請求過於頻繁
- `500 Internal Server Error` - 伺服器錯誤

## 速率限制

- **每分鐘**：60 次請求
- **每小時**：1000 次請求

超過限制時會返回 `429 Too Many Requests`，並在 `Retry-After` 標頭中提供重試時間。

## 相關文件

- **OpenAPI 規格**：http://localhost:8000/openapi.json
- **系統需求規格**：`系統需求設計與分析/spec.md`
- **實作計畫**：`系統需求設計與分析/plan.md`

