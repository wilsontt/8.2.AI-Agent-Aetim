"""
資料模型單元測試

驗證資料模型的基本功能。
"""

import pytest
from datetime import datetime
import uuid
from asset_management.infrastructure.persistence.models import Asset, AssetProduct
from threat_intelligence.infrastructure.persistence.models import ThreatFeed, Threat
from analysis_assessment.infrastructure.persistence.models import PIR
from system_management.infrastructure.persistence.models import User, Role


@pytest.mark.unit
def test_asset_model():
    """測試 Asset 模型"""
    asset = Asset(
        host_name="test-host",
        operating_system="Linux 5.4",
        running_applications="nginx 1.18",
        owner="test-owner",
        data_sensitivity="高",
        is_public_facing=False,
        business_criticality="中",
    )

    assert asset.id is not None
    assert asset.host_name == "test-host"
    assert asset.data_sensitivity == "高"
    assert asset.is_public_facing is False
    assert asset.created_at is not None


@pytest.mark.unit
def test_asset_product_model():
    """測試 AssetProduct 模型"""
    asset_id = str(uuid.uuid4())
    product = AssetProduct(
        asset_id=asset_id,
        product_name="nginx",
        product_version="1.18.0",
        product_type="Application",
    )

    assert product.id is not None
    assert product.asset_id == asset_id
    assert product.product_name == "nginx"
    assert product.product_version == "1.18.0"


@pytest.mark.unit
def test_threat_feed_model():
    """測試 ThreatFeed 模型"""
    feed = ThreatFeed(
        name="CISA KEV",
        priority="P0",
        is_enabled=True,
        collection_frequency="每小時",
    )

    assert feed.id is not None
    assert feed.name == "CISA KEV"
    assert feed.priority == "P0"
    assert feed.is_enabled is True


@pytest.mark.unit
def test_threat_model():
    """測試 Threat 模型"""
    feed_id = str(uuid.uuid4())
    threat = Threat(
        threat_feed_id=feed_id,
        title="Test Threat",
        description="Test Description",
        cve="CVE-2024-0001",
        status="New",
    )

    assert threat.id is not None
    assert threat.threat_feed_id == feed_id
    assert threat.title == "Test Threat"
    assert threat.cve == "CVE-2024-0001"
    assert threat.status == "New"


@pytest.mark.unit
def test_pir_model():
    """測試 PIR 模型"""
    pir = PIR(
        name="PIR-01",
        description="Test PIR",
        priority="高",
        condition_type="產品名稱",
        condition_value="nginx",
        is_enabled=True,
    )

    assert pir.id is not None
    assert pir.name == "PIR-01"
    assert pir.priority == "高"
    assert pir.is_enabled is True


@pytest.mark.unit
def test_user_model():
    """測試 User 模型"""
    user = User(
        subject_id="sub-123",
        email="test@example.com",
        display_name="Test User",
        is_active=True,
    )

    assert user.id is not None
    assert user.subject_id == "sub-123"
    assert user.email == "test@example.com"
    assert user.is_active is True


@pytest.mark.unit
def test_role_model():
    """測試 Role 模型"""
    role = Role(
        name="CISO",
        description="Chief Information Security Officer",
    )

    assert role.id is not None
    assert role.name == "CISO"
    assert role.description == "Chief Information Security Officer"

