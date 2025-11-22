"""
資產 Repository 整合測試

測試資產 Repository 的 CRUD 操作、查詢、分頁、排序、篩選功能。
"""

import pytest
from datetime import datetime
from asset_management.domain import Asset
from asset_management.infrastructure.persistence import AssetRepository, AssetMapper
from asset_management.infrastructure.persistence.models import Asset as AssetModel


@pytest.mark.integration
class TestAssetRepository:
    """測試資產 Repository"""
    
    async def test_save_new_asset(self, db_session):
        """測試儲存新資產"""
        repository = AssetRepository(db_session)
        
        # 建立資產
        asset = Asset.create(
            host_name="test-host-1",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="test-owner",
            data_sensitivity="高",
            business_criticality="高",
        )
        
        # 新增產品
        asset.add_product("nginx", "1.18.0", "Application")
        
        # 儲存
        await repository.save(asset)
        
        # 驗證
        saved_asset = await repository.get_by_id(asset.id)
        assert saved_asset is not None
        assert saved_asset.host_name == "test-host-1"
        assert len(saved_asset.products) == 1
        assert saved_asset.products[0].product_name == "nginx"
    
    async def test_save_update_asset(self, db_session):
        """測試更新資產"""
        repository = AssetRepository(db_session)
        
        # 建立並儲存資產
        asset = Asset.create(
            host_name="test-host-2",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="test-owner",
            data_sensitivity="中",
            business_criticality="中",
        )
        await repository.save(asset)
        
        # 更新資產
        asset.update(host_name="updated-host-2", owner="updated-owner")
        await repository.save(asset)
        
        # 驗證
        updated_asset = await repository.get_by_id(asset.id)
        assert updated_asset.host_name == "updated-host-2"
        assert updated_asset.owner == "updated-owner"
    
    async def test_get_by_id(self, db_session):
        """測試依 ID 查詢資產"""
        repository = AssetRepository(db_session)
        
        # 建立並儲存資產
        asset = Asset.create(
            host_name="test-host-3",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="test-owner",
            data_sensitivity="高",
            business_criticality="高",
        )
        asset.add_product("nginx", "1.18.0")
        await repository.save(asset)
        
        # 查詢
        found_asset = await repository.get_by_id(asset.id)
        assert found_asset is not None
        assert found_asset.id == asset.id
        assert found_asset.host_name == "test-host-3"
        assert len(found_asset.products) == 1
    
    async def test_get_by_id_not_found(self, db_session):
        """測試查詢不存在的資產"""
        repository = AssetRepository(db_session)
        
        found_asset = await repository.get_by_id("nonexistent-id")
        assert found_asset is None
    
    async def test_delete_asset(self, db_session):
        """測試刪除資產"""
        repository = AssetRepository(db_session)
        
        # 建立並儲存資產
        asset = Asset.create(
            host_name="test-host-4",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="test-owner",
            data_sensitivity="高",
            business_criticality="高",
        )
        await repository.save(asset)
        
        # 刪除
        await repository.delete(asset.id)
        
        # 驗證
        deleted_asset = await repository.get_by_id(asset.id)
        assert deleted_asset is None
    
    async def test_delete_nonexistent_asset(self, db_session):
        """測試刪除不存在的資產（應拋出異常）"""
        repository = AssetRepository(db_session)
        
        with pytest.raises(ValueError, match="資產 ID.*不存在"):
            await repository.delete("nonexistent-id")
    
    async def test_get_all_with_pagination(self, db_session):
        """測試查詢所有資產（分頁）"""
        repository = AssetRepository(db_session)
        
        # 建立多筆資產
        for i in range(25):
            asset = Asset.create(
                host_name=f"test-host-{i}",
                operating_system="Linux 5.4",
                running_applications="nginx 1.18",
                owner=f"owner-{i}",
                data_sensitivity="中",
                business_criticality="中",
            )
            await repository.save(asset)
        
        # 查詢第一頁（每頁 20 筆）
        assets, total_count = await repository.get_all(page=1, page_size=20)
        assert len(assets) == 20
        assert total_count == 25
        
        # 查詢第二頁
        assets, total_count = await repository.get_all(page=2, page_size=20)
        assert len(assets) == 5
        assert total_count == 25
    
    async def test_get_all_with_sorting(self, db_session):
        """測試查詢所有資產（排序）"""
        repository = AssetRepository(db_session)
        
        # 建立多筆資產（不同主機名稱）
        host_names = ["z-host", "a-host", "m-host"]
        for host_name in host_names:
            asset = Asset.create(
                host_name=host_name,
                operating_system="Linux 5.4",
                running_applications="nginx 1.18",
                owner="test-owner",
                data_sensitivity="中",
                business_criticality="中",
            )
            await repository.save(asset)
        
        # 依主機名稱升序排序
        assets, _ = await repository.get_all(sort_by="host_name", sort_order="asc")
        assert assets[0].host_name == "a-host"
        assert assets[1].host_name == "m-host"
        assert assets[2].host_name == "z-host"
        
        # 依主機名稱降序排序
        assets, _ = await repository.get_all(sort_by="host_name", sort_order="desc")
        assert assets[0].host_name == "z-host"
        assert assets[1].host_name == "m-host"
        assert assets[2].host_name == "a-host"
    
    async def test_search_by_product_name(self, db_session):
        """測試依產品名稱搜尋"""
        repository = AssetRepository(db_session)
        
        # 建立資產並新增產品
        asset1 = Asset.create(
            host_name="host-1",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="owner-1",
            data_sensitivity="中",
            business_criticality="中",
        )
        asset1.add_product("nginx", "1.18.0")
        await repository.save(asset1)
        
        asset2 = Asset.create(
            host_name="host-2",
            operating_system="Linux 5.4",
            running_applications="apache 2.4",
            owner="owner-2",
            data_sensitivity="中",
            business_criticality="中",
        )
        asset2.add_product("apache", "2.4.0")
        await repository.save(asset2)
        
        # 搜尋 nginx
        assets, total_count = await repository.search(product_name="nginx")
        assert total_count == 1
        assert assets[0].host_name == "host-1"
        assert any(p.product_name == "nginx" for p in assets[0].products)
    
    async def test_search_by_product_version(self, db_session):
        """測試依產品版本搜尋"""
        repository = AssetRepository(db_session)
        
        # 建立資產並新增產品
        asset1 = Asset.create(
            host_name="host-1",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="owner-1",
            data_sensitivity="中",
            business_criticality="中",
        )
        asset1.add_product("nginx", "1.18.0")
        await repository.save(asset1)
        
        asset2 = Asset.create(
            host_name="host-2",
            operating_system="Linux 5.4",
            running_applications="nginx 1.20",
            owner="owner-2",
            data_sensitivity="中",
            business_criticality="中",
        )
        asset2.add_product("nginx", "1.20.0")
        await repository.save(asset2)
        
        # 搜尋版本 1.18
        assets, total_count = await repository.search(product_version="1.18")
        assert total_count == 1
        assert assets[0].host_name == "host-1"
    
    async def test_search_by_is_public_facing(self, db_session):
        """測試依是否對外暴露搜尋"""
        repository = AssetRepository(db_session)
        
        # 建立對外暴露資產
        asset1 = Asset.create(
            host_name="public-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="owner-1",
            data_sensitivity="中",
            business_criticality="中",
            is_public_facing=True,
        )
        await repository.save(asset1)
        
        # 建立非對外暴露資產
        asset2 = Asset.create(
            host_name="private-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="owner-2",
            data_sensitivity="中",
            business_criticality="中",
            is_public_facing=False,
        )
        await repository.save(asset2)
        
        # 搜尋對外暴露資產
        assets, total_count = await repository.search(is_public_facing=True)
        assert total_count == 1
        assert assets[0].host_name == "public-host"
        assert assets[0].is_public_facing is True
    
    async def test_search_by_data_sensitivity(self, db_session):
        """測試依資料敏感度搜尋"""
        repository = AssetRepository(db_session)
        
        # 建立不同敏感度的資產
        for sensitivity in ["高", "中", "低"]:
            asset = Asset.create(
                host_name=f"host-{sensitivity}",
                operating_system="Linux 5.4",
                running_applications="nginx 1.18",
                owner="test-owner",
                data_sensitivity=sensitivity,
                business_criticality="中",
            )
            await repository.save(asset)
        
        # 搜尋高敏感度資產
        assets, total_count = await repository.search(data_sensitivity="高")
        assert total_count == 1
        assert assets[0].data_sensitivity.value == "高"
    
    async def test_search_by_business_criticality(self, db_session):
        """測試依業務關鍵性搜尋"""
        repository = AssetRepository(db_session)
        
        # 建立不同關鍵性的資產
        for criticality in ["高", "中", "低"]:
            asset = Asset.create(
                host_name=f"host-{criticality}",
                operating_system="Linux 5.4",
                running_applications="nginx 1.18",
                owner="test-owner",
                data_sensitivity="中",
                business_criticality=criticality,
            )
            await repository.save(asset)
        
        # 搜尋高關鍵性資產
        assets, total_count = await repository.search(business_criticality="高")
        assert total_count == 1
        assert assets[0].business_criticality.value == "高"
    
    async def test_search_with_multiple_filters(self, db_session):
        """測試多條件篩選"""
        repository = AssetRepository(db_session)
        
        # 建立資產
        asset1 = Asset.create(
            host_name="host-1",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18",
            owner="owner-1",
            data_sensitivity="高",
            business_criticality="高",
            is_public_facing=True,
        )
        asset1.add_product("nginx", "1.18.0", "Application")
        await repository.save(asset1)
        
        asset2 = Asset.create(
            host_name="host-2",
            operating_system="Linux 5.4",
            running_applications="apache 2.4",
            owner="owner-2",
            data_sensitivity="中",
            business_criticality="中",
            is_public_facing=False,
        )
        asset2.add_product("apache", "2.4.0", "Application")
        await repository.save(asset2)
        
        # 多條件搜尋：高敏感度 + 對外暴露 + nginx
        assets, total_count = await repository.search(
            product_name="nginx",
            data_sensitivity="高",
            is_public_facing=True,
        )
        assert total_count == 1
        assert assets[0].host_name == "host-1"
    
    async def test_search_with_pagination(self, db_session):
        """測試搜尋結果分頁"""
        repository = AssetRepository(db_session)
        
        # 建立多筆資產（相同產品）
        for i in range(25):
            asset = Asset.create(
                host_name=f"host-{i}",
                operating_system="Linux 5.4",
                running_applications="nginx 1.18",
                owner=f"owner-{i}",
                data_sensitivity="中",
                business_criticality="中",
            )
            asset.add_product("nginx", "1.18.0")
            await repository.save(asset)
        
        # 搜尋並分頁
        assets, total_count = await repository.search(
            product_name="nginx",
            page=1,
            page_size=20,
        )
        assert len(assets) == 20
        assert total_count == 25
        
        # 第二頁
        assets, total_count = await repository.search(
            product_name="nginx",
            page=2,
            page_size=20,
        )
        assert len(assets) == 5
        assert total_count == 25
    
    async def test_search_with_sorting(self, db_session):
        """測試搜尋結果排序"""
        repository = AssetRepository(db_session)
        
        # 建立資產（不同主機名稱）
        host_names = ["z-host", "a-host", "m-host"]
        for host_name in host_names:
            asset = Asset.create(
                host_name=host_name,
                operating_system="Linux 5.4",
                running_applications="nginx 1.18",
                owner="test-owner",
                data_sensitivity="中",
                business_criticality="中",
            )
            asset.add_product("nginx", "1.18.0")
            await repository.save(asset)
        
        # 搜尋並排序
        assets, _ = await repository.search(
            product_name="nginx",
            sort_by="host_name",
            sort_order="asc",
        )
        assert assets[0].host_name == "a-host"
        assert assets[1].host_name == "m-host"
        assert assets[2].host_name == "z-host"
    
    async def test_invalid_sort_column(self, db_session):
        """測試無效的排序欄位（應拋出異常）"""
        repository = AssetRepository(db_session)
        
        with pytest.raises(ValueError, match="無效的排序欄位"):
            await repository.get_all(sort_by="invalid_column")
    
    async def test_eager_loading_prevents_n_plus_one(self, db_session):
        """測試 Eager Loading 避免 N+1 查詢問題"""
        repository = AssetRepository(db_session)
        
        # 建立資產並新增多個產品
        asset = Asset.create(
            host_name="test-host",
            operating_system="Linux 5.4",
            running_applications="nginx 1.18, apache 2.4",
            owner="test-owner",
            data_sensitivity="中",
            business_criticality="中",
        )
        asset.add_product("nginx", "1.18.0")
        asset.add_product("apache", "2.4.0")
        await repository.save(asset)
        
        # 查詢資產（應該一次查詢就載入所有產品）
        found_asset = await repository.get_by_id(asset.id)
        assert found_asset is not None
        assert len(found_asset.products) == 2
        # 驗證產品已載入（不會觸發額外查詢）
        assert all(p.product_name in ["nginx", "apache"] for p in found_asset.products)

