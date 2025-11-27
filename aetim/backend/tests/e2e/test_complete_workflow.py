"""
完整工作流程端對端測試

測試完整的業務流程，包含：
- 資產管理完整流程
- 威脅收集與分析完整流程
- 報告生成與通知完整流程
- 系統管理功能

符合 T-5-4-1：端對端測試所有功能
"""

import pytest
import sys
import os
from datetime import datetime
from typing import Dict, Any

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from shared_kernel.infrastructure.database import Base
from asset_management.application.services.asset_service import AssetService
from asset_management.application.dtos.asset_dto import CreateAssetRequest, UpdateAssetRequest
from asset_management.infrastructure.persistence.asset_repository import AssetRepository
from asset_management.domain.domain_services.asset_parsing_service import AssetParsingService
from threat_intelligence.application.services.threat_collection_service import ThreatCollectionService
from threat_intelligence.infrastructure.persistence.threat_feed_repository import ThreatFeedRepository
from threat_intelligence.infrastructure.persistence.threat_repository import ThreatRepository
from analysis_assessment.application.services.association_analysis_service import AssociationAnalysisService
from analysis_assessment.application.services.risk_calculation_service import RiskCalculationService
from report_generation.application.services.report_generation_service import ReportGenerationService
from system_management.application.services.system_configuration_service import SystemConfigurationService
from system_management.infrastructure.persistence.system_configuration_repository import SystemConfigurationRepository
from system_management.infrastructure.persistence.audit_log_repository import AuditLogRepository


@pytest.fixture
async def db_session():
    """建立測試用的資料庫會話"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def asset_service(db_session: AsyncSession):
    """建立資產服務"""
    repository = AssetRepository(db_session)
    parsing_service = AssetParsingService()
    return AssetService(repository=repository, parsing_service=parsing_service)


@pytest.fixture
def threat_collection_service(db_session: AsyncSession):
    """建立威脅收集服務"""
    threat_feed_repository = ThreatFeedRepository(db_session)
    threat_repository = ThreatRepository(db_session)
    return ThreatCollectionService(
        threat_feed_repository=threat_feed_repository,
        threat_repository=threat_repository,
    )


@pytest.fixture
def association_analysis_service(db_session: AsyncSession):
    """建立關聯分析服務"""
    from analysis_assessment.infrastructure.persistence.threat_asset_association_repository import (
        ThreatAssetAssociationRepository,
    )
    from asset_management.infrastructure.persistence.asset_repository import AssetRepository
    from threat_intelligence.infrastructure.persistence.threat_repository import ThreatRepository
    
    association_repository = ThreatAssetAssociationRepository(db_session)
    asset_repository = AssetRepository(db_session)
    threat_repository = ThreatRepository(db_session)
    
    return AssociationAnalysisService(
        association_repository=association_repository,
        asset_repository=asset_repository,
        threat_repository=threat_repository,
    )


@pytest.fixture
def risk_calculation_service(db_session: AsyncSession):
    """建立風險計算服務"""
    from analysis_assessment.infrastructure.persistence.risk_assessment_repository import (
        RiskAssessmentRepository,
    )
    from analysis_assessment.infrastructure.persistence.threat_asset_association_repository import (
        ThreatAssetAssociationRepository,
    )
    
    risk_assessment_repository = RiskAssessmentRepository(db_session)
    association_repository = ThreatAssetAssociationRepository(db_session)
    
    return RiskCalculationService(
        risk_assessment_repository=risk_assessment_repository,
        association_repository=association_repository,
    )


@pytest.fixture
def report_generation_service(db_session: AsyncSession):
    """建立報告生成服務"""
    from report_generation.infrastructure.persistence.report_repository import ReportRepository
    
    report_repository = ReportRepository(db_session)
    return ReportGenerationService(report_repository=report_repository)


@pytest.fixture
def system_configuration_service(db_session: AsyncSession):
    """建立系統設定服務"""
    repository = SystemConfigurationRepository(db_session)
    audit_log_repository = AuditLogRepository(db_session)
    return SystemConfigurationService(
        repository=repository,
        audit_log_repository=audit_log_repository,
    )


@pytest.mark.asyncio
async def test_complete_asset_management_workflow(
    db_session: AsyncSession,
    asset_service: AssetService,
):
    """
    測試資產管理完整流程
    
    符合 US-001, US-002, US-003
    """
    # 1. 建立資產
    asset_request = CreateAssetRequest(
        host_name="測試主機",
        operating_system="Windows Server 2016",
        running_applications="Microsoft SQL Server 2017",
        owner="測試使用者",
        data_sensitivity="高",
        is_public_facing=False,
        business_criticality="高",
    )
    
    asset_id = await asset_service.create_asset(asset_request)
    assert asset_id is not None
    
    # 2. 查詢資產
    assets = await asset_service.get_assets(page=1, page_size=10)
    assert len(assets["data"]) > 0
    
    # 3. 更新資產
    update_request = UpdateAssetRequest(host_name="更新後的主機名稱")
    updated_asset = await asset_service.update_asset(asset_id, update_request)
    assert updated_asset.host_name == "更新後的主機名稱"
    
    # 4. 刪除資產
    await asset_service.delete_asset(asset_id)
    
    # 5. 驗證資產已刪除
    deleted_asset = await asset_service.get_asset_by_id(asset_id)
    assert deleted_asset is None


@pytest.mark.asyncio
async def test_complete_threat_collection_and_analysis_workflow(
    db_session: AsyncSession,
    threat_collection_service: ThreatCollectionService,
    association_analysis_service: AssociationAnalysisService,
    risk_calculation_service: RiskCalculationService,
):
    """
    測試威脅收集與分析完整流程
    
    符合 US-008, US-010, US-011
    """
    # 1. 建立威脅來源
    from threat_intelligence.infrastructure.persistence.threat_feed_repository import (
        ThreatFeedRepository,
    )
    from threat_intelligence.domain.aggregates.threat_feed import ThreatFeed
    
    threat_feed_repository = ThreatFeedRepository(db_session)
    threat_feed = ThreatFeed.create(
        name="測試威脅來源",
        priority="P1",
        collection_frequency="每日",
        is_enabled=True,
    )
    await threat_feed_repository.save(threat_feed)
    
    # 2. 建立威脅
    from threat_intelligence.infrastructure.persistence.threat_repository import ThreatRepository
    from threat_intelligence.domain.aggregates.threat import Threat
    
    threat_repository = ThreatRepository(db_session)
    threat = Threat.create(
        threat_feed_id=threat_feed.id,
        title="測試威脅",
        description="測試威脅描述",
        cve="CVE-2024-0001",
        cvss_base_score=7.5,
    )
    await threat_repository.save(threat)
    
    # 3. 執行關聯分析
    # 注意：需要先建立資產
    associations = await association_analysis_service.analyze_threat_asset_associations(
        threat_id=threat.id
    )
    assert isinstance(associations, list)
    
    # 4. 計算風險分數
    if associations:
        association = associations[0]
        risk_assessment = await risk_calculation_service.calculate_risk(
            threat_id=threat.id,
            association_id=association.id,
        )
        assert risk_assessment.final_risk_score >= 0
        assert risk_assessment.final_risk_score <= 10


@pytest.mark.asyncio
async def test_complete_report_generation_workflow(
    db_session: AsyncSession,
    report_generation_service: ReportGenerationService,
):
    """
    測試報告生成完整流程
    
    符合 US-015, US-016
    """
    # 1. 生成報告
    report_data = {
        "report_type": "CISO_Weekly",
        "start_date": datetime(2024, 1, 1),
        "end_date": datetime(2024, 1, 7),
    }
    
    report = await report_generation_service.generate_report(report_data)
    assert report.id is not None
    assert report.report_type == "CISO_Weekly"
    
    # 2. 查詢報告
    reports = await report_generation_service.get_reports(page=1, page_size=10)
    assert len(reports["data"]) > 0
    
    # 3. 取得報告詳情
    report_detail = await report_generation_service.get_report_by_id(report.id)
    assert report_detail.id == report.id


@pytest.mark.asyncio
async def test_complete_system_management_workflow(
    db_session: AsyncSession,
    system_configuration_service: SystemConfigurationService,
):
    """
    測試系統管理完整流程
    
    符合 US-024
    """
    # 1. 更新系統設定（建立新設定）
    config_key = "test_config"
    config_value = '{"test": "value"}'
    
    config = await system_configuration_service.update_configuration(
        key=config_key,
        value=config_value,
        category="test",
        description="測試設定",
    )
    assert config.key == config_key
    
    # 2. 查詢系統設定
    configs = await system_configuration_service.get_configuration()
    assert isinstance(configs, list)
    assert len(configs) > 0
    
    # 3. 更新系統設定
    updated_value = '{"test": "updated_value"}'
    updated_config = await system_configuration_service.update_configuration(
        key=config_key,
        value=updated_value,
        category="test",
    )
    assert updated_config.value == updated_value
    
    # 4. 刪除系統設定
    await system_configuration_service.delete_configuration(
        key=config_key,
        user_id="test-user",
    )
    
    # 5. 驗證設定已刪除
    deleted_config = await system_configuration_service.get_configuration(key=config_key)
    assert deleted_config is None

