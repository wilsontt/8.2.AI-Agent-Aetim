"""
威脅情資模組資料模型

實作威脅情資相關的資料庫模型，符合 plan.md 第 4.2.2 節的設計。
"""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Numeric,
    Index,
)
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from shared_kernel.infrastructure.database import Base


class ThreatFeed(Base):
    """威脅情資來源表"""

    __tablename__ = "threat_feeds"

    # 主鍵
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 基本資訊
    name = Column(String(100), nullable=False, unique=True, comment="來源名稱（CISA KEV、NVD 等）")
    description = Column(Text, nullable=True, comment="來源描述")
    priority = Column(String(10), nullable=False, comment="優先級（P0/P1/P2/P3）")
    is_enabled = Column(Boolean, nullable=False, default=True, comment="是否啟用")

    # 收集設定
    collection_frequency = Column(String(50), nullable=False, comment="收集頻率（每小時/每日/每週）")
    collection_strategy = Column(Text, nullable=True, comment="收集策略說明")
    api_key = Column(String(500), nullable=True, comment="API 金鑰（加密儲存）")

    # 收集狀態
    last_collection_time = Column(DateTime, nullable=True, comment="最後收集時間")
    last_collection_status = Column(String(20), nullable=True, comment="最後收集狀態（Success/Failed）")
    last_collection_error = Column(Text, nullable=True, comment="最後收集錯誤訊息")

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=False, default="system")
    updated_by = Column(String(100), nullable=False, default="system")

    # 關聯
    threats = relationship("Threat", back_populates="threat_feed", cascade="all, delete-orphan")

    # 索引
    __table_args__ = (
        Index("IX_ThreatFeeds_Name", "name"),
        Index("IX_ThreatFeeds_IsEnabled", "is_enabled"),
        Index("IX_ThreatFeeds_Priority", "priority"),
    )

    def __repr__(self):
        return f"<ThreatFeed(id={self.id}, name={self.name})>"


class Threat(Base):
    """威脅主表"""

    __tablename__ = "threats"

    # 主鍵
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # CVE 資訊
    cve = Column(String(50), nullable=True, unique=True, comment="CVE 編號")

    # 外鍵
    threat_feed_id = Column(
        CHAR(36),
        ForeignKey("threat_feeds.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        comment="威脅情資來源 ID",
    )

    # 基本資訊
    title = Column(String(500), nullable=False, comment="威脅標題")
    description = Column(Text, nullable=True, comment="威脅描述")

    # CVSS 資訊
    cvss_base_score = Column(Numeric(3, 1), nullable=True, comment="CVSS 基礎分數")
    cvss_vector = Column(String(200), nullable=True, comment="CVSS 向量字串")
    severity = Column(String(20), nullable=True, comment="嚴重程度（Critical/High/Medium/Low）")

    # 時間資訊
    published_date = Column(DateTime, nullable=True, comment="發布日期")

    # 威脅詳情（JSON 格式）
    affected_products = Column(Text, nullable=True, comment="受影響產品（JSON 格式）")
    threat_type = Column(String(100), nullable=True, comment="威脅類型（RCE/權限提升等）")
    ttps = Column(Text, nullable=True, comment="TTPs（JSON 格式）")
    iocs = Column(Text, nullable=True, comment="IOCs（JSON 格式）")

    # 來源資訊
    source_url = Column(String(500), nullable=True, comment="來源 URL")
    raw_data = Column(Text, nullable=True, comment="原始資料（JSON 格式）")

    # 狀態
    status = Column(
        String(20),
        nullable=False,
        default="New",
        comment="狀態（New/Analyzing/Processed/Closed）",
    )

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯（使用字串避免循環匯入）
    threat_feed = relationship("ThreatFeed", back_populates="threats")
    # associations 和 risk_assessments 將在其他模組中定義反向關係

    # 索引
    __table_args__ = (
        Index("IX_Threats_CVE", "cve"),
        Index("IX_Threats_ThreatFeedId", "threat_feed_id"),
        Index("IX_Threats_Status", "status"),
        Index("IX_Threats_CVSS_BaseScore", "cvss_base_score"),
        Index("IX_Threats_PublishedDate", "published_date"),
    )

    def __repr__(self):
        return f"<Threat(id={self.id}, cve={self.cve}, title={self.title})>"

