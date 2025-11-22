"""
分析與評估模組資料模型

實作分析與評估相關的資料庫模型，符合 plan.md 第 4.2.3 節的設計。
"""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Numeric,
    Integer,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from shared_kernel.infrastructure.database import Base


class PIR(Base):
    """優先情資需求表"""

    __tablename__ = "pirs"

    # 主鍵
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 基本資訊
    name = Column(String(200), nullable=False, comment="PIR 名稱")
    description = Column(Text, nullable=False, comment="PIR 描述")
    priority = Column(String(10), nullable=False, comment="優先級（高/中/低）")

    # 條件設定
    condition_type = Column(String(50), nullable=False, comment="條件類型（產品名稱/CVE/威脅類型等）")
    condition_value = Column(Text, nullable=False, comment="條件值")

    # 狀態
    is_enabled = Column(Boolean, nullable=False, default=True, comment="是否啟用")

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=False, default="system")
    updated_by = Column(String(100), nullable=False, default="system")

    # 索引
    __table_args__ = (
        Index("IX_PIRs_IsEnabled", "is_enabled"),
        Index("IX_PIRs_Priority", "priority"),
    )

    def __repr__(self):
        return f"<PIR(id={self.id}, name={self.name})>"


class ThreatAssetAssociation(Base):
    """威脅資產關聯表"""

    __tablename__ = "threat_asset_associations"

    # 主鍵
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 外鍵
    threat_id = Column(
        CHAR(36),
        ForeignKey("threats.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        comment="威脅 ID",
    )
    asset_id = Column(
        CHAR(36),
        ForeignKey("assets.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        comment="資產 ID",
    )

    # 匹配資訊
    match_confidence = Column(
        Numeric(3, 2), nullable=False, comment="匹配信心分數（0.0-1.0）"
    )
    match_type = Column(
        String(50), nullable=False, comment="匹配類型（Exact/Fuzzy/VersionRange）"
    )
    match_details = Column(Text, nullable=True, comment="匹配詳情（JSON 格式）")

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 關聯（使用字串避免循環匯入）
    threat = relationship("Threat")
    asset = relationship("Asset")

    # 索引與約束
    __table_args__ = (
        Index("IX_ThreatAssetAssociations_ThreatId", "threat_id"),
        Index("IX_ThreatAssetAssociations_AssetId", "asset_id"),
        UniqueConstraint("threat_id", "asset_id", name="UQ_ThreatAssetAssociations_ThreatId_AssetId"),
    )

    def __repr__(self):
        return f"<ThreatAssetAssociation(id={self.id}, threat_id={self.threat_id}, asset_id={self.asset_id})>"


class RiskAssessment(Base):
    """風險評估表"""

    __tablename__ = "risk_assessments"

    # 主鍵
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 外鍵
    threat_id = Column(
        CHAR(36),
        ForeignKey("threats.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        comment="威脅 ID",
    )
    threat_asset_association_id = Column(
        CHAR(36),
        ForeignKey("threat_asset_associations.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        comment="威脅資產關聯 ID",
    )

    # 風險分數計算
    base_cvss_score = Column(Numeric(3, 1), nullable=False, comment="基礎 CVSS 分數")
    asset_importance_weight = Column(
        Numeric(3, 2), nullable=False, comment="資產重要性加權（1.5/1.0/0.5）"
    )
    affected_asset_count = Column(Integer, nullable=False, comment="受影響資產數量")
    pir_match_weight = Column(Numeric(3, 2), nullable=True, comment="PIR 符合度加權")
    cisa_kev_weight = Column(Numeric(3, 2), nullable=True, comment="CISA KEV 加權")

    # 最終結果
    final_risk_score = Column(Numeric(4, 2), nullable=False, comment="最終風險分數（0.0-10.0）")
    risk_level = Column(
        String(20), nullable=False, comment="風險等級（Critical/High/Medium/Low）"
    )

    # 計算詳情
    calculation_details = Column(Text, nullable=True, comment="計算詳情（JSON 格式）")

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯（使用字串避免循環匯入）
    threat = relationship("Threat")
    threat_asset_association = relationship("ThreatAssetAssociation")

    # 索引
    __table_args__ = (
        Index("IX_RiskAssessments_ThreatId", "threat_id"),
        Index("IX_RiskAssessments_RiskLevel", "risk_level"),
        Index("IX_RiskAssessments_FinalRiskScore", "final_risk_score"),
    )

    def __repr__(self):
        return f"<RiskAssessment(id={self.id}, threat_id={self.threat_id}, final_risk_score={self.final_risk_score})>"

