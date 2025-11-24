"""
風險評估歷史記錄 Repository 實作

實作風險評估歷史記錄的資料存取邏輯。
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ...domain.interfaces.risk_assessment_history_repository import (
    IRiskAssessmentHistoryRepository,
)
from ...domain.aggregates.risk_assessment import RiskAssessment
from .models import RiskAssessmentHistory
import structlog

logger = structlog.get_logger(__name__)


class RiskAssessmentHistoryRepository(IRiskAssessmentHistoryRepository):
    """
    風險評估歷史記錄 Repository 實作
    
    負責風險評估歷史記錄的資料存取。
    """

    def __init__(self, session: AsyncSession):
        """
        初始化 Repository
        
        Args:
            session: 資料庫會話
        """
        self.session = session

    async def save_history(
        self,
        risk_assessment: RiskAssessment,
    ) -> None:
        """
        儲存風險評估歷史記錄（AC-012-5）
        
        Args:
            risk_assessment: 風險評估聚合根
        """
        try:
            history = RiskAssessmentHistory(
                risk_assessment_id=risk_assessment.id,
                base_cvss_score=float(risk_assessment.base_cvss_score),
                asset_importance_weight=float(risk_assessment.asset_importance_weight),
                asset_count_weight=float(risk_assessment.asset_count_weight),
                pir_match_weight=float(risk_assessment.pir_match_weight)
                if risk_assessment.pir_match_weight is not None
                else None,
                cisa_kev_weight=float(risk_assessment.cisa_kev_weight)
                if risk_assessment.cisa_kev_weight is not None
                else None,
                final_risk_score=float(risk_assessment.final_risk_score),
                risk_level=risk_assessment.risk_level,
                calculation_details=risk_assessment.get_calculation_details_json(),
                calculated_at=datetime.utcnow(),
            )

            self.session.add(history)
            await self.session.flush()

            logger.info(
                "風險評估歷史記錄已儲存",
                risk_assessment_id=risk_assessment.id,
                final_risk_score=risk_assessment.final_risk_score,
            )
        except Exception as e:
            logger.error(
                "儲存風險評估歷史記錄失敗",
                risk_assessment_id=risk_assessment.id,
                error=str(e),
            )
            raise

    async def get_by_risk_assessment_id(
        self,
        risk_assessment_id: str,
    ) -> List[dict]:
        """
        查詢風險評估的歷史記錄（AC-013-3）
        
        Args:
            risk_assessment_id: 風險評估 ID
        
        Returns:
            List[dict]: 歷史記錄清單
        """
        try:
            stmt = (
                select(RiskAssessmentHistory)
                .where(RiskAssessmentHistory.risk_assessment_id == risk_assessment_id)
                .order_by(desc(RiskAssessmentHistory.calculated_at))
            )

            result = await self.session.execute(stmt)
            histories = result.scalars().all()

            return [
                {
                    "id": h.id,
                    "risk_assessment_id": h.risk_assessment_id,
                    "base_cvss_score": float(h.base_cvss_score),
                    "asset_importance_weight": float(h.asset_importance_weight),
                    "asset_count_weight": float(h.asset_count_weight),
                    "pir_match_weight": float(h.pir_match_weight)
                    if h.pir_match_weight is not None
                    else None,
                    "cisa_kev_weight": float(h.cisa_kev_weight)
                    if h.cisa_kev_weight is not None
                    else None,
                    "final_risk_score": float(h.final_risk_score),
                    "risk_level": h.risk_level,
                    "calculation_details": h.calculation_details,
                    "calculated_at": h.calculated_at.isoformat() if h.calculated_at else None,
                }
                for h in histories
            ]
        except Exception as e:
            logger.error(
                "查詢風險評估歷史記錄失敗",
                risk_assessment_id=risk_assessment_id,
                error=str(e),
            )
            raise

    async def get_latest(
        self,
        risk_assessment_id: str,
    ) -> Optional[dict]:
        """
        查詢最新的風險評估記錄
        
        Args:
            risk_assessment_id: 風險評估 ID
        
        Returns:
            Optional[dict]: 最新的歷史記錄，如果沒有則返回 None
        """
        try:
            stmt = (
                select(RiskAssessmentHistory)
                .where(RiskAssessmentHistory.risk_assessment_id == risk_assessment_id)
                .order_by(desc(RiskAssessmentHistory.calculated_at))
                .limit(1)
            )

            result = await self.session.execute(stmt)
            history = result.scalar_one_or_none()

            if history is None:
                return None

            return {
                "id": history.id,
                "risk_assessment_id": history.risk_assessment_id,
                "base_cvss_score": float(history.base_cvss_score),
                "asset_importance_weight": float(history.asset_importance_weight),
                "asset_count_weight": float(history.asset_count_weight),
                "pir_match_weight": float(history.pir_match_weight)
                if history.pir_match_weight is not None
                else None,
                "cisa_kev_weight": float(history.cisa_kev_weight)
                if history.cisa_kev_weight is not None
                else None,
                "final_risk_score": float(history.final_risk_score),
                "risk_level": history.risk_level,
                "calculation_details": history.calculation_details,
                "calculated_at": history.calculated_at.isoformat()
                if history.calculated_at
                else None,
            }
        except Exception as e:
            logger.error(
                "查詢最新風險評估記錄失敗",
                risk_assessment_id=risk_assessment_id,
                error=str(e),
            )
            raise

    async def get_by_time_range(
        self,
        risk_assessment_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[dict]:
        """
        根據時間範圍查詢歷史記錄
        
        Args:
            risk_assessment_id: 風險評估 ID
            start_time: 開始時間（可選）
            end_time: 結束時間（可選）
        
        Returns:
            List[dict]: 歷史記錄清單
        """
        try:
            stmt = select(RiskAssessmentHistory).where(
                RiskAssessmentHistory.risk_assessment_id == risk_assessment_id
            )

            if start_time:
                stmt = stmt.where(RiskAssessmentHistory.calculated_at >= start_time)

            if end_time:
                stmt = stmt.where(RiskAssessmentHistory.calculated_at <= end_time)

            stmt = stmt.order_by(desc(RiskAssessmentHistory.calculated_at))

            result = await self.session.execute(stmt)
            histories = result.scalars().all()

            return [
                {
                    "id": h.id,
                    "risk_assessment_id": h.risk_assessment_id,
                    "base_cvss_score": float(h.base_cvss_score),
                    "asset_importance_weight": float(h.asset_importance_weight),
                    "asset_count_weight": float(h.asset_count_weight),
                    "pir_match_weight": float(h.pir_match_weight)
                    if h.pir_match_weight is not None
                    else None,
                    "cisa_kev_weight": float(h.cisa_kev_weight)
                    if h.cisa_kev_weight is not None
                    else None,
                    "final_risk_score": float(h.final_risk_score),
                    "risk_level": h.risk_level,
                    "calculation_details": h.calculation_details,
                    "calculated_at": h.calculated_at.isoformat() if h.calculated_at else None,
                }
                for h in histories
            ]
        except Exception as e:
            logger.error(
                "根據時間範圍查詢歷史記錄失敗",
                risk_assessment_id=risk_assessment_id,
                start_time=start_time,
                end_time=end_time,
                error=str(e),
            )
            raise

