"""
PIR Service 整合測試

測試 PIR Service 的業務邏輯。
"""

import pytest
from analysis_assessment.application.services.pir_service import PIRService
from analysis_assessment.application.dtos.pir_dto import (
    CreatePIRRequest,
    UpdatePIRRequest,
)
from analysis_assessment.infrastructure.persistence.pir_repository import PIRRepository


@pytest.fixture
def pir_service(db_session):
    """建立 PIR Service"""
    repository = PIRRepository(db_session)
    return PIRService(repository)


@pytest.mark.asyncio
async def test_create_pir(pir_service):
    """測試建立 PIR"""
    request = CreatePIRRequest(
        name="測試 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
    )
    
    pir_id = await pir_service.create_pir(request, user_id="user1")
    
    assert pir_id is not None
    
    # 驗證已建立
    pir = await pir_service.get_pir_by_id(pir_id)
    assert pir is not None
    assert pir.name == "測試 PIR"
    assert pir.priority == "高"
    assert pir.created_by == "user1"


@pytest.mark.asyncio
async def test_update_pir(pir_service):
    """測試更新 PIR"""
    # 建立 PIR
    create_request = CreatePIRRequest(
        name="測試 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
    )
    pir_id = await pir_service.create_pir(create_request)
    
    # 更新 PIR
    update_request = UpdatePIRRequest(
        name="更新後的 PIR",
        description="更新後的描述",
    )
    await pir_service.update_pir(pir_id, update_request, user_id="user2")
    
    # 驗證已更新
    pir = await pir_service.get_pir_by_id(pir_id)
    assert pir.name == "更新後的 PIR"
    assert pir.description == "更新後的描述"
    assert pir.updated_by == "user2"


@pytest.mark.asyncio
async def test_delete_pir(pir_service):
    """測試刪除 PIR"""
    # 建立 PIR
    create_request = CreatePIRRequest(
        name="測試 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
    )
    pir_id = await pir_service.create_pir(create_request)
    
    # 刪除 PIR
    await pir_service.delete_pir(pir_id, user_id="user1")
    
    # 驗證已刪除
    pir = await pir_service.get_pir_by_id(pir_id)
    assert pir is None


@pytest.mark.asyncio
async def test_toggle_pir(pir_service):
    """測試切換 PIR 啟用狀態"""
    # 建立 PIR
    create_request = CreatePIRRequest(
        name="測試 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
        is_enabled=True,
    )
    pir_id = await pir_service.create_pir(create_request)
    
    # 驗證初始狀態
    pir = await pir_service.get_pir_by_id(pir_id)
    assert pir.is_enabled is True
    
    # 切換狀態
    await pir_service.toggle_pir(pir_id, user_id="user1")
    
    # 驗證已切換
    pir = await pir_service.get_pir_by_id(pir_id)
    assert pir.is_enabled is False


@pytest.mark.asyncio
async def test_get_pirs(pir_service):
    """測試查詢 PIR 清單"""
    # 建立多個 PIR
    for i in range(3):
        create_request = CreatePIRRequest(
            name=f"測試 PIR {i}",
            description="測試描述",
            priority="高",
            condition_type="產品名稱",
            condition_value="VMware",
        )
        await pir_service.create_pir(create_request)
    
    # 查詢清單
    response = await pir_service.get_pirs(page=1, page_size=2)
    
    assert response.total_count == 3
    assert len(response.data) == 2
    assert response.page == 1
    assert response.page_size == 2
    assert response.total_pages == 2


@pytest.mark.asyncio
async def test_get_enabled_pirs(pir_service):
    """測試查詢啟用的 PIR"""
    # 建立啟用的 PIR
    create_request1 = CreatePIRRequest(
        name="啟用的 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
        is_enabled=True,
    )
    await pir_service.create_pir(create_request1)
    
    # 建立停用的 PIR
    create_request2 = CreatePIRRequest(
        name="停用的 PIR",
        description="測試描述",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
        is_enabled=False,
    )
    await pir_service.create_pir(create_request2)
    
    # 查詢啟用的 PIR
    enabled_pirs = await pir_service.get_enabled_pirs()
    
    assert len(enabled_pirs) == 1
    assert enabled_pirs[0].name == "啟用的 PIR"
    assert enabled_pirs[0].is_enabled is True


@pytest.mark.asyncio
async def test_find_matching_pirs(pir_service):
    """測試查詢符合威脅資料的 PIR"""
    # 建立多個 PIR
    create_request1 = CreatePIRRequest(
        name="VMware PIR",
        description="VMware 相關威脅",
        priority="高",
        condition_type="產品名稱",
        condition_value="VMware",
        is_enabled=True,
    )
    await pir_service.create_pir(create_request1)
    
    create_request2 = CreatePIRRequest(
        name="CVE-2024 PIR",
        description="2024 年 CVE",
        priority="高",
        condition_type="CVE 編號",
        condition_value="CVE-2024-",
        is_enabled=True,
    )
    await pir_service.create_pir(create_request2)
    
    # 查詢符合的 PIR
    matching_pirs = await pir_service.find_matching_pirs({"product_name": "VMware ESXi"})
    
    assert len(matching_pirs) == 1
    assert matching_pirs[0].name == "VMware PIR"

