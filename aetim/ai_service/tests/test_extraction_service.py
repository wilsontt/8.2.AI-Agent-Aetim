"""
整合提取服務單元測試

測試 ExtractionService 的各種功能，包括：
- 整合所有提取器
- 信心分數計算
- 錯誤處理
- 邊界情況處理
"""

import pytest
from unittest.mock import Mock, patch
from app.services.extraction_service import ExtractionService
from app.processors.cve_extractor import CVEExtractor
from app.processors.product_extractor import ProductExtractor
from app.processors.ttp_extractor import TTPExtractor
from app.processors.ioc_extractor import IOCExtractor


class TestExtractionService:
    """整合提取服務測試"""
    
    @pytest.fixture
    def service(self):
        """建立 ExtractionService 實例"""
        return ExtractionService()
    
    # ========== extract 方法測試 ==========
    
    def test_extract_all_types(self, service):
        """測試提取所有類型的威脅資訊"""
        text = """
        CVE-2024-12345 affects VMware ESXi 7.0.3.
        This is a phishing attack using IP 192.168.1.1 and domain malicious.com.
        """
        result = service.extract(text)
        
        assert "cve" in result
        assert "products" in result
        assert "ttps" in result
        assert "iocs" in result
        assert "confidence" in result
        
        assert len(result["cve"]) > 0
        assert len(result["products"]) > 0
        assert len(result["ttps"]) > 0
        assert len(result["iocs"]["ips"]) > 0 or len(result["iocs"]["domains"]) > 0
    
    def test_extract_cve_only(self, service):
        """測試僅提取 CVE"""
        text = "CVE-2024-12345 is a critical vulnerability"
        result = service.extract(text)
        
        assert len(result["cve"]) > 0
        assert "CVE-2024-12345" in result["cve"]
        assert result["confidence"] >= 0.3  # CVE 權重
    
    def test_extract_products_only(self, service):
        """測試僅提取產品"""
        text = "VMware ESXi 7.0.3 is affected"
        result = service.extract(text)
        
        assert len(result["products"]) > 0
        assert result["confidence"] >= 0.3  # Products 權重
    
    def test_extract_ttps_only(self, service):
        """測試僅提取 TTPs"""
        text = "This is a phishing attack"
        result = service.extract(text)
        
        assert len(result["ttps"]) > 0
        assert result["confidence"] >= 0.2  # TTPs 權重
    
    def test_extract_iocs_only(self, service):
        """測試僅提取 IOCs"""
        text = "IP: 192.168.1.1, Domain: malicious.com"
        result = service.extract(text)
        
        assert len(result["iocs"]["ips"]) > 0 or len(result["iocs"]["domains"]) > 0
        assert result["confidence"] >= 0.2  # IOCs 權重
    
    def test_extract_empty_string(self, service):
        """測試空字串"""
        result = service.extract("")
        
        assert result["cve"] == []
        assert result["products"] == []
        assert result["ttps"] == []
        assert result["iocs"] == {"ips": [], "domains": [], "hashes": []}
        assert result["confidence"] == 0.0
    
    def test_extract_none_input(self, service):
        """測試 None 輸入"""
        result = service.extract(None)
        
        assert result["cve"] == []
        assert result["confidence"] == 0.0
    
    def test_extract_non_string_input(self, service):
        """測試非字串輸入"""
        result = service.extract(12345)
        
        assert result["cve"] == []
        assert result["confidence"] == 0.0
    
    def test_extract_error_handling_cve(self, service):
        """測試 CVE 提取器錯誤處理"""
        # 建立會拋出異常的 CVE 提取器
        mock_cve_extractor = Mock(spec=CVEExtractor)
        mock_cve_extractor.extract_all.side_effect = Exception("CVE extractor error")
        
        service_with_mock = ExtractionService(cve_extractor=mock_cve_extractor)
        result = service_with_mock.extract("CVE-2024-12345")
        
        # 應處理錯誤並返回空列表
        assert result["cve"] == []
        # 其他提取器應正常運作
        assert "confidence" in result
    
    def test_extract_error_handling_product(self, service):
        """測試產品提取器錯誤處理"""
        mock_product_extractor = Mock(spec=ProductExtractor)
        mock_product_extractor.extract.side_effect = Exception("Product extractor error")
        
        service_with_mock = ExtractionService(product_extractor=mock_product_extractor)
        result = service_with_mock.extract("VMware ESXi 7.0.3")
        
        # 應處理錯誤並返回空列表
        assert result["products"] == []
        # 其他提取器應正常運作
        assert "confidence" in result
    
    def test_extract_error_handling_ttp(self, service):
        """測試 TTP 提取器錯誤處理"""
        mock_ttp_extractor = Mock(spec=TTPExtractor)
        mock_ttp_extractor.extract.side_effect = Exception("TTP extractor error")
        
        service_with_mock = ExtractionService(ttp_extractor=mock_ttp_extractor)
        result = service_with_mock.extract("Phishing attack")
        
        # 應處理錯誤並返回空列表
        assert result["ttps"] == []
        # 其他提取器應正常運作
        assert "confidence" in result
    
    def test_extract_error_handling_ioc(self, service):
        """測試 IOC 提取器錯誤處理"""
        mock_ioc_extractor = Mock(spec=IOCExtractor)
        mock_ioc_extractor.extract.side_effect = Exception("IOC extractor error")
        
        service_with_mock = ExtractionService(ioc_extractor=mock_ioc_extractor)
        result = service_with_mock.extract("IP: 192.168.1.1")
        
        # 應處理錯誤並返回空字典
        assert result["iocs"] == {"ips": [], "domains": [], "hashes": []}
        # 其他提取器應正常運作
        assert "confidence" in result
    
    # ========== _calculate_confidence 方法測試 ==========
    
    def test_calculate_confidence_all_types(self, service):
        """測試計算所有類型的信心分數"""
        cve = ["CVE-2024-12345"]
        products = [{"name": "VMware", "version": "7.0.3"}]
        ttps = ["T1566.001"]
        iocs = {"ips": ["192.168.1.1"], "domains": [], "hashes": []}
        
        confidence = service._calculate_confidence(cve, products, ttps, iocs)
        
        # 應為所有權重之和：0.3 + 0.3 + 0.2 + 0.2 = 1.0
        assert confidence == 1.0
    
    def test_calculate_confidence_cve_only(self, service):
        """測試僅 CVE 的信心分數"""
        cve = ["CVE-2024-12345"]
        products = []
        ttps = []
        iocs = {"ips": [], "domains": [], "hashes": []}
        
        confidence = service._calculate_confidence(cve, products, ttps, iocs)
        
        assert confidence == 0.3  # CVE 權重
    
    def test_calculate_confidence_products_only(self, service):
        """測試僅產品的信心分數"""
        cve = []
        products = [{"name": "VMware"}]
        ttps = []
        iocs = {"ips": [], "domains": [], "hashes": []}
        
        confidence = service._calculate_confidence(cve, products, ttps, iocs)
        
        assert confidence == 0.3  # Products 權重
    
    def test_calculate_confidence_ttps_only(self, service):
        """測試僅 TTPs 的信心分數"""
        cve = []
        products = []
        ttps = ["T1566.001"]
        iocs = {"ips": [], "domains": [], "hashes": []}
        
        confidence = service._calculate_confidence(cve, products, ttps, iocs)
        
        assert confidence == 0.2  # TTPs 權重
    
    def test_calculate_confidence_iocs_only(self, service):
        """測試僅 IOCs 的信心分數"""
        cve = []
        products = []
        ttps = []
        iocs = {"ips": ["192.168.1.1"], "domains": [], "hashes": []}
        
        confidence = service._calculate_confidence(cve, products, ttps, iocs)
        
        assert confidence == 0.2  # IOCs 權重
    
    def test_calculate_confidence_no_results(self, service):
        """測試無結果的信心分數"""
        cve = []
        products = []
        ttps = []
        iocs = {"ips": [], "domains": [], "hashes": []}
        
        confidence = service._calculate_confidence(cve, products, ttps, iocs)
        
        assert confidence == 0.0
    
    def test_calculate_confidence_partial_results(self, service):
        """測試部分結果的信心分數"""
        cve = ["CVE-2024-12345"]
        products = [{"name": "VMware"}]
        ttps = []
        iocs = {"ips": [], "domains": [], "hashes": []}
        
        confidence = service._calculate_confidence(cve, products, ttps, iocs)
        
        # CVE (0.3) + Products (0.3) = 0.6
        assert confidence == 0.6
    
    def test_calculate_confidence_ioc_with_ips(self, service):
        """測試包含 IP 的 IOC 信心分數"""
        cve = []
        products = []
        ttps = []
        iocs = {"ips": ["192.168.1.1"], "domains": [], "hashes": []}
        
        confidence = service._calculate_confidence(cve, products, ttps, iocs)
        
        assert confidence == 0.2
    
    def test_calculate_confidence_ioc_with_domains(self, service):
        """測試包含網域的 IOC 信心分數"""
        cve = []
        products = []
        ttps = []
        iocs = {"ips": [], "domains": ["malicious.com"], "hashes": []}
        
        confidence = service._calculate_confidence(cve, products, ttps, iocs)
        
        assert confidence == 0.2
    
    def test_calculate_confidence_ioc_with_hashes(self, service):
        """測試包含雜湊值的 IOC 信心分數"""
        cve = []
        products = []
        ttps = []
        iocs = {"ips": [], "domains": [], "hashes": ["abc123def456"]}
        
        confidence = service._calculate_confidence(cve, products, ttps, iocs)
        
        assert confidence == 0.2
    
    def test_calculate_confidence_ioc_empty(self, service):
        """測試空的 IOC 不計分"""
        cve = []
        products = []
        ttps = []
        iocs = {"ips": [], "domains": [], "hashes": []}
        
        confidence = service._calculate_confidence(cve, products, ttps, iocs)
        
        assert confidence == 0.0
    
    def test_calculate_confidence_max_one(self, service):
        """測試信心分數不超過 1.0"""
        cve = ["CVE-2024-12345"]
        products = [{"name": "VMware"}]
        ttps = ["T1566.001"]
        iocs = {"ips": ["192.168.1.1"], "domains": ["malicious.com"], "hashes": ["abc123"]}
        
        confidence = service._calculate_confidence(cve, products, ttps, iocs)
        
        assert confidence <= 1.0
    
    # ========== 真實場景測試 ==========
    
    def test_extract_from_security_advisory(self, service):
        """測試從安全通報中提取威脅資訊"""
        text = """
        VMware has released a security advisory for CVE-2024-12345.
        This vulnerability affects VMware ESXi 7.0.3.
        Attackers use phishing emails to deliver malware.
        Indicators of Compromise:
        - IP: 192.168.1.1
        - Domain: malicious.com
        - Hash: abc123def45678901234567890123456
        """
        result = service.extract(text)
        
        assert len(result["cve"]) > 0
        assert len(result["products"]) > 0
        assert len(result["ttps"]) > 0
        assert len(result["iocs"]["ips"]) > 0 or len(result["iocs"]["domains"]) > 0
        assert result["confidence"] > 0.0
    
    def test_extract_from_threat_report(self, service):
        """測試從威脅報告中提取威脅資訊"""
        text = """
        Threat Report: CVE-2024-12345
        Affected Products: Windows Server 2022, SQL Server 2019
        Attack Techniques: Phishing (T1566.001), Command Execution (T1059.001)
        IOCs:
        - IP: 10.0.0.1, 172.16.0.1
        - Domain: attacker.com, malware.net
        - Hash: def4567890123456789012345678901234567890123456789012345678901234
        """
        result = service.extract(text)
        
        assert len(result["cve"]) > 0
        assert len(result["products"]) > 0
        assert len(result["ttps"]) > 0
        assert len(result["iocs"]["ips"]) > 0
        assert len(result["iocs"]["domains"]) > 0
        assert len(result["iocs"]["hashes"]) > 0
        assert result["confidence"] >= 0.8  # 應有較高的信心分數
    
    def test_extract_minimal_text(self, service):
        """測試最小文字內容"""
        text = "CVE-2024-12345"
        result = service.extract(text)
        
        assert len(result["cve"]) > 0
        assert result["confidence"] >= 0.3

