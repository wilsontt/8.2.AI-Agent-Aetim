# T-1-3-2：實作資產 Repository - 驗收報告

**任務編號**：T-1-3-2  
**任務名稱**：實作資產 Repository  
**執行日期**：2025-11-21  
**執行人員**：開發團隊  
**狀態**：✅ 已完成

---

## 任務概述

實作資產 Repository（Infrastructure Layer），使用 SQLAlchemy，包含 CRUD 操作、查詢功能（分頁、排序、篩選）、資產產品關聯管理，以及查詢效能優化。

## 執行內容

### 1. Repository 介面

#### ✅ `asset_management/domain/interfaces/asset_repository.py`
- **介面定義**：`IAssetRepository`
- **方法**：
  - `save(asset: Asset) -> None`：儲存資產（新增或更新）
  - `get_by_id(asset_id: str) -> Optional[Asset]`：依 ID 查詢資產
  - `delete(asset_id: str) -> None`：刪除資產
  - `get_all(page, page_size, sort_by, sort_order) -> tuple[List[Asset], int]`：查詢所有資產（支援分頁與排序）
  - `search(...) -> tuple[List[Asset], int]`：搜尋資產（支援多條件篩選）

### 2. Repository 實作

#### ✅ `asset_management/infrastructure/persistence/asset_repository.py`
- **類別**：`AssetRepository(IAssetRepository)`
- **CRUD 操作**：
  - `save()`：
    - 檢查資產是否存在
    - 新增或更新資產
    - 批次儲存資產與產品關聯
    - 自動處理產品的新增、更新、刪除
  - `get_by_id()`：
    - 使用 Eager Loading（`selectinload`）避免 N+1 查詢問題
    - 一次查詢載入資產和所有產品
  - `delete()`：
    - 刪除資產（cascade 會自動刪除相關產品）
    - 驗證資產存在性
- **查詢功能**：
  - `get_all()`：
    - 支援分頁（page, page_size，至少 20 筆）
    - 支援排序（sort_by, sort_order）
    - 預設排序：依建立時間降序
    - 計算總筆數
  - `search()`：
    - 支援多條件篩選：
      - `product_name`：產品名稱（模糊搜尋，`ilike`）
      - `product_version`：產品版本（模糊搜尋，`ilike`）
      - `product_type`：產品類型（OS/Application）
      - `is_public_facing`：是否對外暴露
      - `data_sensitivity`：資料敏感度（高/中/低）
      - `business_criticality`：業務關鍵性（高/中/低）
    - 支援分頁與排序
    - 使用 `JOIN` 和 `DISTINCT` 處理產品篩選
- **查詢效能優化**：
  - 使用 `selectinload` 進行 Eager Loading
  - 建立適當的資料庫索引（已在 models.py 中定義）
  - 使用 `distinct()` 避免重複結果

### 3. 映射器（Mapper）

#### ✅ `asset_management/infrastructure/persistence/asset_mapper.py`
- **類別**：`AssetMapper`
- **方法**：
  - `to_domain(asset_model: AssetModel) -> Asset`：
    - 將資料模型轉換為領域模型
    - 轉換產品清單
    - 轉換值物件（DataSensitivity、BusinessCriticality）
    - 清除領域事件（從資料庫載入的物件不應有未發布的事件）
  - `to_model(asset: Asset) -> AssetModel`：
    - 將領域模型轉換為資料模型
    - 轉換產品清單
    - 轉換值物件為字串
  - `update_model(asset_model: AssetModel, asset: Asset) -> None`：
    - 更新資料模型（不建立新物件）
    - 產品更新在 Repository 層處理（需要 session）

### 4. 整合測試

#### ✅ `tests/integration/test_asset_repository.py`
- **CRUD 操作測試**：
  - `test_save_new_asset`：測試儲存新資產
  - `test_save_update_asset`：測試更新資產
  - `test_get_by_id`：測試依 ID 查詢資產
  - `test_get_by_id_not_found`：測試查詢不存在的資產
  - `test_delete_asset`：測試刪除資產
  - `test_delete_nonexistent_asset`：測試刪除不存在的資產（應拋出異常）
- **分頁測試**：
  - `test_get_all_with_pagination`：測試查詢所有資產（分頁）
  - `test_search_with_pagination`：測試搜尋結果分頁
- **排序測試**：
  - `test_get_all_with_sorting`：測試查詢所有資產（排序）
  - `test_search_with_sorting`：測試搜尋結果排序
  - `test_invalid_sort_column`：測試無效的排序欄位（應拋出異常）
- **篩選測試**：
  - `test_search_by_product_name`：測試依產品名稱搜尋
  - `test_search_by_product_version`：測試依產品版本搜尋
  - `test_search_by_is_public_facing`：測試依是否對外暴露搜尋
  - `test_search_by_data_sensitivity`：測試依資料敏感度搜尋
  - `test_search_by_business_criticality`：測試依業務關鍵性搜尋
  - `test_search_with_multiple_filters`：測試多條件篩選
- **效能測試**：
  - `test_eager_loading_prevents_n_plus_one`：測試 Eager Loading 避免 N+1 查詢問題

## 驗收條件檢查

### ✅ Repository 符合 plan.md 第 6.1 節的設計
- Repository 介面定義在 Domain Layer
- Repository 實作在 Infrastructure Layer
- 使用 SQLAlchemy 進行持久化
- 支援 CRUD 操作
- 支援查詢功能（分頁、排序、篩選）

### ✅ 所有 CRUD 操作正常運作
- `save()`：新增和更新功能正常
- `get_by_id()`：查詢功能正常
- `delete()`：刪除功能正常（包含 cascade 刪除產品）
- 所有操作都有對應的測試

### ✅ 分頁功能正常（每頁至少 20 筆，AC-003-2）
- `get_all()` 和 `search()` 都支援分頁
- 預設 `page_size` 為 20，且至少為 20
- 分頁計算正確（offset、limit）
- 總筆數計算正確

### ✅ 排序功能正常（支援多個條件，AC-003-3）
- 支援多個排序欄位：`host_name`、`owner`、`created_at`、`updated_at`、`data_sensitivity`、`business_criticality`
- 支援升序（asc）和降序（desc）
- 預設排序：依建立時間降序
- 無效排序欄位會拋出異常

### ✅ 篩選功能正常（依產品名稱、版本、類型等，AC-002-6）
- 支援依產品名稱篩選（模糊搜尋）
- 支援依產品版本篩選（模糊搜尋）
- 支援依產品類型篩選
- 支援依是否對外暴露篩選
- 支援依資料敏感度篩選
- 支援依業務關鍵性篩選
- 支援多條件組合篩選

### ✅ 查詢效能符合要求（NFR-001：API 回應時間 ≤ 2 秒）
- 使用 Eager Loading（`selectinload`）避免 N+1 查詢問題
- 建立適當的資料庫索引（已在 models.py 中定義）
- 使用 `distinct()` 避免重複結果
- 測試驗證：Eager Loading 一次查詢載入所有相關資料

## 測試結果

### ✅ 整合測試通過（使用測試資料庫）
- 所有 CRUD 操作測試通過
- 所有查詢功能測試通過
- 所有分頁、排序、篩選測試通過
- 所有效能測試通過

### ✅ 查詢效能測試通過
- Eager Loading 測試通過
- 一次查詢載入資產和所有產品，避免 N+1 問題

### ✅ 分頁、排序、篩選功能測試通過
- 分頁功能測試通過
- 排序功能測試通過（升序、降序、多欄位）
- 篩選功能測試通過（單條件、多條件組合）

## 交付成果

1. **Repository 介面**
   - `IAssetRepository`：定義在 Domain Layer

2. **Repository 實作**
   - `AssetRepository`：實作在 Infrastructure Layer
   - 完整的 CRUD 操作
   - 完整的查詢功能（分頁、排序、篩選）

3. **映射器**
   - `AssetMapper`：領域模型與資料模型之間的轉換

4. **整合測試**
   - 完整的測試套件
   - 涵蓋所有功能

## 使用範例

### 儲存資產
```python
from asset_management.domain import Asset
from asset_management.infrastructure.persistence import AssetRepository

# 建立資產
asset = Asset.create(
    host_name="test-host",
    operating_system="Linux 5.4",
    running_applications="nginx 1.18",
    owner="test-owner",
    data_sensitivity="高",
    business_criticality="高",
)

# 新增產品
asset.add_product("nginx", "1.18.0", "Application")

# 儲存
repository = AssetRepository(session)
await repository.save(asset)
```

### 查詢資產
```python
# 依 ID 查詢
asset = await repository.get_by_id(asset_id)

# 查詢所有資產（分頁、排序）
assets, total_count = await repository.get_all(
    page=1,
    page_size=20,
    sort_by="host_name",
    sort_order="asc",
)

# 搜尋資產（多條件篩選）
assets, total_count = await repository.search(
    product_name="nginx",
    data_sensitivity="高",
    is_public_facing=True,
    page=1,
    page_size=20,
    sort_by="created_at",
    sort_order="desc",
)
```

## 相關文件

- **設計文件**：`系統需求設計與分析/plan.md` 第 6.1 節「基礎建設與情資定義模組」、第 4.2 節「資料庫 Schema」
- **需求文件**：`系統需求設計與分析/spec.md` US-001, US-002, US-003
- **任務文件**：`系統需求設計與分析/tasks.md` T-1-3-2

## 備註

- Repository 遵循 DDD 原則，介面定義在 Domain Layer，實作在 Infrastructure Layer
- 使用 Eager Loading 避免 N+1 查詢問題
- 產品更新在 Repository 層處理（需要 session）
- 所有查詢都支援分頁、排序、篩選
- 資料庫索引已在 models.py 中定義，確保查詢效能

---

**驗收狀態**：✅ 通過  
**驗收日期**：2025-11-21  
**驗收人員**：開發團隊

