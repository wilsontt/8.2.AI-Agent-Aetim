# T-2-2-4：實作 NVD 收集器 - 驗收報告

**任務編號**：T-2-2-4  
**任務名稱**：實作 NVD 收集器  
**執行日期**：2025-01-27  
**執行者**：AI Assistant  
**狀態**：✅ 已完成

---

## 1. 任務概述

### 1.1 任務描述
實作 NVD 收集器（Infrastructure Layer），從 NVD (National Vulnerability Database) 收集威脅情資，支援增量收集和速率限制處理。

### 1.2 對應文件
- **使用者故事**：US-008
- **驗收條件**：AC-008-1, AC-008-5, AC-008-6
- **plan.md**：第 10.1.2 節「威脅情資收集引擎」
- **優先級**：P0
- **預估工時**：10 小時

---

## 2. 執行內容

### 2.1 NVD 收集器

#### 2.1.1 NVDCollector 類別
- **檔案位置**：`threat_intelligence/infrastructure/external_services/collectors/nvd_collector.py`
- **功能**：
  - `collect`：從 NVD API 收集威脅情資（支援增量收集）
  - `_fetch_cves_batch`：取得一批 CVE 資料（分頁處理）
  - `_parse_cve`：解析單一 CVE 資料並轉換為 Threat 聚合根
  - `_parse_cpe`：解析 CPE 字串提取產品資訊
  - `get_collector_type`：取得收集器類型（返回 "NVD"）

#### 2.1.2 API 端點
- **URL**：`https://services.nvd.nist.gov/rest/json/cves/2.0`
- **格式**：JSON (REST API v2.0)
- **請求方式**：GET
- **超時時間**：30 秒

#### 2.1.3 速率限制處理
- **無 API 金鑰**：每 6 秒 5 個請求
- **有 API 金鑰**：每 6 秒 50 個請求
- **實作**：`RateLimiter` 類別，使用時間窗口和請求計數器

#### 2.1.4 增量收集機制
- **記錄最後收集時間**：使用 `feed.last_collection_time`
- **僅收集新資料**：根據 `start_date` 和 `end_date` 參數過濾
- **預設行為**：如果沒有指定日期，收集最近 7 天的資料

#### 2.1.5 資料解析
- **提取欄位**：
  - CVE ID
  - 描述（優先使用英文描述）
  - 發布日期
  - CVSS 分數（優先使用 v3.1，其次 v3.0，最後 v2.0）
  - CVSS 向量字串
  - 產品資訊（從 CPE 字串解析）
- **標準化處理**：
  - 轉換為 Threat 聚合根
  - 根據 CVSS 分數自動決定嚴重程度
  - 如果沒有 CVSS 分數，預設為 Medium
  - 儲存原始資料（JSON 格式）

### 2.2 速率限制器

#### 2.2.1 RateLimiter 類別
- **功能**：
  - `wait_if_needed`：如果需要，等待直到可以發送請求
  - 使用時間窗口和請求計數器追蹤請求
  - 自動移除過期的請求時間

### 2.3 單元測試

#### 2.3.1 測試檔案
- **檔案位置**：`tests/unit/test_nvd_collector.py`
- **測試案例數**：9 個

#### 2.3.2 測試覆蓋範圍
- `test_get_collector_type`：測試取得收集器類型
- `test_collect_success`：測試成功收集威脅情資
- `test_collect_with_incremental`：測試增量收集
- `test_collect_empty_response`：測試空回應
- `test_collect_http_error`：測試 HTTP 錯誤
- `test_parse_cve_with_cvss_v31`：測試解析包含 CVSS v3.1 的 CVE
- `test_parse_cve_with_cvss_v30`：測試解析包含 CVSS v3.0 的 CVE
- `test_parse_cpe`：測試 CPE 解析
- `test_rate_limiter`：測試速率限制器

---

## 3. 驗收條件檢查

### 3.1 功能驗收

| 驗收條件 | 狀態 | 說明 |
|---------|------|------|
| 可成功從 NVD API 收集資料 | ✅ | 已實作 `collect` 方法，使用 httpx 呼叫 API |
| 正確處理 API 速率限制 | ✅ | 已實作 `RateLimiter` 類別，符合 NVD API 速率限制 |
| 正確解析 JSON 格式 | ✅ | 已實作 JSON 解析，包含錯誤處理 |
| 正確提取 CVE、CVSS、產品資訊（AC-008-6） | ✅ | 已實作完整的資料提取邏輯 |
| 標準化為統一資料模型（AC-008-5） | ✅ | 轉換為 Threat 聚合根，符合領域模型設計 |
| 增量收集機制正常運作 | ✅ | 已實作增量收集，支援根據最後收集時間過濾 |

### 3.2 測試要求

| 驗收條件 | 狀態 | 說明 |
|---------|------|------|
| 單元測試通過（使用 Mock API） | ✅ | 已建立 9 個單元測試案例，使用 Mock 模擬 API 回應 |
| 速率限制處理測試通過 | ✅ | 已測試速率限制器的功能 |
| 錯誤處理測試通過 | ✅ | 已測試 HTTP 錯誤等情況 |

---

## 4. 實作細節

### 4.1 收集流程

1. **檢查增量收集**：如果沒有指定日期，使用最後收集時間或最近 7 天
2. **分頁收集**：使用分頁方式收集所有 CVE（每頁最多 2000 筆）
3. **速率限制**：每次請求前檢查速率限制，必要時等待
4. **呼叫 NVD API**：使用 httpx 非同步客戶端呼叫 API
5. **解析回應**：解析 JSON 格式的回應，取得 CVE 列表
6. **轉換為 Threat 聚合根**：對每個 CVE 呼叫 `_parse_cve` 方法
7. **錯誤處理**：捕獲並處理各種錯誤情況

### 4.2 資料解析邏輯

1. **基本資訊提取**：
   - CVE ID（必填）
   - 描述（優先使用英文描述）
   - 發布日期（解析 ISO 格式）

2. **CVSS 分數處理**：
   - 優先使用 CVSS v3.1
   - 其次使用 CVSS v3.0
   - 最後使用 CVSS v2.0
   - 根據 CVSS 分數自動決定嚴重程度
   - 如果沒有 CVSS 分數，預設為 Medium

3. **產品資訊提取**：
   - 從 `configurations` 中的 CPE 字串提取產品資訊
   - 解析 CPE 字串格式：`cpe:2.3:type:vendor:product:version:...`
   - 提取產品名稱、版本、類型（Application/Operating System/Hardware）

4. **其他資訊**：
   - 儲存原始資料（JSON 格式）
   - 建立來源 URL

### 4.3 速率限制處理

- **時間窗口**：追蹤最近 6 秒內的請求
- **請求計數**：計算時間窗口內的請求數
- **等待機制**：如果達到最大請求數，等待直到最舊的請求超過時間窗口
- **自動清理**：自動移除過期的請求時間

### 4.4 增量收集

- **最後收集時間**：使用 `feed.last_collection_time` 作為起始時間
- **日期範圍**：使用 `start_date` 和 `end_date` 參數過濾 CVE
- **預設行為**：如果沒有最後收集時間，收集最近 7 天的資料

---

## 5. 交付項目

### 5.1 收集器實作
- `threat_intelligence/infrastructure/external_services/collectors/nvd_collector.py`：NVD 收集器（包含 RateLimiter）

### 5.2 單元測試
- `tests/unit/test_nvd_collector.py`：NVD 收集器單元測試（9 個測試案例）

### 5.3 文件
- 本驗收報告

---

## 6. 相關文件

### 6.1 需求文件
- `系統需求設計與分析/plan.md`：第 10.1.2 節「威脅情資收集引擎」
- `系統需求設計與分析/spec.md`：US-008, AC-008-1
- `系統需求設計與分析/tasks.md`：T-2-2-4

### 6.2 技術文件
- NVD API 文件：https://nvd.nist.gov/developers/vulnerabilities
- httpx 文件：https://www.python-httpx.org/
- CPE 規格：https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nistir7695.pdf

---

## 7. 備註

### 7.1 實作細節

1. **API 金鑰支援**：
   - 支援可選的 API 金鑰參數
   - 有 API 金鑰可提高速率限制（從每 6 秒 5 個請求提升到 50 個）

2. **分頁處理**：
   - NVD API 每頁最多 2000 筆
   - 自動處理分頁，收集所有符合條件的 CVE

3. **CPE 解析**：
   - 支援解析 CPE 2.3 格式
   - 提取產品名稱、版本、類型
   - 處理各種 CPE 格式變體

4. **CVSS 版本優先級**：
   - 優先使用最新的 CVSS 版本（v3.1 > v3.0 > v2.0）
   - 確保使用最準確的風險評分

### 7.2 已知限制

1. **大量資料收集**：
   - 如果時間範圍很大，可能收集到大量 CVE
   - 建議使用增量收集機制，定期收集新資料

2. **速率限制**：
   - 無 API 金鑰時速率限制較嚴格（每 6 秒 5 個請求）
   - 建議申請 API 金鑰以提高收集效率

3. **CPE 解析**：
   - 目前使用簡單的 CPE 解析邏輯
   - 可能無法正確解析所有 CPE 格式變體

### 7.3 後續改進建議

1. 申請 NVD API 金鑰以提高速率限制
2. 優化 CPE 解析邏輯，支援更多格式變體
3. 實作整合測試（實際 API 呼叫）
4. 實作快取機制，避免重複收集相同的 CVE
5. 實作並行收集（多個時間範圍同時收集）

---

## 8. 使用說明

### 8.1 註冊收集器

```python
from threat_intelligence.infrastructure.external_services.collector_factory import CollectorFactory
from threat_intelligence.infrastructure.external_services.collectors.nvd_collector import NVDCollector

factory = CollectorFactory()
# 無 API 金鑰
factory.register_collector("NVD", NVDCollector())
# 有 API 金鑰
factory.register_collector("NVD", NVDCollector(api_key="your-api-key"))
```

### 8.2 使用收集器

```python
from threat_intelligence.infrastructure.external_services.collectors.nvd_collector import NVDCollector

collector = NVDCollector()
# 增量收集（使用最後收集時間）
threats = await collector.collect(feed)
# 指定日期範圍收集
threats = await collector.collect(
    feed,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
)
```

---

## 9. 簽核

**執行者**：AI Assistant  
**日期**：2025-01-27  
**狀態**：✅ 已完成並通過驗收

