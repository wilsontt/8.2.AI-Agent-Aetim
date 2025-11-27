# 操作手冊

## 概述

本文件說明 AETIM 系統的日常操作流程，包含系統監控、維護、故障排除等。

## 系統監控

### 1. 健康檢查

#### 1.1 後端 API 健康檢查

```bash
curl http://localhost:8000/api/v1/health
```

回應範例：

```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T00:00:00Z",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "ai_service": "healthy"
  }
}
```

#### 1.2 系統狀態檢查

```bash
curl -H "Authorization: Bearer {token}" http://localhost:8000/api/v1/system-status
```

### 2. 日誌監控

#### 2.1 查看後端日誌

```bash
# Docker Compose
docker-compose logs -f backend

# Kubernetes
kubectl logs -f deployment/aetim-backend -n aetim
```

#### 2.2 查看前端日誌

```bash
# Docker Compose
docker-compose logs -f frontend

# Kubernetes
kubectl logs -f deployment/aetim-frontend -n aetim
```

#### 2.3 日誌級別

- **DEBUG**：詳細除錯資訊
- **INFO**：一般資訊
- **WARN**：警告訊息
- **ERROR**：錯誤訊息
- **FATAL**：嚴重錯誤

### 3. 效能監控

#### 3.1 Prometheus 指標

系統暴露 Prometheus 格式的指標，可在以下端點存取：

```
http://localhost:8000/api/v1/metrics
```

主要指標：

- `api_request_duration_seconds`：API 請求處理時間
- `api_request_total`：API 請求總數
- `api_request_errors_total`：API 錯誤總數

#### 3.2 效能監控儀表板

使用 Grafana 建立效能監控儀表板，監控以下指標：

- API 回應時間
- 請求數量
- 錯誤率
- 系統資源使用量

## 日常維護

### 1. 資料庫維護

#### 1.1 資料庫備份

```bash
# SQLite（開發環境）
cp data/aetim.db data/aetim.db.$(date +%Y%m%d)

# MS SQL Server（生產環境）
sqlcmd -S server -U user -P password -Q "BACKUP DATABASE aetim TO DISK='backup_$(date +%Y%m%d).bak'"
```

#### 1.2 資料庫清理

定期清理過期的稽核日誌和威脅記錄：

```sql
-- 刪除 2 年前的稽核日誌
DELETE FROM audit_logs WHERE created_at < DATEADD(YEAR, -2, GETDATE());

-- 刪除 2 年前的威脅記錄
DELETE FROM threats WHERE created_at < DATEADD(YEAR, -2, GETDATE());
```

#### 1.3 資料庫優化

```sql
-- 重建索引
ALTER INDEX ALL ON threats REBUILD;

-- 更新統計資訊
UPDATE STATISTICS threats;
```

### 2. 快取維護

#### 2.1 清除快取

```bash
# 連線到 Redis
redis-cli

# 清除所有快取
FLUSHALL

# 清除特定模式的快取
KEYS cache:statistics:*
DEL cache:statistics:*
```

#### 2.2 快取監控

```bash
# 查看 Redis 資訊
redis-cli INFO

# 查看記憶體使用
redis-cli INFO memory
```

### 3. 服務重啟

#### 3.1 重啟後端服務

```bash
# Docker Compose
docker-compose restart backend

# Kubernetes
kubectl rollout restart deployment/aetim-backend -n aetim
```

#### 3.2 重啟前端服務

```bash
# Docker Compose
docker-compose restart frontend

# Kubernetes
kubectl rollout restart deployment/aetim-frontend -n aetim
```

### 4. 資料庫遷移

#### 4.1 執行遷移

```bash
# Docker Compose
docker-compose exec backend alembic upgrade head

# 本地開發
cd backend
alembic upgrade head
```

#### 4.2 建立遷移

```bash
# 建立新的遷移檔案
alembic revision --autogenerate -m "描述"

# 檢查遷移檔案
alembic history

# 執行特定遷移
alembic upgrade {revision}
```

## 故障排除

### 1. 服務無法啟動

#### 1.1 檢查日誌

```bash
docker-compose logs backend
```

#### 1.2 檢查環境變數

```bash
docker-compose exec backend env | grep DATABASE
docker-compose exec backend env | grep REDIS
```

#### 1.3 檢查埠號

```bash
# 檢查埠號是否被占用
netstat -an | grep 8000
lsof -i :8000
```

### 2. 資料庫連線問題

#### 2.1 檢查資料庫服務

```bash
# SQLite
ls -la data/aetim.db

# MS SQL Server
sqlcmd -S server -U user -P password -Q "SELECT 1"
```

#### 2.2 檢查連線字串

確認 `DATABASE_URL` 環境變數設定正確。

### 3. Redis 連線問題

#### 3.1 檢查 Redis 服務

```bash
redis-cli ping
```

#### 3.2 檢查 Redis 連線

```bash
redis-cli -h localhost -p 6379 ping
```

### 4. API 回應時間過長

#### 4.1 檢查資料庫查詢

查看慢查詢日誌，優化查詢語句。

#### 4.2 檢查快取

確認快取是否正常運作。

#### 4.3 檢查系統資源

```bash
# CPU 使用率
top

# 記憶體使用率
free -h

# 磁碟使用率
df -h
```

### 5. 認證問題

#### 5.1 檢查 OAuth2 設定

確認 OAuth2 相關環境變數設定正確。

#### 5.2 檢查 Token 有效性

```bash
curl -H "Authorization: Bearer {token}" http://localhost:8000/api/v1/auth/me
```

## 備份與還原

### 1. 完整備份

#### 1.1 資料庫備份

```bash
# SQLite
cp data/aetim.db backups/aetim_$(date +%Y%m%d_%H%M%S).db

# MS SQL Server
sqlcmd -S server -U user -P password -Q "BACKUP DATABASE aetim TO DISK='backups/aetim_$(date +%Y%m%d_%H%M%S).bak'"
```

#### 1.2 檔案備份

```bash
# 備份報告檔案
tar -czf backups/reports_$(date +%Y%m%d_%H%M%S).tar.gz reports/

# 備份設定檔案
tar -czf backups/config_$(date +%Y%m%d_%H%M%S).tar.gz .env docker-compose.yml
```

### 2. 還原程序

#### 2.1 資料庫還原

```bash
# SQLite
cp backups/aetim_20250127.db data/aetim.db

# MS SQL Server
sqlcmd -S server -U user -P password -Q "RESTORE DATABASE aetim FROM DISK='backups/aetim_20250127.bak'"
```

#### 2.2 檔案還原

```bash
# 還原報告檔案
tar -xzf backups/reports_20250127.tar.gz

# 還原設定檔案
tar -xzf backups/config_20250127.tar.gz
```

## 安全性檢查

### 1. 定期安全性掃描

```bash
# 執行安全性掃描
cd backend
python scripts/security_scan.py
```

### 2. 依賴套件更新

```bash
# 檢查過時的套件
pip list --outdated

# 更新套件
pip install --upgrade package_name
```

### 3. 日誌審查

定期審查日誌，檢查異常活動：

```bash
# 檢查錯誤日誌
grep ERROR logs/app.log

# 檢查認證失敗
grep "authentication failed" logs/app.log
```

## 效能優化

### 1. 資料庫優化

- 定期重建索引
- 更新統計資訊
- 清理過期資料

### 2. 快取優化

- 調整快取 TTL
- 監控快取命中率
- 清理無效快取

### 3. API 優化

- 監控 API 回應時間
- 優化慢查詢
- 調整速率限制

## 相關文件

- **系統架構文件**：`docs/ARCHITECTURE.md`
- **部署文件**：`docs/DEPLOYMENT.md`
- **維護手冊**：`docs/MAINTENANCE.md`

