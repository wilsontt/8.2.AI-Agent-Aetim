"""
資產服務整合測試

測試資產服務的 CRUD 操作和查詢功能。
"""

import pytest
from asset_management.application.services.asset_service import AssetService
from asset_management.application.services.asset_import_service import AssetImportService
from asset_management.application.dtos.asset_dto import (
    CreateAssetRequest,
    UpdateAssetRequest,
    AssetSearchRequest,
)
from asset_management.infrastructure.persistence import AssetRepository
from asset_management.domain.domain_services.asset_parsing_service import AssetParsingService


@pytest.mark.integration
class TestAssetService:
    """測試資產服務"""
    
    @pytest.fixture
    def asset_service(self, db_session):
        """建立資產服務"""
        repository = AssetRepository(db_session)
        parsing_service = AssetParsingService()
        return AssetService(repository, parsing_service)
    
    async def test_create_asset(self, asset_service):
        """測試建立資產"""
        request = CreateAssetRequest(
            host_name="test-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18.0",
            owner="test-owner",
            data_sensitivity="高",
            business_criticality="高",
        )
        
        asset_id = await asset_service.create_asset(request, "user1")
        
        assert asset_id is not None
        
        # 驗證資產已建立
        asset = await asset_service.get_asset_by_id(asset_id)
        assert asset is not None
        assert asset.host_name == "test-host"
        assert len(asset.products) > 0  # 應該有解析出產品
    
    async def test_update_asset(self, asset_service):
        """測試更新資產"""
        # 建立資產
        create_request = CreateAssetRequest(
            host_name="test-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18.0",
            owner="test-owner",
            data_sensitivity="中",
            business_criticality="中",
        )
        asset_id = await asset_service.create_asset(create_request, "user1")
        
        # 更新資產
        update_request = UpdateAssetRequest(
            host_name="updated-host",
            owner="updated-owner",
        )
        await asset_service.update_asset(asset_id, update_request, "user2")
        
        # 驗證更新
        asset = await asset_service.get_asset_by_id(asset_id)
        assert asset.host_name == "updated-host"
        assert asset.owner == "updated-owner"
        assert asset.updated_by == "user2"
    
    async def test_delete_asset(self, asset_service):
        """測試刪除資產"""
        # 建立資產
        create_request = CreateAssetRequest(
            host_name="test-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18.0",
            owner="test-owner",
            data_sensitivity="中",
            business_criticality="中",
        )
        asset_id = await asset_service.create_asset(create_request, "user1")
        
        # 刪除資產（需要確認）
        await asset_service.delete_asset(asset_id, "user1", confirm=True)
        
        # 驗證已刪除
        asset = await asset_service.get_asset_by_id(asset_id)
        assert asset is None
    
    async def test_delete_asset_without_confirm(self, asset_service):
        """測試刪除資產（未確認，應拋出異常）"""
        # 建立資產
        create_request = CreateAssetRequest(
            host_name="test-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18.0",
            owner="test-owner",
            data_sensitivity="中",
            business_criticality="中",
        )
        asset_id = await asset_service.create_asset(create_request, "user1")
        
        # 嘗試刪除（未確認）
        with pytest.raises(ValueError, match="刪除資產需要確認"):
            await asset_service.delete_asset(asset_id, "user1", confirm=False)
    
    async def test_batch_delete_assets(self, asset_service):
        """測試批次刪除資產"""
        # 建立多筆資產
        asset_ids = []
        for i in range(5):
            create_request = CreateAssetRequest(
                host_name=f"test-host-{i}",
                operating_system="Linux 5.4",
                running_applications="nginx 1.18.0",
                owner="test-owner",
                data_sensitivity="中",
                business_criticality="中",
            )
            asset_id = await asset_service.create_asset(create_request, "user1")
            asset_ids.append(asset_id)
        
        # 批次刪除
        result = await asset_service.batch_delete_assets(asset_ids, "user1", confirm=True)
        
        assert result["success_count"] == 5
        assert result["failure_count"] == 0
        
        # 驗證已刪除
        for asset_id in asset_ids:
            asset = await asset_service.get_asset_by_id(asset_id)
            assert asset is None
    
    async def test_get_assets_with_pagination(self, asset_service):
        """測試查詢資產清單（分頁）"""
        # 建立多筆資產
        for i in range(25):
            create_request = CreateAssetRequest(
                host_name=f"test-host-{i}",
                operating_system="Linux 5.4",
                running_applications="nginx 1.18.0",
                owner="test-owner",
                data_sensitivity="中",
                business_criticality="中",
            )
            await asset_service.create_asset(create_request, "user1")
        
        # 查詢第一頁
        response = await asset_service.get_assets(page=1, page_size=20)
        assert len(response.data) == 20
        assert response.total_count == 25
        assert response.total_pages == 2
        
        # 查詢第二頁
        response = await asset_service.get_assets(page=2, page_size=20)
        assert len(response.data) == 5
        assert response.total_count == 25
    
    async def test_search_assets(self, asset_service):
        """測試搜尋資產"""
        # 建立資產
        create_request1 = CreateAssetRequest(
            host_name="host-1",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18.0",
            owner="owner-1",
            data_sensitivity="高",
            business_criticality="高",
            is_public_facing=True,
        )
        await asset_service.create_asset(create_request1, "user1")
        
        create_request2 = CreateAssetRequest(
            host_name="host-2",
            operating_system="Linux 5.4",
            running_applications="apache 2.4.0",
            owner="owner-2",
            data_sensitivity="中",
            business_criticality="中",
            is_public_facing=False,
        )
        await asset_service.create_asset(create_request2, "user1")
        
        # 搜尋高敏感度資產
        search_request = AssetSearchRequest(
            data_sensitivity="高",
            page=1,
            page_size=20,
        )
        response = await asset_service.search_assets(search_request)
        assert response.total_count == 1
        assert response.data[0].data_sensitivity == "高"
        
        # 搜尋對外暴露資產
        search_request = AssetSearchRequest(
            is_public_facing=True,
            page=1,
            page_size=20,
        )
        response = await asset_service.search_assets(search_request)
        assert response.total_count == 1
        assert response.data[0].is_public_facing is True


@pytest.mark.integration
class TestAssetImportService:
    """測試資產匯入服務"""
    
    @pytest.fixture
    def asset_import_service(self, db_session):
        """建立資產匯入服務"""
        repository = AssetRepository(db_session)
        parsing_service = AssetParsingService()
        asset_service = AssetService(repository, parsing_service)
        return AssetImportService(asset_service)
    
    async def test_preview_import(self, asset_import_service):
        """測試匯入預覽"""
        csv_content = """ITEM,IP,主機名稱,作業系統(含版本),運行的應用程式(含版本),負責人,資料敏感度,是否對外(Public-facing),業務關鍵性
1,10.6.82.31,test-host,Linux 5.4,nginx 1.18.0,test-owner,高,Y,高"""
        
        preview = await asset_import_service.preview_import(csv_content)
        
        assert preview.total_count == 1
        assert preview.valid_count == 1
        assert preview.invalid_count == 0
        assert len(preview.preview_data) == 1
    
    async def test_preview_import_with_errors(self, asset_import_service):
        """測試匯入預覽（包含錯誤）"""
        csv_content = """ITEM,IP,主機名稱,作業系統(含版本),運行的應用程式(含版本),負責人,資料敏感度,是否對外(Public-facing),業務關鍵性
1,10.6.82.31,,Linux 5.4,nginx 1.18.0,test-owner,高,Y,高"""
        
        preview = await asset_import_service.preview_import(csv_content)
        
        assert preview.total_count == 1
        assert preview.valid_count == 0
        assert preview.invalid_count > 0
        assert len(preview.errors) > 0
    
    async def test_import_assets(self, asset_import_service):
        """測試匯入資產"""
        csv_content = """ITEM,IP,主機名稱,作業系統(含版本),運行的應用程式(含版本),負責人,資料敏感度,是否對外(Public-facing),業務關鍵性
1,10.6.82.31,test-host-1,Linux 5.4,nginx 1.18.0,test-owner,高,Y,高
2,10.6.82.32,test-host-2,Linux 5.4,apache 2.4.0,test-owner,中,N,中"""
        
        result = await asset_import_service.import_assets(csv_content, "user1")
        
        assert result.total_count == 2
        assert result.success_count == 2
        assert result.failure_count == 0
    
    async def test_import_assets_with_errors(self, asset_import_service):
        """測試匯入資產（包含錯誤）"""
        csv_content = """ITEM,IP,主機名稱,作業系統(含版本),運行的應用程式(含版本),負責人,資料敏感度,是否對外(Public-facing),業務關鍵性
1,10.6.82.31,,Linux 5.4,nginx 1.18.0,test-owner,高,Y,高"""
        
        result = await asset_import_service.import_assets(csv_content, "user1")
        
        assert result.total_count == 1
        assert result.success_count == 0
        assert result.failure_count == 1

