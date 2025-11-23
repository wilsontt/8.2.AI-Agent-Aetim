"""
威脅提取服務整合測試

測試威脅提取服務的功能，包含 AI 服務整合和回退機制。
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from threat_intelligence.application.services.threat_extraction_service import (
    ThreatExtractionService,
    ExtractedThreatInfo,
)
from threat_intelligence.infrastructure.external_services.ai_service_client import (
    AIServiceClient,
)


@pytest.fixture
def mock_ai_service_client():
    """建立模擬的 AI 服務客戶端"""
    client = MagicMock(spec=AIServiceClient)
    client.base_url = "http://localhost:8001"
    client.timeout = 30
    client.health_check = AsyncMock(return_value=True)
    client.extract_threat_info = AsyncMock(
        return_value={
            "cves": ["CVE-2024-12345"],
            "products": [
                {
                    "product_name": "Windows Server",
                    "product_version": "2019",
                    "product_type": "Operating System",
                }
            ],
            "ttps": ["T1566.001"],
            "iocs": {
                "ips": ["192.168.1.1"],
                "domains": ["example.com"],
                "hashes": [],
            },
            "confidence": 0.95,
        }
    )
    return client


@pytest.mark.asyncio
class TestThreatExtractionService:
    """威脅提取服務測試"""
    
    async def test_extract_with_ai_service_success(self, mock_ai_service_client):
        """測試使用 AI 服務成功提取"""
        service = ThreatExtractionService(
            ai_service_client=mock_ai_service_client,
            use_fallback=True,
        )
        
        text = "Windows Server 2019 存在 CVE-2024-12345 漏洞"
        result = await service.extract_threat_info(text)
        
        assert result.source == "ai"
        assert "CVE-2024-12345" in result.cves
        assert len(result.products) > 0
        assert result.confidence == 0.95
        mock_ai_service_client.extract_threat_info.assert_called_once()
    
    async def test_extract_with_ai_service_failure_fallback(self, mock_ai_service_client):
        """測試 AI 服務失敗時使用回退機制"""
        # 模擬 AI 服務失敗
        mock_ai_service_client.extract_threat_info.side_effect = Exception("AI 服務錯誤")
        
        service = ThreatExtractionService(
            ai_service_client=mock_ai_service_client,
            use_fallback=True,
        )
        
        text = "Windows Server 2019 存在 CVE-2024-12345 漏洞，攻擊者使用 T1566.001"
        result = await service.extract_threat_info(text)
        
        assert result.source == "rule_based"
        assert "CVE-2024-12345" in result.cves
        assert len(result.products) > 0
        assert "T1566.001" in result.ttps
        assert result.confidence == 0.5
    
    async def test_extract_with_rule_based_only(self):
        """測試僅使用規則基礎方法"""
        service = ThreatExtractionService(
            ai_service_client=None,
            use_fallback=True,
        )
        
        text = "Windows Server 2019 存在 CVE-2024-12345 漏洞，IP 位址：192.168.1.1"
        result = await service.extract_threat_info(text)
        
        assert result.source == "rule_based"
        assert "CVE-2024-12345" in result.cves
        assert len(result.products) > 0
        assert "192.168.1.1" in result.iocs["ips"]
        assert result.confidence == 0.5
    
    async def test_extract_with_force_fallback(self, mock_ai_service_client):
        """測試強制使用回退機制"""
        service = ThreatExtractionService(
            ai_service_client=mock_ai_service_client,
            use_fallback=True,
        )
        
        text = "Windows Server 2019 存在 CVE-2024-12345 漏洞"
        result = await service.extract_threat_info(text, force_fallback=True)
        
        assert result.source == "rule_based"
        mock_ai_service_client.extract_threat_info.assert_not_called()
    
    async def test_extract_without_fallback(self, mock_ai_service_client):
        """測試不使用回退機制時 AI 服務失敗的情況"""
        # 模擬 AI 服務失敗
        mock_ai_service_client.extract_threat_info.side_effect = Exception("AI 服務錯誤")
        
        service = ThreatExtractionService(
            ai_service_client=mock_ai_service_client,
            use_fallback=False,
        )
        
        text = "Windows Server 2019 存在 CVE-2024-12345 漏洞"
        result = await service.extract_threat_info(text)
        
        assert result.source == "none"
        assert len(result.cves) == 0
        assert result.confidence == 0.0
    
    async def test_health_check_success(self, mock_ai_service_client):
        """測試健康檢查成功"""
        service = ThreatExtractionService(
            ai_service_client=mock_ai_service_client,
            use_fallback=True,
        )
        
        is_healthy = await service.check_ai_service_health()
        
        assert is_healthy is True
        mock_ai_service_client.health_check.assert_called_once()
    
    async def test_health_check_failure(self, mock_ai_service_client):
        """測試健康檢查失敗"""
        mock_ai_service_client.health_check.return_value = False
        
        service = ThreatExtractionService(
            ai_service_client=mock_ai_service_client,
            use_fallback=True,
        )
        
        is_healthy = await service.check_ai_service_health()
        
        assert is_healthy is False
    
    async def test_extract_cves(self):
        """測試 CVE 提取"""
        service = ThreatExtractionService()
        
        text = "CVE-2024-12345 和 CVE-2024-67890 是兩個漏洞"
        cves = service._extract_cves(text)
        
        assert "CVE-2024-12345" in cves
        assert "CVE-2024-67890" in cves
    
    async def test_extract_products(self):
        """測試產品提取"""
        service = ThreatExtractionService()
        
        text = "Windows Server 2019 和 Linux 5.4 存在漏洞"
        products = service._extract_products(text)
        
        assert len(products) > 0
        product_names = [p["product_name"] for p in products]
        assert "Windows" in product_names or "Linux" in product_names
    
    async def test_extract_ttps(self):
        """測試 TTPs 提取"""
        service = ThreatExtractionService()
        
        text = "攻擊者使用 T1566.001 和 T1059.003 進行攻擊"
        ttps = service._extract_ttps(text)
        
        assert "T1566.001" in ttps
        assert "T1059.003" in ttps
    
    async def test_extract_iocs(self):
        """測試 IOCs 提取"""
        service = ThreatExtractionService()
        
        text = "IP 位址：192.168.1.1，網域：example.com，雜湊值：abc123def456"
        iocs = service._extract_iocs(text)
        
        assert "192.168.1.1" in iocs["ips"]
        assert "example.com" in iocs["domains"]
        assert len(iocs["hashes"]) > 0

