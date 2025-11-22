"""
資產 API 整合測試

測試資產 API 端點的功能。
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.mark.integration
class TestAssetAPI:
    """測試資產 API"""
    
    def test_create_asset(self):
        """測試建立資產"""
        response = client.post(
            "/api/v1/assets",
            json={
                "host_name": "test-host",
                "operating_system": "Linux 5.4",
                "running_applications": "nginx 1.18.0",
                "owner": "test-owner",
                "data_sensitivity": "高",
                "business_criticality": "高",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["message"] == "資產建立成功"
    
    def test_create_asset_invalid_data(self):
        """測試建立資產（無效資料）"""
        response = client.post(
            "/api/v1/assets",
            json={
                "host_name": "",  # 空字串
                "operating_system": "Linux 5.4",
                "running_applications": "nginx 1.18.0",
                "owner": "test-owner",
                "data_sensitivity": "高",
                "business_criticality": "高",
            },
        )
        
        assert response.status_code == 422  # 驗證錯誤
    
    def test_list_assets(self):
        """測試查詢資產清單"""
        # 先建立一筆資產
        create_response = client.post(
            "/api/v1/assets",
            json={
                "host_name": "test-host-list",
                "operating_system": "Linux 5.4",
                "running_applications": "nginx 1.18.0",
                "owner": "test-owner",
                "data_sensitivity": "中",
                "business_criticality": "中",
            },
        )
        
        # 查詢資產清單
        response = client.get("/api/v1/assets?page=1&page_size=20")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total_count" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
    
    def test_list_assets_with_filter(self):
        """測試查詢資產清單（篩選）"""
        # 先建立一筆對外暴露的資產
        create_response = client.post(
            "/api/v1/assets",
            json={
                "host_name": "test-host-public",
                "operating_system": "Linux 5.4",
                "running_applications": "nginx 1.18.0",
                "owner": "test-owner",
                "data_sensitivity": "高",
                "business_criticality": "高",
                "is_public_facing": True,
            },
        )
        
        # 查詢對外暴露的資產
        response = client.get("/api/v1/assets?is_public_facing=true")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        # 驗證所有結果都是對外暴露的
        for asset in data["data"]:
            assert asset["is_public_facing"] is True
    
    def test_get_asset(self):
        """測試查詢資產詳情"""
        # 先建立一筆資產
        create_response = client.post(
            "/api/v1/assets",
            json={
                "host_name": "test-host-detail",
                "operating_system": "Linux 5.4",
                "running_applications": "nginx 1.18.0",
                "owner": "test-owner",
                "data_sensitivity": "中",
                "business_criticality": "中",
            },
        )
        asset_id = create_response.json()["id"]
        
        # 查詢資產詳情
        response = client.get(f"/api/v1/assets/{asset_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == asset_id
        assert data["host_name"] == "test-host-detail"
        assert "products" in data
    
    def test_get_asset_not_found(self):
        """測試查詢不存在的資產"""
        response = client.get("/api/v1/assets/nonexistent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_update_asset(self):
        """測試更新資產"""
        # 先建立一筆資產
        create_response = client.post(
            "/api/v1/assets",
            json={
                "host_name": "test-host-update",
                "operating_system": "Linux 5.4",
                "running_applications": "nginx 1.18.0",
                "owner": "test-owner",
                "data_sensitivity": "中",
                "business_criticality": "中",
            },
        )
        asset_id = create_response.json()["id"]
        
        # 更新資產
        response = client.put(
            f"/api/v1/assets/{asset_id}",
            json={
                "host_name": "updated-host",
                "owner": "updated-owner",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == asset_id
        assert data["message"] == "資產更新成功"
        
        # 驗證更新
        get_response = client.get(f"/api/v1/assets/{asset_id}")
        assert get_response.json()["host_name"] == "updated-host"
        assert get_response.json()["owner"] == "updated-owner"
    
    def test_delete_asset(self):
        """測試刪除資產"""
        # 先建立一筆資產
        create_response = client.post(
            "/api/v1/assets",
            json={
                "host_name": "test-host-delete",
                "operating_system": "Linux 5.4",
                "running_applications": "nginx 1.18.0",
                "owner": "test-owner",
                "data_sensitivity": "中",
                "business_criticality": "中",
            },
        )
        asset_id = create_response.json()["id"]
        
        # 刪除資產（需要確認）
        response = client.delete(f"/api/v1/assets/{asset_id}?confirm=true")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == asset_id
        assert data["message"] == "資產刪除成功"
        
        # 驗證已刪除
        get_response = client.get(f"/api/v1/assets/{asset_id}")
        assert get_response.status_code == 404
    
    def test_delete_asset_without_confirm(self):
        """測試刪除資產（未確認）"""
        # 先建立一筆資產
        create_response = client.post(
            "/api/v1/assets",
            json={
                "host_name": "test-host-delete-no-confirm",
                "operating_system": "Linux 5.4",
                "running_applications": "nginx 1.18.0",
                "owner": "test-owner",
                "data_sensitivity": "中",
                "business_criticality": "中",
            },
        )
        asset_id = create_response.json()["id"]
        
        # 嘗試刪除（未確認）
        response = client.delete(f"/api/v1/assets/{asset_id}?confirm=false")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_batch_delete_assets(self):
        """測試批次刪除資產"""
        # 先建立多筆資產
        asset_ids = []
        for i in range(3):
            create_response = client.post(
                "/api/v1/assets",
                json={
                    "host_name": f"test-host-batch-{i}",
                    "operating_system": "Linux 5.4",
                    "running_applications": "nginx 1.18.0",
                    "owner": "test-owner",
                    "data_sensitivity": "中",
                    "business_criticality": "中",
                },
            )
            asset_ids.append(create_response.json()["id"])
        
        # 批次刪除
        response = client.post(
            "/api/v1/assets/batch-delete?confirm=true",
            json=asset_ids,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 3
        assert data["failure_count"] == 0
    
    def test_import_assets(self):
        """測試匯入資產"""
        csv_content = """ITEM,IP,主機名稱,作業系統(含版本),運行的應用程式(含版本),負責人,資料敏感度,是否對外(Public-facing),業務關鍵性
1,10.6.82.31,test-host-import,Linux 5.4,nginx 1.18.0,test-owner,高,Y,高"""
        
        response = client.post(
            "/api/v1/assets/import",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_count" in data
        assert "success_count" in data
        assert "failure_count" in data
    
    def test_import_assets_file_too_large(self):
        """測試匯入資產（檔案過大）"""
        # 建立一個超過 10MB 的檔案內容（模擬）
        large_content = "x" * (11 * 1024 * 1024)  # 11MB
        
        response = client.post(
            "/api/v1/assets/import",
            files={"file": ("test.csv", large_content, "text/csv")},
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "FILE_TOO_LARGE" in str(data)
    
    def test_preview_import(self):
        """測試預覽匯入資料"""
        csv_content = """ITEM,IP,主機名稱,作業系統(含版本),運行的應用程式(含版本),負責人,資料敏感度,是否對外(Public-facing),業務關鍵性
1,10.6.82.31,test-host-preview,Linux 5.4,nginx 1.18.0,test-owner,高,Y,高"""
        
        response = client.post(
            "/api/v1/assets/import/preview",
            files={"file": ("test.csv", csv_content, "text/csv")},
            params={"max_preview_rows": 10},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_count" in data
        assert "valid_count" in data
        assert "invalid_count" in data
        assert "preview_data" in data

