"""
CISA KEV 收集器單元測試

測試 CISA KEV 收集器的功能。
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from threat_intelligence.infrastructure.external_services.collectors.cisa_kev_collector import CISAKEVCollector
from threat_intelligence.domain.aggregates.threat_feed import ThreatFeed
from threat_intelligence.domain.value_objects.threat_feed_priority import ThreatFeedPriority
from threat_intelligence.domain.value_objects.collection_frequency import CollectionFrequency


@pytest.fixture
def sample_feed():
    """建立測試用的 ThreatFeed"""
    return ThreatFeed.create(
        name="CISA KEV",
        priority="P0",
        collection_frequency="每小時",
        description="CISA Known Exploited Vulnerabilities",
    )


@pytest.fixture
def sample_kev_response():
    """建立測試用的 CISA KEV API 回應"""
    return {
        "title": "CISA Known Exploited Vulnerabilities Catalog",
        "catalogVersion": "2024.01.15",
        "dateReleased": "2024-01-15",
        "count": 2,
        "vulnerabilities": [
            {
                "cveID": "CVE-2024-12345",
                "vendorProject": "Microsoft",
                "product": "Windows 10",
                "vulnerabilityName": "Remote Code Execution",
                "dateAdded": "2024-01-10",
                "shortDescription": "A critical vulnerability that allows remote code execution.",
                "requiredAction": "Apply updates immediately.",
                "dueDate": "2024-01-20",
                "knownRansomwareCampaignUse": "Yes",
            },
            {
                "cveID": "CVE-2024-67890",
                "vendorProject": "VMware",
                "product": "ESXi 7.0.3",
                "vulnerabilityName": "Privilege Escalation",
                "dateAdded": "2024-01-12",
                "shortDescription": "A vulnerability that allows privilege escalation.",
                "requiredAction": "Upgrade to version 7.0.4 or later.",
                "dueDate": "2024-01-22",
                "knownRansomwareCampaignUse": "No",
                "cvssScore": "9.8",
            },
        ],
    }


@pytest.mark.asyncio
class TestCISAKEVCollector:
    """CISA KEV 收集器測試"""
    
    def test_get_collector_type(self):
        """測試取得收集器類型"""
        collector = CISAKEVCollector()
        assert collector.get_collector_type() == "CISA_KEV"
    
    @pytest.mark.asyncio
    async def test_collect_success(self, sample_feed, sample_kev_response):
        """測試成功收集威脅情資"""
        collector = CISAKEVCollector()
        
        with patch("httpx.AsyncClient") as mock_client:
            # 設定 Mock 回應
            mock_response = MagicMock()
            mock_response.json.return_value = sample_kev_response
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            # 執行收集
            threats = await collector.collect(sample_feed)
            
            # 驗證結果
            assert len(threats) == 2
            assert threats[0].cve_id == "CVE-2024-12345"
            assert threats[1].cve_id == "CVE-2024-67890"
            assert threats[0].threat_feed_id == sample_feed.id
            assert threats[1].threat_feed_id == sample_feed.id
    
    @pytest.mark.asyncio
    async def test_collect_empty_response(self, sample_feed):
        """測試空回應"""
        collector = CISAKEVCollector()
        
        with patch("httpx.AsyncClient") as mock_client:
            # 設定 Mock 回應（空漏洞列表）
            mock_response = MagicMock()
            mock_response.json.return_value = {"vulnerabilities": []}
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            # 執行收集
            threats = await collector.collect(sample_feed)
            
            # 驗證結果
            assert len(threats) == 0
    
    @pytest.mark.asyncio
    async def test_collect_http_error(self, sample_feed):
        """測試 HTTP 錯誤"""
        collector = CISAKEVCollector()
        
        with patch("httpx.AsyncClient") as mock_client:
            # 設定 Mock 回應（HTTP 錯誤）
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.side_effect = Exception("HTTP 500 Error")
            mock_client.return_value = mock_client_instance
            
            # 執行收集，應該拋出異常
            with pytest.raises(Exception, match="CISA KEV API 請求失敗"):
                await collector.collect(sample_feed)
    
    @pytest.mark.asyncio
    async def test_collect_json_error(self, sample_feed):
        """測試 JSON 解析錯誤"""
        collector = CISAKEVCollector()
        
        with patch("httpx.AsyncClient") as mock_client:
            import json
            
            # 設定 Mock 回應（無效 JSON）
            mock_response = MagicMock()
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            # 執行收集，應該拋出異常
            with pytest.raises(Exception, match="CISA KEV API 回應格式錯誤"):
                await collector.collect(sample_feed)
    
    @pytest.mark.asyncio
    async def test_parse_vulnerability_with_cvss(self, sample_feed, sample_kev_response):
        """測試解析包含 CVSS 分數的漏洞"""
        collector = CISAKEVCollector()
        
        vuln = sample_kev_response["vulnerabilities"][1]  # 包含 CVSS 分數的漏洞
        
        threat = collector._parse_vulnerability(vuln, sample_feed)
        
        assert threat is not None
        assert threat.cve_id == "CVE-2024-67890"
        assert threat.cvss_base_score == 9.8
        assert threat.severity.value == "Critical"  # CVSS 9.8 應該是 Critical
    
    @pytest.mark.asyncio
    async def test_parse_vulnerability_without_cvss(self, sample_feed, sample_kev_response):
        """測試解析不包含 CVSS 分數的漏洞"""
        collector = CISAKEVCollector()
        
        vuln = sample_kev_response["vulnerabilities"][0]  # 不包含 CVSS 分數的漏洞
        
        threat = collector._parse_vulnerability(vuln, sample_feed)
        
        assert threat is not None
        assert threat.cve_id == "CVE-2024-12345"
        assert threat.cvss_base_score is None
        assert threat.severity.value == "High"  # 沒有 CVSS，但已知被利用，預設為 High
    
    @pytest.mark.asyncio
    async def test_parse_vulnerability_without_cve(self, sample_feed):
        """測試解析缺少 CVE 編號的漏洞"""
        collector = CISAKEVCollector()
        
        vuln = {
            "vendorProject": "Microsoft",
            "product": "Windows 10",
            "vulnerabilityName": "Remote Code Execution",
        }
        
        threat = collector._parse_vulnerability(vuln, sample_feed)
        
        assert threat is None  # 缺少 CVE 編號，應該返回 None
    
    @pytest.mark.asyncio
    async def test_parse_vulnerability_product_extraction(self, sample_feed, sample_kev_response):
        """測試產品資訊提取"""
        collector = CISAKEVCollector()
        
        vuln = sample_kev_response["vulnerabilities"][0]
        
        threat = collector._parse_vulnerability(vuln, sample_feed)
        
        assert threat is not None
        assert len(threat.products) > 0
        assert threat.products[0].product_name in ["Microsoft", "Windows 10"]
    
    @pytest.mark.asyncio
    async def test_parse_vulnerability_required_action(self, sample_feed, sample_kev_response):
        """測試 Required Action 提取"""
        collector = CISAKEVCollector()
        
        vuln = sample_kev_response["vulnerabilities"][0]
        
        threat = collector._parse_vulnerability(vuln, sample_feed)
        
        assert threat is not None
        assert "Required Action" in threat.description
        assert "Apply updates immediately" in threat.description

