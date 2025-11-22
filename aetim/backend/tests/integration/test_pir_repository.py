"""
PIR Repository 整合測試

測試 PIR Repository 與資料庫的整合。
"""

import pytest
from analysis_assessment.domain.aggregates.pir import PIR
from analysis_assessment.infrastructure.persistence.pir_repository import PIRRepository
from analysis_assessment.infrastructure.persistence.pir_mapper import PIRMapper
from analysis_assessment.infrastructure.persistence.models import PIR as PIRModel


@pytest.mark.asyncio
async def test_save_new_pir(db_session):
    """測試儲存新的 PIR"""
    repository = PIRRepository(db_session)
    
    pir = PIR.create(
        name="測試 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
    )
    
    await repository.save(pir)
    
    # 驗證已儲存
    saved_pir = await repository.get_by_id(pir.id)
    assert saved_pir is not None
    assert saved_pir.name == "測試 PIR"
    assert saved_pir.priority.value == "高"


@pytest.mark.asyncio
async def test_save_existing_pir(db_session):
    """測試更新現有的 PIR"""
    repository = PIRRepository(db_session)
    
    # 建立並儲存 PIR
    pir = PIR.create(
        name="測試 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
    )
    await repository.save(pir)
    
    # 更新 PIR
    pir.update(name="更新後的 PIR", updated_by="user1")
    await repository.save(pir)
    
    # 驗證已更新
    saved_pir = await repository.get_by_id(pir.id)
    assert saved_pir.name == "更新後的 PIR"
    assert saved_pir.updated_by == "user1"


@pytest.mark.asyncio
async def test_get_by_id(db_session):
    """測試依 ID 查詢 PIR"""
    repository = PIRRepository(db_session)
    
    pir = PIR.create(
        name="測試 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
    )
    await repository.save(pir)
    
    # 查詢
    found_pir = await repository.get_by_id(pir.id)
    assert found_pir is not None
    assert found_pir.id == pir.id
    assert found_pir.name == "測試 PIR"
    
    # 查詢不存在的 PIR
    not_found = await repository.get_by_id("non-existent-id")
    assert not_found is None


@pytest.mark.asyncio
async def test_delete_pir(db_session):
    """測試刪除 PIR"""
    repository = PIRRepository(db_session)
    
    pir = PIR.create(
        name="測試 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
    )
    await repository.save(pir)
    
    # 刪除
    await repository.delete(pir.id)
    
    # 驗證已刪除
    deleted_pir = await repository.get_by_id(pir.id)
    assert deleted_pir is None
    
    # 刪除不存在的 PIR 應拋出錯誤
    with pytest.raises(ValueError):
        await repository.delete("non-existent-id")


@pytest.mark.asyncio
async def test_get_all_with_pagination(db_session):
    """測試查詢所有 PIR（分頁）"""
    repository = PIRRepository(db_session)
    
    # 建立多個 PIR
    for i in range(5):
        pir = PIR.create(
            name=f"測試 PIR {i}",
            description="測試描述",
            priority="高",
            condition_type="產品名稱",
            condition_value="VMware",
        )
        await repository.save(pir)
    
    # 查詢第一頁（每頁 2 筆）
    pirs, total_count = await repository.get_all(page=1, page_size=2)
    
    assert len(pirs) == 2
    assert total_count == 5
    
    # 查詢第二頁
    pirs, total_count = await repository.get_all(page=2, page_size=2)
    
    assert len(pirs) == 2
    assert total_count == 5


@pytest.mark.asyncio
async def test_get_all_with_sorting(db_session):
    """測試查詢所有 PIR（排序）"""
    repository = PIRRepository(db_session)
    
    # 建立多個 PIR
    priorities = ["高", "中", "低"]
    for priority in priorities:
        pir = PIR.create(
            name=f"測試 PIR {priority}",
            description="測試描述",
            priority=priority,
            condition_type="產品名稱",
            condition_value="VMware",
        )
        await repository.save(pir)
    
    # 依名稱排序（升序）
    pirs, _ = await repository.get_all(sort_by="name", sort_order="asc")
    
    assert len(pirs) == 3
    assert pirs[0].name == "測試 PIR 中"  # 中文字排序


@pytest.mark.asyncio
async def test_get_enabled_pirs(db_session):
    """測試查詢啟用的 PIR"""
    repository = PIRRepository(db_session)
    
    # 建立啟用的 PIR
    enabled_pir = PIR.create(
        name="啟用的 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
        is_enabled=True,
    )
    await repository.save(enabled_pir)
    
    # 建立停用的 PIR
    disabled_pir = PIR.create(
        name="停用的 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
        is_enabled=False,
    )
    await repository.save(disabled_pir)
    
    # 查詢啟用的 PIR
    enabled_pirs = await repository.get_enabled_pirs()
    
    assert len(enabled_pirs) == 1
    assert enabled_pirs[0].id == enabled_pir.id
    assert enabled_pirs[0].is_enabled is True


@pytest.mark.asyncio
async def test_find_matching_pirs(db_session):
    """測試查詢符合威脅資料的 PIR"""
    repository = PIRRepository(db_session)
    
    # 建立多個 PIR
    pir1 = PIR.create(
        name="VMware PIR",
        description="VMware 相關威脅",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
        is_enabled=True,
    )
    await repository.save(pir1)
    
    pir2 = PIR.create(
        name="CVE-2024 PIR",
        description="2024 年 CVE",
        priority="高",
        condition_type="CVE 編號",
        condition_value="CVE-2024-",
        is_enabled=True,
    )
    await repository.save(pir2)
    
    pir3 = PIR.create(
        name="停用的 PIR",
        description="停用的 PIR",
        priority="高",
        condition_type="產品名稱",
        condition_value="Microsoft",
        is_enabled=False,
    )
    await repository.save(pir3)
    
    # 查詢符合的 PIR（產品名稱匹配）
    matching_pirs = await repository.find_matching_pirs({"product_name": "VMware ESXi"})
    
    assert len(matching_pirs) == 1
    assert matching_pirs[0].id == pir1.id
    
    # 查詢符合的 PIR（CVE 匹配）
    matching_pirs = await repository.find_matching_pirs({"cve": "CVE-2024-1234"})
    
    assert len(matching_pirs) == 1
    assert matching_pirs[0].id == pir2.id
    
    # 停用的 PIR 不應被匹配（業務規則 AC-005-2）
    matching_pirs = await repository.find_matching_pirs({"product_name": "Microsoft SQL Server"})
    
    assert len(matching_pirs) == 0

