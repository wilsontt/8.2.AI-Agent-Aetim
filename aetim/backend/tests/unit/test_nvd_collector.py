"""
NVD 收集器單元測試

測試 NVD 收集器的功能。
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from threat_intelligence.infrastructure.external_services.collectors.nvd_collector import (
    NVDCollector,
    RateLimiter,
)
from threat_intelligence.domain.aggregates.threat_feed import ThreatFeed
from threat_intelligence.domain.value_objects.threat_feed_priority import ThreatFeedPriority
from threat_intelligence.domain.value_objects.collection_frequency import CollectionFrequency


@pytest.fixture
def sample_feed():
    """建立測試用的 ThreatFeed"""
    return ThreatFeed.create(
        name="NVD",
        priority="P1",
        collection_frequency="每日",
        description="National Vulnerability Database",
    )


@pytest.fixture
def sample_nvd_response():
    """建立測試用的 NVD API 回應"""
    return {
        "resultsPerPage": 2,
        "startIndex": 0,
        "totalResults": 2,
        "format": "NVD_CVE",
        "version": "2.0",
        "timestamp": "2024-01-15T10:30:00.000",
        "vulnerabilities": [
            {
                "cve": {
                    "id": "CVE-2024-12345",
                    "sourceIdentifier": "cve@mitre.org",
                    "published": "2024-01-10T10:00:00.000",
                    "lastModified": "2024-01-12T10:00:00.000",
                    "vulnStatus": "Analyzed",
                    "descriptions": [
                        {
                            "lang": "en",
                            "value": "A critical vulnerability in Windows Server 2022.",
                        }
                    ],
                    "metrics": {
                        "cvssMetricV31": [
                            {
                                "source": "nvd@nist.gov",
                                "type": "Primary",
                                "cvssData": {
                                    "version": "3.1",
                                    "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                                    "baseScore": 9.8,
                                    "baseSeverity": "CRITICAL",
                                },
                            }
                        ]
                    },
                    "configurations": [
                        {
                            "nodes": [
                                {
                                    "operator": "OR",
                                    "cpeMatch": [
                                        {
                                            "vulnerable": True,
                                            "criteria": "cpe:2.3:a:microsoft:windows_server:2022:*:*:*:*:*:*:*",
                                        }
                                    ],
                                }
                            ]
                        }
                    ],
                }
            },
            {
                "cve": {
                    "id": "CVE-2024-67890",
                    "sourceIdentifier": "cve@mitre.org",
                    "published": "2024-01-12T10:00:00.000",
                    "lastModified": "2024-01-14T10:00:00.000",
                    "vulnStatus": "Analyzed",
                    "descriptions": [
                        {
                            "lang": "en",
                            "value": "A vulnerability in VMware ESXi 7.0.3.",
                        }
                    ],
                    "metrics": {
                        "cvssMetricV30": [
                            {
                                "source": "nvd@nist.gov",
                                "type": "Primary",
                                "cvssData": {
                                    "version": "3.0",
                                    "vectorString": "CVSS:3.0/AV:N/AC:L/PR:L/UI:N/S:U/C:L/I:L/A:L",
                                    "baseScore": 6.5,
                                    "baseSeverity": "MEDIUM",
                                },
                            }
                        ]
                    },
                    "configurations": [
                        {
                            "nodes": [
                                {
                                    "operator": "OR",
                                    "cpeMatch": [
                                        {
                                            "vulnerable": True,
                                            "criteria": "cpe:2.3:a:vmware:esxi:7.0.3:*:*:*:*:*:*:*",
                                        }
                                    ],
                                }
                            ]
                        }
                    ],
                }
            },
        ],
    }


@pytest.mark.asyncio
class TestNVDCollector:
    """NVD 收集器測試"""
    
    def test_get_collector_type(self):
        """測試取得收集器類型"""
        collector = NVDCollector()
        assert collector.get_collector_type() == "NVD"
    
    @pytest.mark.asyncio
    async def test_collect_success(self, sample_feed, sample_nvd_response):
        """測試成功收集威脅情資"""
        collector = NVDCollector()
        
        with patch("httpx.AsyncClient") as mock_client:
            # 設定 Mock 回應
            mock_response = MagicMock()
            mock_response.json.return_value = sample_nvd_response
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
    async def test_collect_with_incremental(self, sample_feed, sample_nvd_response):
        """測試增量收集"""
        collector = NVDCollector()
        
        # 設定最後收集時間
        sample_feed.last_collection_time = datetime.utcnow() - timedelta(days=1)
        
        with patch("httpx.AsyncClient") as mock_client:
            # 設定 Mock 回應
            mock_response = MagicMock()
            mock_response.json.return_value = sample_nvd_response
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
    
    @pytest.mark.asyncio
    async def test_collect_empty_response(self, sample_feed):
        """測試空回應"""
        collector = NVDCollector()
        
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
        collector = NVDCollector()
        
        with patch("httpx.AsyncClient") as mock_client:
            # 設定 Mock 回應（HTTP 錯誤）
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.side_effect = Exception("HTTP 500 Error")
            mock_client.return_value = mock_client_instance
            
            # 執行收集，應該拋出異常
            with pytest.raises(Exception, match="NVD API 請求失敗"):
                await collector.collect(sample_feed)
    
    @pytest.mark.asyncio
    async def test_parse_cve_with_cvss_v31(self, sample_feed, sample_nvd_response):
        """測試解析包含 CVSS v3.1 的 CVE"""
        collector = NVDCollector()
        
        cve_data = sample_nvd_response["vulnerabilities"][0]["cve"]
        
        threat = collector._parse_cve(cve_data, sample_feed)
        
        assert threat is not None
        assert threat.cve_id == "CVE-2024-12345"
        assert threat.cvss_base_score == 9.8
        assert threat.cvss_vector == "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
        assert threat.severity.value == "Critical"  # CVSS 9.8 應該是 Critical
    
    @pytest.mark.asyncio
    async def test_parse_cve_with_cvss_v30(self, sample_feed, sample_nvd_response):
        """測試解析包含 CVSS v3.0 的 CVE"""
        collector = NVDCollector()
        
        cve_data = sample_nvd_response["vulnerabilities"][1]["cve"]
        
        threat = collector._parse_cve(cve_data, sample_feed)
        
        assert threat is not None
        assert threat.cve_id == "CVE-2024-67890"
        assert threat.cvss_base_score == 6.5
        assert threat.severity.value == "Medium"  # CVSS 6.5 應該是 Medium
    
    @pytest.mark.asyncio
    async def test_parse_cpe(self):
        """測試 CPE 解析"""
        collector = NVDCollector()
        
        # 測試應用程式 CPE
        cpe_string = "cpe:2.3:a:microsoft:windows_server:2022:*:*:*:*:*:*:*"
        product_info = collector._parse_cpe(cpe_string)
        
        assert product_info is not None
        assert product_info["name"] == "microsoft windows_server"
        assert product_info["version"] == "2022"
        assert product_info["type"] == "Application"
        
        # 測試作業系統 CPE
        cpe_string = "cpe:2.3:o:vmware:esxi:7.0.3:*:*:*:*:*:*:*"
        product_info = collector._parse_cpe(cpe_string)
        
        assert product_info is not None
        assert product_info["name"] == "vmware esxi"
        assert product_info["version"] == "7.0.3"
        assert product_info["type"] == "Operating System"
    
    @pytest.mark.asyncio
    async def test_rate_limiter(self):
        """測試速率限制器"""
        rate_limiter = RateLimiter(max_requests=2, window_seconds=1)
        
        # 第一次請求，不應該等待
        start_time = datetime.utcnow()
        await rate_limiter.wait_if_needed()
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        assert elapsed < 0.1  # 應該幾乎立即返回
        
        # 第二次請求，不應該等待
        start_time = datetime.utcnow()
        await rate_limiter.wait_if_needed()
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        assert elapsed < 0.1  # 應該幾乎立即返回
        
        # 第三次請求，應該等待（因為已達到最大請求數）
        start_time = datetime.utcnow()
        await rate_limiter.wait_if_needed()
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        assert elapsed >= 0.9  # 應該等待約 1 秒

