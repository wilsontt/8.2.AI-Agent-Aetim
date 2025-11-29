# 部署文件

## 概述

本文件說明 AETIM 系統的部署方式，包含開發環境和生產環境的部署步驟。

## 前置需求

### 系統需求

- **作業系統**：Linux / macOS / Windows
- **Docker**：20.10+
- **Docker Compose**：2.0+
- **記憶體**：至少 4GB RAM
- **磁碟空間**：至少 10GB

### 軟體需求

- **Python**：3.10+（本地開發）
- **Node.js**：18+（本地開發）
- **Redis**：7.0+（或使用 Docker）

## 開發環境部署

### 使用 Docker Compose（推薦）

#### 1. 複製環境變數檔案

```bash
cp .env.example .env
```

#### 2. 設定環境變數

編輯 `.env` 檔案，設定以下變數：

```env
# 資料庫設定
DATABASE_URL=sqlite+aiosqlite:///./data/aetim.db

# Redis 設定
REDIS_URL=redis://redis:6379/0
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# OAuth2 設定
OAUTH2_CLIENT_ID=your_client_id
OAUTH2_CLIENT_SECRET=your_client_secret
OAUTH2_AUTHORIZATION_ENDPOINT=https://idp.example.com/authorize
OAUTH2_TOKEN_ENDPOINT=https://idp.example.com/token
OAUTH2_USERINFO_ENDPOINT=https://idp.example.com/userinfo
OAUTH2_REDIRECT_URI=http://localhost:3030/callback

# 日誌設定
LOG_LEVEL=INFO
ENABLE_FILE_LOGGING=true
```

#### 3. 啟動服務

```bash
docker-compose up -d
```

#### 4. 檢查服務狀態

```bash
docker-compose ps
```

#### 5. 查看日誌

```bash
# 所有服務日誌
docker-compose logs -f

# 特定服務日誌
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### 6. 執行資料庫遷移

```bash
docker-compose exec backend alembic upgrade head
```

#### 7. 初始化角色與權限

```bash
docker-compose exec backend python scripts/seed_roles_and_permissions.py
```

#### 8. 測試服務

```bash
# 健康檢查
curl http://localhost:8000/api/v1/health

# 前端
curl http://localhost:3030
```

### 本地開發（不使用 Docker）

#### 後端設定

```bash
cd backend

# 建立虛擬環境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
export DATABASE_URL=sqlite+aiosqlite:///./data/aetim.db
export REDIS_URL=redis://localhost:6379/0

# 執行資料庫遷移
alembic upgrade head

# 初始化角色與權限
python scripts/seed_roles_and_permissions.py

# 啟動服務
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端設定

```bash
cd frontend

# 安裝依賴
npm install

# 設定環境變數
export NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# 啟動服務
npm run dev
```

#### AI 服務設定

```bash
cd ai_service

# 建立虛擬環境
python3 -m venv .venv
source .venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 啟動服務
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## 生產環境部署

### 1. 準備工作

#### 1.1 環境變數設定

建立生產環境的 `.env` 檔案：

```env
# 資料庫設定（生產環境使用 MS SQL Server）
DATABASE_URL=mssql+pyodbc://user:password@server:1433/database?driver=ODBC+Driver+17+for+SQL+Server

# Redis 設定
REDIS_URL=redis://redis-server:6379/0

# OAuth2 設定
OAUTH2_CLIENT_ID=production_client_id
OAUTH2_CLIENT_SECRET=production_client_secret
OAUTH2_AUTHORIZATION_ENDPOINT=https://idp.production.com/authorize
OAUTH2_TOKEN_ENDPOINT=https://idp.production.com/token
OAUTH2_USERINFO_ENDPOINT=https://idp.production.com/userinfo
OAUTH2_REDIRECT_URI=https://aetim.production.com/callback

# 日誌設定
LOG_LEVEL=INFO
ENABLE_FILE_LOGGING=true

# 環境設定
ENVIRONMENT=production
```

#### 1.2 SSL/TLS 憑證

確保已設定 SSL/TLS 憑證，用於 HTTPS 連線。

### 2. Docker 部署

#### 2.1 建置映像檔

```bash
# 建置後端映像檔
docker build -t aetim-backend:latest -f docker/backend/Dockerfile ./backend

# 建置前端映像檔
docker build -t aetim-frontend:latest -f docker/frontend/Dockerfile ./frontend

# 建置 AI 服務映像檔
docker build -t aetim-ai-service:latest -f docker/ai-service/Dockerfile ./ai_service
```

#### 2.2 使用 Docker Compose 部署

```bash
# 使用生產環境設定檔
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Kubernetes 部署

#### 3.1 建立命名空間

```bash
kubectl create namespace aetim
```

#### 3.2 建立 ConfigMap

```bash
kubectl create configmap aetim-config --from-file=.env -n aetim
```

#### 3.3 建立 Secret

```bash
kubectl create secret generic aetim-secrets \
  --from-literal=oauth2-client-secret=your_secret \
  --from-literal=database-password=your_password \
  -n aetim
```

#### 3.4 部署服務

```bash
# 部署後端服務
kubectl apply -f k8s/backend-deployment.yaml

# 部署前端服務
kubectl apply -f k8s/frontend-deployment.yaml

# 部署 AI 服務
kubectl apply -f k8s/ai-service-deployment.yaml
```

### 4. 資料庫設定

#### 4.1 建立資料庫

```sql
CREATE DATABASE aetim;
```

#### 4.2 執行遷移

```bash
docker-compose exec backend alembic upgrade head
```

#### 4.3 初始化資料

```bash
docker-compose exec backend python scripts/seed_roles_and_permissions.py
```

### 5. 反向代理設定（Nginx）

#### 5.1 Nginx 設定檔

```nginx
server {
    listen 80;
    server_name aetim.production.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name aetim.production.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # 前端
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 後端 API
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # AI 服務
    location /ai/ {
        proxy_pass http://ai-service:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 6. 監控與日誌

#### 6.1 健康檢查

```bash
# 後端健康檢查
curl https://aetim.production.com/api/v1/health

# AI 服務健康檢查
curl https://aetim.production.com/ai/health
```

#### 6.2 日誌收集

設定日誌收集系統（例如：ELK Stack、Loki）收集應用程式日誌。

#### 6.3 監控指標

設定 Prometheus 收集系統指標，並使用 Grafana 進行視覺化。

## 備份與還原

### 1. 資料庫備份

```bash
# SQLite（開發環境）
cp data/aetim.db data/aetim.db.backup

# MS SQL Server（生產環境）
sqlcmd -S server -U user -P password -Q "BACKUP DATABASE aetim TO DISK='backup.bak'"
```

### 2. 資料庫還原

```bash
# SQLite（開發環境）
cp data/aetim.db.backup data/aetim.db

# MS SQL Server（生產環境）
sqlcmd -S server -U user -P password -Q "RESTORE DATABASE aetim FROM DISK='backup.bak'"
```

## 故障排除

### 1. 服務無法啟動

- 檢查環境變數設定
- 檢查日誌：`docker-compose logs`
- 檢查埠號是否被占用

### 2. 資料庫連線失敗

- 檢查資料庫服務是否運行
- 檢查連線字串設定
- 檢查防火牆設定

### 3. Redis 連線失敗

- 檢查 Redis 服務是否運行
- 檢查 Redis URL 設定
- 檢查網路連線

## 相關文件

- **系統架構文件**：`docs/ARCHITECTURE.md`
- **API 文件**：`docs/API.md`
- **操作手冊**：`docs/OPERATIONS.md`

