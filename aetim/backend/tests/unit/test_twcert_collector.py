"""
TWCERT 收集器單元測試

測試 TWCERT 收集器的功能。
"""

import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from threat_intelligence.infrastructure.external_services.collectors.twcert_collector import (
    TWCERTCollector,
)
from threat_intelligence.domain.aggregates.threat_feed import ThreatFeed


@pytest.fixture
def sample_feed():
    """建立測試用的 ThreatFeed"""
    return ThreatFeed.create(
        name="TWCERT",
        priority="P2",
        collection_frequency="每日",
        description="台灣電腦網路危機處理暨協調中心",
    )


@pytest.fixture
def mock_ai_service_client():
    """建立 Mock AI 服務客戶端"""
    client = AsyncMock()
    client.extract_threat_info = AsyncMock(return_value={
        "cve": ["CVE-2024-12345"],
        "products": [
            {"name": "Windows Server", "version": "2022"}
        ],
        "ttps": ["T1566.001"],
        "iocs": {
            "ips": ["192.168.1.1"],
            "domains": ["malicious.com"],
        },
        "confidence": 0.85,
    })
    return client


@pytest.fixture
def sample_twcert_html():
    """建立測試用的 TWCERT HTML 頁面"""
    return """
    <html>
        <head><title>TWCERT 資安情資</title></head>
        <body>
            <h1>資安情資</h1>
            <ul>
                <li><a href="/twcert/advisory/TA-2024-0001">TA-2024-0001: 重大安全漏洞通報</a></li>
                <li><a href="/twcert/advisory/TA-2024-0002">TA-2024-0002: 勒索軟體攻擊警告</a></li>
            </ul>
        </body>
    </html>
    """


@pytest.fixture
def sample_advisory_html():
    """建立測試用的 TWCERT 通報頁面"""
    return """
    <html>
        <head><title>TA-2024-0001: 重大安全漏洞通報</title></head>
        <body>
            <h1>TA-2024-0001: 重大安全漏洞通報</h1>
            <div class="content">
                <p>本中心接獲通報，發現 CVE-2024-12345 影響 Windows Server 2022。</p>
                <p>攻擊者可能利用此漏洞進行遠端程式碼執行。</p>
                <p>建議立即更新至最新版本。</p>
            </div>
        </body>
    </html>
    """


@pytest.mark.asyncio
class TestTWCERTCollector:
    """TWCERT 收集器測試"""
    
    def test_get_collector_type(self, mock_ai_service_client):
        """測試取得收集器類型"""
        collector = TWCERTCollector(ai_service_client=mock_ai_service_client)
        assert collector.get_collector_type() == "TWCERT"
    
    def test_init_without_ai_service(self):
        """測試未提供 AI 服務客戶端時初始化"""
        # 應該發出警告但不拋出異常
        collector = TWCERTCollector()
        assert collector.ai_service_client is None
    
    @pytest.mark.asyncio
    async def test_collect_success(
        self,
        sample_feed,
        mock_ai_service_client,
        sample_twcert_html,
        sample_advisory_html,
    ):
        """測試成功收集威脅情資"""
        collector = TWCERTCollector(ai_service_client=mock_ai_service_client)
        
        with patch("httpx.AsyncClient") as mock_client:
            # 設定 Mock 回應
            mock_response_advisory = MagicMock()
            mock_response_advisory.text = sample_twcert_html
            mock_response_advisory.raise_for_status = MagicMock()
            
            mock_response_detail = MagicMock()
            mock_response_detail.text = sample_advisory_html
            mock_response_detail.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.side_effect = [
                mock_response_advisory,  # 第一次請求（通報列表）
                mock_response_detail,  # 第二次請求（個別通報）
            ]
            mock_client.return_value = mock_client_instance
            
            # 執行收集
            threats = await collector.collect(sample_feed)
            
            # 驗證結果
            assert len(threats) >= 1
            assert threats[0].threat_feed_id == sample_feed.id
            
            # 驗證 AI 服務被呼叫
            assert mock_ai_service_client.extract_threat_info.called
    
    @pytest.mark.asyncio
    async def test_collect_without_ai_service(self, sample_feed):
        """測試未提供 AI 服務時收集（應該拋出異常）"""
        collector = TWCERTCollector()
        
        with pytest.raises(ValueError, match="TWCERT 收集器需要 AI 服務客戶端"):
            await collector.collect(sample_feed)
    
    @pytest.mark.asyncio
    async def test_collect_empty_response(
        self,
        sample_feed,
        mock_ai_service_client,
    ):
        """測試空回應"""
        collector = TWCERTCollector(ai_service_client=mock_ai_service_client)
        
        empty_html = """
        <html>
            <body>
                <h1>資安情資</h1>
                <p>目前沒有通報</p>
            </body>
        </html>
        """
        
        with patch("httpx.AsyncClient") as mock_client:
            # 設定 Mock 回應
            mock_response = MagicMock()
            mock_response.text = empty_html
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
    async def test_collect_http_error(
        self,
        sample_feed,
        mock_ai_service_client,
    ):
        """測試 HTTP 錯誤"""
        collector = TWCERTCollector(ai_service_client=mock_ai_service_client)
        
        with patch("httpx.AsyncClient") as mock_client:
            # 設定 Mock 回應（HTTP 錯誤）
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.side_effect = Exception("HTTP 500 Error")
            mock_client.return_value = mock_client_instance
            
            # 執行收集，應該拋出異常
            with pytest.raises(Exception, match="TWCERT 網站請求失敗"):
                await collector.collect(sample_feed)
    
    @pytest.mark.asyncio
    async def test_parse_advisory_with_cve(
        self,
        sample_feed,
        mock_ai_service_client,
        sample_advisory_html,
    ):
        """測試解析包含 CVE 的通報"""
        collector = TWCERTCollector(ai_service_client=mock_ai_service_client)
        
        advisory = {
            "url": "https://www.twcert.org.tw/twcert/advisory/TA-2024-0001",
            "title": "TA-2024-0001: 重大安全漏洞通報",
            "date": "2024-01-15",
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            # 設定 Mock 回應
            mock_response = MagicMock()
            mock_response.text = sample_advisory_html
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            # 執行解析
            threats = await collector._parse_advisory(advisory, sample_feed)
            
            # 驗證結果
            assert len(threats) >= 1
            assert threats[0].cve_id == "CVE-2024-12345"
            assert threats[0].threat_feed_id == sample_feed.id
    
    @pytest.mark.asyncio
    async def test_parse_advisory_without_cve(
        self,
        sample_feed,
        mock_ai_service_client,
    ):
        """測試解析沒有 CVE 的通報"""
        collector = TWCERTCollector(ai_service_client=mock_ai_service_client)
        
        # Mock AI 服務返回空 CVE 列表
        mock_ai_service_client.extract_threat_info.return_value = {
            "cve": [],
            "products": [],
            "ttps": [],
            "iocs": {},
            "confidence": 0.5,
        }
        
        advisory = {
            "url": "https://www.twcert.org.tw/twcert/advisory/TA-2024-0001",
            "title": "TA-2024-0001: 一般安全通報",
            "date": "2024-01-15",
        }
        
        advisory_html = """
        <html>
            <body>
                <h1>TA-2024-0001: 一般安全通報</h1>
                <div class="content">
                    <p>本中心發布一般安全通報，提醒使用者注意資安防護。</p>
                </div>
            </body>
        </html>
        """
        
        with patch("httpx.AsyncClient") as mock_client:
            # 設定 Mock 回應
            mock_response = MagicMock()
            mock_response.text = advisory_html
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            # 執行解析
            threats = await collector._parse_advisory(advisory, sample_feed)
            
            # 驗證結果（應該建立一個沒有 CVE 的威脅）
            assert len(threats) == 1
            assert threats[0].cve_id is None
            assert threats[0].title == "TA-2024-0001: 一般安全通報"

