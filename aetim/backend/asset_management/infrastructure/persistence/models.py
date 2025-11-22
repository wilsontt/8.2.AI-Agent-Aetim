"""
資產管理模組資料模型

實作資產管理相關的資料庫模型，符合 plan.md 第 4.2.1 節的設計。
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from shared_kernel.infrastructure.database import Base


class Asset(Base):
    """資產主表"""

    __tablename__ = "assets"

    # 主鍵
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 基本資訊
    item = Column(Integer, nullable=True, comment="資產項目編號")
    ip = Column(String(500), nullable=True, comment="IP 位址或 IP 範圍")
    host_name = Column(String(200), nullable=False, comment="主機名稱")
    operating_system = Column(String(500), nullable=False, comment="作業系統（含版本）")
    running_applications = Column(Text, nullable=False, comment="運行的應用程式（含版本）")
    owner = Column(String(200), nullable=False, comment="負責人")

    # 風險評估相關
    data_sensitivity = Column(
        String(10), nullable=False, comment="資料敏感度（高/中/低）"
    )
    is_public_facing = Column(Boolean, nullable=False, default=False, comment="是否對外暴露")
    business_criticality = Column(
        String(10), nullable=False, comment="業務關鍵性（高/中/低）"
    )

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=False, default="system")
    updated_by = Column(String(100), nullable=False, default="system")

    # 關聯
    products = relationship("AssetProduct", back_populates="asset", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index("IX_Assets_HostName", "host_name"),
        Index("IX_Assets_IsPublicFacing", "is_public_facing"),
        Index("IX_Assets_DataSensitivity", "data_sensitivity"),
        Index("IX_Assets_BusinessCriticality", "business_criticality"),
    )

    def __repr__(self):
        return f"<Asset(id={self.id}, host_name={self.host_name})>"


class AssetProduct(Base):
    """資產產品資訊表"""

    __tablename__ = "asset_products"

    # 主鍵
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 外鍵
    asset_id = Column(
        CHAR(36),
        ForeignKey("assets.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        comment="資產 ID",
    )

    # 產品資訊
    product_name = Column(String(200), nullable=False, comment="產品名稱（解析後）")
    product_version = Column(String(100), nullable=True, comment="產品版本（解析後）")
    product_type = Column(String(50), nullable=True, comment="產品類型（OS/Application）")
    original_text = Column(Text, nullable=True, comment="原始文字（用於比對）")

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯
    asset = relationship("Asset", back_populates="products")

    # 索引
    __table_args__ = (
        Index("IX_AssetProducts_AssetId", "asset_id"),
        Index("IX_AssetProducts_ProductName", "product_name"),
    )

    def __repr__(self):
        return f"<AssetProduct(id={self.id}, product_name={self.product_name})>"

