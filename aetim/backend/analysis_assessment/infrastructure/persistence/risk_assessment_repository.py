"""
風險評估 Repository 實作

實作風險評估的資料存取邏輯。
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import json

from ...domain.interfaces.risk_assessment_repository import IRiskAssessmentRepository
from ...domain.aggregates.risk_assessment import RiskAssessment
from .models import RiskAssessment as RiskAssessmentModel
import structlog

logger = structlog.get_logger(__name__)


class RiskAssessmentRepository(IRiskAssessmentRepository):
    """
    風險評估 Repository 實作
    
    負責風險評估的資料存取。
    """

    def __init__(self, session: AsyncSession):
        """
        初始化 Repository
        
        Args:
            session: 資料庫會話
        """
        self.session = session

    async def save(self, risk_assessment: RiskAssessment) -> None:
        """
        儲存風險評估（新增或更新）
        
        Args:
            risk_assessment: 風險評估聚合根
        """
        try:
            # 檢查風險評估是否存在
            stmt = select(RiskAssessmentModel).where(
                RiskAssessmentModel.id == risk_assessment.id
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # 更新現有風險評估
                existing.base_cvss_score = float(risk_assessment.base_cvss_score)
                existing.asset_importance_weight = float(
                    risk_assessment.asset_importance_weight
                )
                existing.affected_asset_count = risk_assessment.affected_asset_count
                # 注意：RiskAssessment 模型沒有 asset_count_weight 欄位
                # 這個值會儲存在 calculation_details 中
                existing.pir_match_weight = (
                    float(risk_assessment.pir_match_weight)
                    if risk_assessment.pir_match_weight is not None
                    else None
                )
                existing.cisa_kev_weight = (
                    float(risk_assessment.cisa_kev_weight)
                    if risk_assessment.cisa_kev_weight is not None
                    else None
                )
                existing.final_risk_score = float(risk_assessment.final_risk_score)
                existing.risk_level = risk_assessment.risk_level
                existing.calculation_details = risk_assessment.get_calculation_details_json()
            else:
                # 新增風險評估
                new_assessment = RiskAssessmentModel(
                    id=risk_assessment.id,
                    threat_id=risk_assessment.threat_id,
                    threat_asset_association_id=risk_assessment.threat_asset_association_id,
                    base_cvss_score=float(risk_assessment.base_cvss_score),
                    asset_importance_weight=float(risk_assessment.asset_importance_weight),
                    affected_asset_count=risk_assessment.affected_asset_count,
                    # 注意：RiskAssessment 模型沒有 asset_count_weight 欄位
                    # 這個值會儲存在 calculation_details 中
                    pir_match_weight=(
                        float(risk_assessment.pir_match_weight)
                        if risk_assessment.pir_match_weight is not None
                        else None
                    ),
                    cisa_kev_weight=(
                        float(risk_assessment.cisa_kev_weight)
                        if risk_assessment.cisa_kev_weight is not None
                        else None
                    ),
                    final_risk_score=float(risk_assessment.final_risk_score),
                    risk_level=risk_assessment.risk_level,
                    calculation_details=risk_assessment.get_calculation_details_json(),
                )
                self.session.add(new_assessment)

            await self.session.flush()

            logger.info(
                "風險評估已儲存",
                risk_assessment_id=risk_assessment.id,
                threat_id=risk_assessment.threat_id,
            )
        except Exception as e:
            logger.error(
                "儲存風險評估失敗",
                risk_assessment_id=risk_assessment.id,
                error=str(e),
            )
            raise

    async def get_by_id(
        self, risk_assessment_id: str
    ) -> Optional[RiskAssessment]:
        """
        依 ID 查詢風險評估
        
        Args:
            risk_assessment_id: 風險評估 ID
        
        Returns:
            Optional[RiskAssessment]: 風險評估聚合根，如果不存在則返回 None
        """
        try:
            stmt = select(RiskAssessmentModel).where(
                RiskAssessmentModel.id == risk_assessment_id
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return self._to_domain(model)
        except Exception as e:
            logger.error(
                "查詢風險評估失敗",
                risk_assessment_id=risk_assessment_id,
                error=str(e),
            )
            raise

    async def get_by_threat_id(self, threat_id: str) -> Optional[RiskAssessment]:
        """
        依威脅 ID 查詢風險評估
        
        Args:
            threat_id: 威脅 ID
        
        Returns:
            Optional[RiskAssessment]: 風險評估聚合根，如果不存在則返回 None
        """
        try:
            stmt = select(RiskAssessmentModel).where(
                RiskAssessmentModel.threat_id == threat_id
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model is None:
                return None

            return self._to_domain(model)
        except Exception as e:
            logger.error(
                "查詢風險評估失敗",
                threat_id=threat_id,
                error=str(e),
            )
            raise
    
    async def get_by_risk_score_range(
        self,
        min_risk_score: float,
        max_risk_score: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[RiskAssessment]:
        """
        依風險分數範圍查詢風險評估
        
        Args:
            min_risk_score: 最小風險分數
            max_risk_score: 最大風險分數（可選，如果不提供則不設上限）
            start_date: 開始日期（可選）
            end_date: 結束日期（可選）
        
        Returns:
            List[RiskAssessment]: 風險評估聚合根清單
        """
        try:
            stmt = select(RiskAssessmentModel).where(
                RiskAssessmentModel.final_risk_score >= min_risk_score
            )
            
            if max_risk_score is not None:
                stmt = stmt.where(RiskAssessmentModel.final_risk_score <= max_risk_score)
            
            if start_date is not None:
                stmt = stmt.where(RiskAssessmentModel.updated_at >= start_date)
            
            if end_date is not None:
                stmt = stmt.where(RiskAssessmentModel.updated_at <= end_date)
            
            # 依更新時間降序排序（最新的在前）
            stmt = stmt.order_by(RiskAssessmentModel.updated_at.desc())
            
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._to_domain(model) for model in models]
            
        except Exception as e:
            logger.error(
                "依風險分數範圍查詢風險評估失敗",
                min_risk_score=min_risk_score,
                max_risk_score=max_risk_score,
                start_date=start_date,
                end_date=end_date,
                error=str(e),
                exc_info=True,
            )
            raise

    def _to_domain(self, model: RiskAssessmentModel) -> RiskAssessment:
        """
        將資料模型轉換為領域模型
        
        Args:
            model: 資料模型
        
        Returns:
            RiskAssessment: 領域模型
        """
        calculation_details = None
        if model.calculation_details:
            try:
                calculation_details = json.loads(model.calculation_details)
            except json.JSONDecodeError:
                logger.warning(
                    "無法解析計算詳情 JSON",
                    risk_assessment_id=model.id,
                )

        # 從 calculation_details 中取得 asset_count_weight
        asset_count_weight = 0.0
        if calculation_details and "asset_count_weight" in calculation_details:
            asset_count_weight = calculation_details["asset_count_weight"]
        
        # 使用 create 方法建立領域模型，然後設定 id
        risk_assessment = RiskAssessment.create(
            threat_id=model.threat_id,
            threat_asset_association_id=model.threat_asset_association_id,
            base_cvss_score=float(model.base_cvss_score),
            asset_importance_weight=float(model.asset_importance_weight),
            affected_asset_count=model.affected_asset_count,
            asset_count_weight=asset_count_weight,
            final_risk_score=float(model.final_risk_score),
            risk_level=model.risk_level,
            pir_match_weight=(
                float(model.pir_match_weight) if model.pir_match_weight is not None else None
            ),
            cisa_kev_weight=(
                float(model.cisa_kev_weight) if model.cisa_kev_weight is not None else None
            ),
            calculation_details=calculation_details,
        )
        
        # 設定 id 和時間戳記
        risk_assessment.id = model.id
        risk_assessment.created_at = model.created_at
        risk_assessment.updated_at = model.updated_at
        
        return risk_assessment

