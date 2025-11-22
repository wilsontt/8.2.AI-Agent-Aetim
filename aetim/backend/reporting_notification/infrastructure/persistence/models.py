"""
報告與通知模組資料模型

實作報告與通知相關的資料庫模型，符合 plan.md 第 4.2.4 節的設計。
"""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Numeric,
    Time,
    Index,
)
from sqlalchemy.dialects.sqlite import CHAR
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from shared_kernel.infrastructure.database import Base


class Report(Base):
    """報告主表"""

    __tablename__ = "reports"

    # 主鍵
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 報告資訊
    report_type = Column(String(50), nullable=False, comment="報告類型（CISO_Weekly/IT_Ticket）")
    title = Column(String(500), nullable=False, comment="報告標題")
    file_path = Column(String(1000), nullable=False, comment="檔案路徑")
    file_format = Column(String(20), nullable=False, comment="檔案格式（HTML/PDF/JSON/TEXT）")

    # 時間資訊
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="生成時間")
    period_start = Column(DateTime, nullable=True, comment="報告期間開始")
    period_end = Column(DateTime, nullable=True, comment="報告期間結束")

    # 內容
    summary = Column(Text, nullable=True, comment="AI 生成的摘要")
    metadata = Column(Text, nullable=True, comment="報告元資料（JSON 格式）")

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 關聯
    notifications = relationship("Notification", back_populates="report")

    # 索引
    __table_args__ = (
        Index("IX_Reports_ReportType", "report_type"),
        Index("IX_Reports_GeneratedAt", "generated_at"),
    )

    def __repr__(self):
        return f"<Report(id={self.id}, report_type={self.report_type}, title={self.title})>"


class NotificationRule(Base):
    """通知規則表"""

    __tablename__ = "notification_rules"

    # 主鍵
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 通知設定
    notification_type = Column(
        String(50), nullable=False, comment="通知類型（Critical/HighRiskDaily/Weekly）"
    )
    is_enabled = Column(Boolean, nullable=False, default=True, comment="是否啟用")
    risk_score_threshold = Column(
        Numeric(4, 2), nullable=True, comment="風險分數閾值"
    )
    send_time = Column(Time, nullable=True, comment="發送時間")
    recipients = Column(Text, nullable=False, comment="收件人清單（JSON 格式）")

    # 時間戳記
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=False, default="system")
    updated_by = Column(String(100), nullable=False, default="system")

    # 關聯
    notifications = relationship("Notification", back_populates="notification_rule")

    # 索引
    __table_args__ = (
        Index("IX_NotificationRules_NotificationType", "notification_type"),
        Index("IX_NotificationRules_IsEnabled", "is_enabled"),
    )

    def __repr__(self):
        return f"<NotificationRule(id={self.id}, notification_type={self.notification_type})>"


class Notification(Base):
    """通知記錄表"""

    __tablename__ = "notifications"

    # 主鍵
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 外鍵
    notification_rule_id = Column(
        CHAR(36),
        ForeignKey("notification_rules.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        comment="通知規則 ID",
    )
    related_threat_id = Column(
        CHAR(36),
        ForeignKey("threats.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        comment="相關威脅 ID",
    )
    related_report_id = Column(
        CHAR(36),
        ForeignKey("reports.id", ondelete="SET NULL", onupdate="CASCADE"),
        nullable=True,
        comment="相關報告 ID",
    )

    # 通知資訊
    notification_type = Column(String(50), nullable=False, comment="通知類型")
    recipients = Column(Text, nullable=False, comment="收件人清單（JSON 格式）")
    subject = Column(String(500), nullable=False, comment="主旨")
    body = Column(Text, nullable=False, comment="內容")

    # 發送狀態
    sent_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="發送時間")
    status = Column(String(20), nullable=False, default="Sent", comment="狀態（Sent/Failed）")
    error_message = Column(Text, nullable=True, comment="錯誤訊息")

    # 關聯（使用字串避免循環匯入）
    notification_rule = relationship("NotificationRule")
    threat = relationship("Threat")
    report = relationship("Report")

    # 索引
    __table_args__ = (
        Index("IX_Notifications_SentAt", "sent_at"),
        Index("IX_Notifications_Status", "status"),
        Index("IX_Notifications_RelatedThreatId", "related_threat_id"),
    )

    def __repr__(self):
        return f"<Notification(id={self.id}, notification_type={self.notification_type}, status={self.status})>"

