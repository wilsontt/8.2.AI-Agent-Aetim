"""
風險分數分類服務單元測試

測試風險分數分類邏輯，符合 AC-012-4 的要求。
"""

import pytest

from analysis_assessment.domain.domain_services.risk_level_classifier import (
    RiskLevelClassifier,
)


class TestRiskLevelClassifier:
    """風險分數分類服務測試"""
    
    @pytest.fixture
    def classifier(self):
        """建立風險等級分類器實例"""
        return RiskLevelClassifier()
    
    def test_classify_critical(self, classifier):
        """測試分類為嚴重（Critical）"""
        assert classifier.classify(9.0) == "Critical"
        assert classifier.classify(8.0) == "Critical"
        assert classifier.classify(8.5) == "Critical"
        assert classifier.classify(10.0) == "Critical"
    
    def test_classify_high(self, classifier):
        """測試分類為高（High）"""
        assert classifier.classify(7.0) == "High"
        assert classifier.classify(6.0) == "High"
        assert classifier.classify(6.5) == "High"
        assert classifier.classify(7.9) == "High"
    
    def test_classify_medium(self, classifier):
        """測試分類為中（Medium）"""
        assert classifier.classify(5.0) == "Medium"
        assert classifier.classify(4.0) == "Medium"
        assert classifier.classify(4.5) == "Medium"
        assert classifier.classify(5.9) == "Medium"
    
    def test_classify_low(self, classifier):
        """測試分類為低（Low）"""
        assert classifier.classify(3.0) == "Low"
        assert classifier.classify(2.0) == "Low"
        assert classifier.classify(1.0) == "Low"
        assert classifier.classify(0.0) == "Low"
    
    def test_classify_boundary_values(self, classifier):
        """測試邊界值"""
        # 邊界值 8.0 應該是 Critical
        assert classifier.classify(8.0) == "Critical"
        # 邊界值 6.0 應該是 High
        assert classifier.classify(6.0) == "High"
        # 邊界值 4.0 應該是 Medium
        assert classifier.classify(4.0) == "Medium"
        # 邊界值 3.9 應該是 Low
        assert classifier.classify(3.9) == "Low"
    
    def test_classify_invalid_score(self, classifier):
        """測試無效的風險分數"""
        with pytest.raises(ValueError, match="風險分數必須在 0.0 - 10.0 範圍內"):
            classifier.classify(-1.0)
        
        with pytest.raises(ValueError, match="風險分數必須在 0.0 - 10.0 範圍內"):
            classifier.classify(11.0)
    
    def test_get_risk_level_label(self, classifier):
        """測試取得風險等級標籤"""
        assert classifier.get_risk_level_label("Critical") == "嚴重"
        assert classifier.get_risk_level_label("High") == "高"
        assert classifier.get_risk_level_label("Medium") == "中"
        assert classifier.get_risk_level_label("Low") == "低"
    
    def test_get_risk_level_color(self, classifier):
        """測試取得風險等級顏色"""
        assert "red" in classifier.get_risk_level_color("Critical")
        assert "orange" in classifier.get_risk_level_color("High")
        assert "yellow" in classifier.get_risk_level_color("Medium")
        assert "green" in classifier.get_risk_level_color("Low")
    
    def test_determine_risk_level_static(self):
        """測試靜態方法決定風險等級"""
        assert RiskLevelClassifier.determine_risk_level(9.0) == "Critical"
        assert RiskLevelClassifier.determine_risk_level(7.0) == "High"
        assert RiskLevelClassifier.determine_risk_level(5.0) == "Medium"
        assert RiskLevelClassifier.determine_risk_level(3.0) == "Low"

