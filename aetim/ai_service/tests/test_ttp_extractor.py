"""
TTPs 提取器單元測試

測試 TTPExtractor 的各種功能，包括：
- TTP 關鍵字匹配
- TTP ID 提取
- 邊界情況處理
"""

import pytest
from app.processors.ttp_extractor import TTPExtractor


class TestTTPExtractor:
    """TTPs 提取器測試"""
    
    @pytest.fixture
    def extractor(self):
        """建立 TTPExtractor 實例"""
        return TTPExtractor()
    
    # ========== extract 方法測試 ==========
    
    def test_extract_phishing_ttp(self, extractor):
        """測試提取釣魚 TTP"""
        text = "This is a phishing attack targeting users"
        result = extractor.extract(text)
        
        assert "T1566.001" in result
    
    def test_extract_command_execution_ttp(self, extractor):
        """測試提取命令執行 TTP"""
        text = "Command execution via PowerShell"
        result = extractor.extract(text)
        
        assert "T1059.001" in result
    
    def test_extract_multiple_ttps(self, extractor):
        """測試提取多個 TTP"""
        text = "Phishing attack followed by command execution via PowerShell"
        result = extractor.extract(text)
        
        assert len(result) >= 2
        assert "T1566.001" in result
        assert "T1059.001" in result
    
    def test_extract_chinese_keywords(self, extractor):
        """測試中文關鍵字匹配"""
        text = "這是一個釣魚攻擊"
        result = extractor.extract(text)
        
        assert "T1566.001" in result
    
    def test_extract_case_insensitive(self, extractor):
        """測試大小寫不敏感匹配"""
        text = "PHISHING ATTACK"
        result = extractor.extract(text)
        
        assert "T1566.001" in result
    
    def test_extract_no_ttps(self, extractor):
        """測試文字中沒有 TTP 時返回空列表"""
        text = "This is a general security notice"
        result = extractor.extract(text)
        
        assert result == []
    
    def test_extract_empty_string(self, extractor):
        """測試空字串"""
        result = extractor.extract("")
        assert result == []
    
    def test_extract_none_input(self, extractor):
        """測試 None 輸入"""
        result = extractor.extract(None)
        assert result == []
    
    def test_extract_non_string_input(self, extractor):
        """測試非字串輸入"""
        result = extractor.extract(12345)
        assert result == []
    
    def test_extract_deduplication(self, extractor):
        """測試去重功能"""
        text = "Phishing attack. Phishing email sent."
        result = extractor.extract(text)
        
        # 應去重，只返回一個 TTP ID
        assert result.count("T1566.001") == 0  # 列表中不應有重複
        assert "T1566.001" in result  # 但應包含該 TTP
    
    def test_extract_sorted_result(self, extractor):
        """測試結果是否排序"""
        text = "Phishing attack and command execution"
        result = extractor.extract(text)
        
        # 結果應按 TTP ID 排序
        assert result == sorted(result)
    
    # ========== get_ttp_info 方法測試 ==========
    
    def test_get_ttp_info_existing(self, extractor):
        """測試取得存在的 TTP 資訊"""
        info = extractor.get_ttp_info("T1566.001")
        
        assert info["id"] == "T1566.001"
        assert len(info["keywords"]) > 0
    
    def test_get_ttp_info_nonexistent(self, extractor):
        """測試取得不存在的 TTP 資訊"""
        info = extractor.get_ttp_info("T9999.999")
        
        assert info["id"] == "T9999.999"
        assert info["keywords"] == []
    
    # ========== 真實場景測試 ==========
    
    def test_extract_from_security_advisory(self, extractor):
        """測試從安全通報中提取 TTP"""
        text = """
        This attack uses phishing emails to deliver malware.
        Once executed, the malware uses PowerShell for command execution.
        """
        result = extractor.extract(text)
        
        assert "T1566.001" in result
        assert "T1059.001" in result
    
    def test_extract_from_threat_report(self, extractor):
        """測試從威脅報告中提取 TTP"""
        text = """
        Attackers use credential theft to gain initial access.
        Then they use RDP for lateral movement.
        """
        result = extractor.extract(text)
        
        assert len(result) > 0

