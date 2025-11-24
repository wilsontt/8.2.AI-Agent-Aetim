"""
風險評估歷史記錄 Repository 單元測試

測試風險評估歷史記錄的資料存取邏輯。
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from analysis_assessment.domain.aggregates.risk_assessment import RiskAssessment
from analysis_assessment.infrastructure.persistence.risk_assessment_history_repository import (
    RiskAssessmentHistoryRepository,
)
from analysis_assessment.infrastructure.persistence.models import RiskAssessmentHistory


class TestRiskAssessmentHistoryRepository:
    """風險評估歷史記錄 Repository 測試"""
    
    @pytest.fixture
    def mock_session(self):
        """建立模擬的資料庫會話"""
        session = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.execute = AsyncMock()
        return session
    
    @pytest.fixture
    def repository(self, mock_session):
        """建立 Repository 實例"""
        return RiskAssessmentHistoryRepository(mock_session)
    
    @pytest.fixture
    def sample_risk_assessment(self):
        """建立測試用的風險評估"""
        return RiskAssessment.create(
            threat_id="threat-1",
            threat_asset_association_id="assoc-1",
            base_cvss_score=7.5,
            asset_importance_weight=1.5,
            affected_asset_count=2,
            asset_count_weight=0.02,
            final_risk_score=11.27,
            risk_level="Critical",
            pir_match_weight=0.3,
            cisa_kev_weight=0.5,
        )
    
    @pytest.mark.asyncio
    async def test_save_history(self, repository, mock_session, sample_risk_assessment):
        """測試儲存歷史記錄"""
        await repository.save_history(sample_risk_assessment)
        
        # 驗證 add 被呼叫
        mock_session.add.assert_called_once()
        # 驗證 flush 被呼叫
        mock_session.flush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_risk_assessment_id(
        self,
        repository,
        mock_session,
    ):
        """測試查詢風險評估的歷史記錄"""
        # 模擬查詢結果
        mock_history = MagicMock()
        mock_history.id = "history-1"
        mock_history.risk_assessment_id = "risk-1"
        mock_history.base_cvss_score = 7.5
        mock_history.asset_importance_weight = 1.5
        mock_history.asset_count_weight = 0.02
        mock_history.pir_match_weight = 0.3
        mock_history.cisa_kev_weight = 0.5
        mock_history.final_risk_score = 11.27
        mock_history.risk_level = "Critical"
        mock_history.calculation_details = '{"test": "data"}'
        mock_history.calculated_at = datetime.utcnow()
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_history]
        mock_session.execute.return_value = mock_result
        
        histories = await repository.get_by_risk_assessment_id("risk-1")
        
        assert len(histories) == 1
        assert histories[0]["id"] == "history-1"
        assert histories[0]["risk_assessment_id"] == "risk-1"
        assert histories[0]["final_risk_score"] == 11.27
    
    @pytest.mark.asyncio
    async def test_get_latest(self, repository, mock_session):
        """測試查詢最新的風險評估記錄"""
        # 模擬查詢結果
        mock_history = MagicMock()
        mock_history.id = "history-1"
        mock_history.risk_assessment_id = "risk-1"
        mock_history.base_cvss_score = 7.5
        mock_history.asset_importance_weight = 1.5
        mock_history.asset_count_weight = 0.02
        mock_history.pir_match_weight = 0.3
        mock_history.cisa_kev_weight = 0.5
        mock_history.final_risk_score = 11.27
        mock_history.risk_level = "Critical"
        mock_history.calculation_details = '{"test": "data"}'
        mock_history.calculated_at = datetime.utcnow()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_history
        mock_session.execute.return_value = mock_result
        
        latest = await repository.get_latest("risk-1")
        
        assert latest is not None
        assert latest["id"] == "history-1"
        assert latest["final_risk_score"] == 11.27
    
    @pytest.mark.asyncio
    async def test_get_latest_not_found(self, repository, mock_session):
        """測試查詢最新的風險評估記錄（不存在）"""
        # 模擬查詢結果為 None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        latest = await repository.get_latest("risk-1")
        
        assert latest is None
    
    @pytest.mark.asyncio
    async def test_get_by_time_range(self, repository, mock_session):
        """測試根據時間範圍查詢歷史記錄"""
        start_time = datetime(2024, 1, 1)
        end_time = datetime(2024, 12, 31)
        
        # 模擬查詢結果
        mock_history = MagicMock()
        mock_history.id = "history-1"
        mock_history.risk_assessment_id = "risk-1"
        mock_history.base_cvss_score = 7.5
        mock_history.asset_importance_weight = 1.5
        mock_history.asset_count_weight = 0.02
        mock_history.pir_match_weight = 0.3
        mock_history.cisa_kev_weight = 0.5
        mock_history.final_risk_score = 11.27
        mock_history.risk_level = "Critical"
        mock_history.calculation_details = '{"test": "data"}'
        mock_history.calculated_at = datetime(2024, 6, 1)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_history]
        mock_session.execute.return_value = mock_result
        
        histories = await repository.get_by_time_range(
            "risk-1", start_time=start_time, end_time=end_time
        )
        
        assert len(histories) == 1
        assert histories[0]["id"] == "history-1"

