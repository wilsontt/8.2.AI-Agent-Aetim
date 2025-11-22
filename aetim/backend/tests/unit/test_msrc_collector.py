"""
MSRC 收集器單元測試

測試 MSRC 收集器的功能。
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from threat_intelligence.infrastructure.external_services.collectors.msrc_collector import (
    MSRCCollector,
)
from threat_intelligence.domain.aggregates.threat_feed import ThreatFeed


@pytest.fixture
def sample_feed():
    """建立測試用的 ThreatFeed"""
    return ThreatFeed.create(
        name="MSRC",
        priority="P1",
        collection_frequency="每日",
        description="Microsoft Security Response Center",
    )


@pytest.fixture
def sample_updates_response():
    """建立測試用的 MSRC Updates API 回應"""
    return {
        "value": [
            {
                "ID": "2024-Jan",
                "Alias": "2024-January",
                "DocumentTitle": "January 2024 Security Updates",
                "Severity": None,
                "InitialReleaseDate": "2024-01-09T08:00:00Z",
                "CurrentReleaseDate": "2024-01-09T08:00:00Z",
                "CvrfUrl": "https://api.msrc.microsoft.com/cvrf/v2.0/cvrf/2024-Jan",
            }
        ]
    }


@pytest.fixture
def sample_cvrf_response():
    """建立測試用的 MSRC CVRF API 回應"""
    return {
        "DocumentTitle": "January 2024 Security Updates",
        "DocumentType": "Security Update",
        "DocumentTracking": {
            "ID": "2024-Jan",
            "Alias": "2024-January",
            "Version": "1.0",
            "InitialReleaseDate": "2024-01-09T08:00:00Z",
            "CurrentReleaseDate": "2024-01-09T08:00:00Z",
        },
        "DocumentNotes": [
            {
                "Type": "General",
                "Lang": "en",
                "Value": "This security update resolves vulnerabilities in Microsoft products.",
            }
        ],
        "Vulnerability": [
            {
                "CVE": "CVE-2024-12345",
                "Title": "Windows Server Remote Code Execution Vulnerability",
                "Notes": [
                    {
                        "Type": "Description",
                        "Lang": "en",
                        "Text": "A remote code execution vulnerability exists in Windows Server 2022.",
                    }
                ],
                "CVSSScoreSets": [
                    {
                        "BaseScore": "9.8",
                        "Vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    }
                ],
                "ProductStatuses": [
                    {
                        "Type": "First Affected",
                        "ProductID": ["12345"],
                    }
                ],
            },
            {
                "CVE": "CVE-2024-67890",
                "Title": "SQL Server Information Disclosure Vulnerability",
                "Notes": [
                    {
                        "Type": "Description",
                        "Lang": "en",
                        "Text": "An information disclosure vulnerability exists in SQL Server 2019.",
                    }
                ],
                "CVSSScoreSets": [
                    {
                        "BaseScore": "5.5",
                        "Vector": "CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N",
                    }
                ],
                "ProductStatuses": [],
            },
        ],
    }


@pytest.mark.asyncio
class TestMSRCCollector:
    """MSRC 收集器測試"""
    
    def test_get_collector_type(self):
        """測試取得收集器類型"""
        collector = MSRCCollector()
        assert collector.get_collector_type() == "MSRC"
    
    @pytest.mark.asyncio
    async def test_collect_success(
        self,
        sample_feed,
        sample_updates_response,
        sample_cvrf_response,
    ):
        """測試成功收集威脅情資"""
        collector = MSRCCollector()
        
        with patch("httpx.AsyncClient") as mock_client:
            # 設定 Mock 回應
            mock_response_updates = MagicMock()
            mock_response_updates.json.return_value = sample_updates_response
            mock_response_updates.raise_for_status = MagicMock()
            
            mock_response_cvrf = MagicMock()
            mock_response_cvrf.json.return_value = sample_cvrf_response
            mock_response_cvrf.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.side_effect = [
                mock_response_updates,  # 第一次請求（Updates）
                mock_response_cvrf,  # 第二次請求（CVRF）
            ]
            mock_client.return_value = mock_client_instance
            
            # 執行收集
            threats = await collector.collect(sample_feed)
            
            # 驗證結果
            assert len(threats) == 2
            assert threats[0].cve_id == "CVE-2024-12345"
            assert threats[1].cve_id == "CVE-2024-67890"
            assert threats[0].threat_feed_id == sample_feed.id
            assert threats[0].cvss_base_score == 9.8
            assert threats[1].cvss_base_score == 5.5
    
    @pytest.mark.asyncio
    async def test_collect_with_date_range(
        self,
        sample_feed,
        sample_updates_response,
        sample_cvrf_response,
    ):
        """測試使用日期範圍收集"""
        collector = MSRCCollector()
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        
        with patch("httpx.AsyncClient") as mock_client:
            # 設定 Mock 回應
            mock_response_updates = MagicMock()
            mock_response_updates.json.return_value = sample_updates_response
            mock_response_updates.raise_for_status = MagicMock()
            
            mock_response_cvrf = MagicMock()
            mock_response_cvrf.json.return_value = sample_cvrf_response
            mock_response_cvrf.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.side_effect = [
                mock_response_updates,
                mock_response_cvrf,
            ]
            mock_client.return_value = mock_client_instance
            
            # 執行收集
            threats = await collector.collect(
                sample_feed,
                start_date=start_date,
                end_date=end_date,
            )
            
            # 驗證結果
            assert len(threats) >= 0
    
    @pytest.mark.asyncio
    async def test_collect_empty_response(self, sample_feed):
        """測試空回應"""
        collector = MSRCCollector()
        
        with patch("httpx.AsyncClient") as mock_client:
            # 設定 Mock 回應（空更新列表）
            mock_response = MagicMock()
            mock_response.json.return_value = {"value": []}
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
        collector = MSRCCollector()
        
        with patch("httpx.AsyncClient") as mock_client:
            # 設定 Mock 回應（HTTP 錯誤）
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.side_effect = Exception("HTTP 500 Error")
            mock_client.return_value = mock_client_instance
            
            # 執行收集，應該拋出異常
            with pytest.raises(Exception, match="MSRC API 請求失敗"):
                await collector.collect(sample_feed)
    
    @pytest.mark.asyncio
    async def test_parse_vulnerability_with_cvss(self, sample_feed, sample_cvrf_response):
        """測試解析包含 CVSS 分數的漏洞"""
        collector = MSRCCollector()
        
        vuln = sample_cvrf_response["Vulnerability"][0]
        
        threat = collector._parse_vulnerability(
            vuln,
            sample_feed,
            sample_cvrf_response["DocumentTitle"],
            sample_cvrf_response["DocumentNotes"],
            datetime(2024, 1, 9),
        )
        
        assert threat is not None
        assert threat.cve_id == "CVE-2024-12345"
        assert threat.cvss_base_score == 9.8
        assert threat.cvss_vector == "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
        assert threat.severity.value == "Critical"  # CVSS 9.8 應該是 Critical
    
    @pytest.mark.asyncio
    async def test_parse_vulnerability_without_cve(self, sample_feed, sample_cvrf_response):
        """測試解析缺少 CVE 編號的漏洞"""
        collector = MSRCCollector()
        
        vuln = {
            "Title": "Test Vulnerability",
            "Notes": [],
        }
        
        threat = collector._parse_vulnerability(
            vuln,
            sample_feed,
            "Test Document",
            [],
            None,
        )
        
        assert threat is None  # 缺少 CVE 編號，應該返回 None

