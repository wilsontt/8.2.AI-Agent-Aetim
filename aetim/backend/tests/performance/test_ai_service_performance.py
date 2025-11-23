"""
AI 服務處理效能測試

測試 AI 服務處理的效能，包含：
- AI 服務處理效能（單一請求 ≤ 5 秒）
"""

import pytest
import sys
import os
import time
import asyncio
from unittest.mock import AsyncMock, MagicMock

# 加入專案路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from threat_intelligence.infrastructure.external_services.ai_service_client import AIServiceClient
from threat_intelligence.application.services.threat_extraction_service import ThreatExtractionService


@pytest.fixture
def mock_ai_service_client():
    """建立模擬的 AI 服務客戶端（模擬處理時間）"""
    client = MagicMock(spec=AIServiceClient)
    client.base_url = "http://localhost:8001"
    client.timeout = 30
    
    async def extract_threat_info(text: str):
        # 模擬 AI 服務處理時間（約 1 秒）
        await asyncio.sleep(1.0)
        return {
            "cves": ["CVE-2024-12345"],
            "products": [{"product_name": "Test Product"}],
            "ttps": ["T1566.001"],
            "iocs": {"ips": [], "domains": [], "hashes": []},
            "confidence": 0.95,
        }
    
    client.extract_threat_info = extract_threat_info
    return client


@pytest.mark.asyncio
class TestAIServicePerformance:
    """AI 服務處理效能測試"""
    
    async def test_ai_service_extraction_performance(
        self,
        mock_ai_service_client,
    ):
        """
        測試 AI 服務提取效能
        
        要求：單一請求 ≤ 5 秒
        """
        extraction_service = ThreatExtractionService(
            ai_service_client=mock_ai_service_client,
            use_fallback=True,
        )
        
        text = "Windows Server 2019 存在 CVE-2024-12345 漏洞，攻擊者使用 T1566.001 進行攻擊"
        
        # 測量提取時間
        start_time = time.time()
        
        result = await extraction_service.extract_threat_info(text)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 驗證提取成功
        assert result.source == "ai"
        assert len(result.cves) > 0
        
        # 驗證效能要求（≤ 5 秒）
        assert elapsed_time <= 5.0, f"AI 服務提取時間 {elapsed_time:.2f} 秒超過 5 秒限制"
        
        print(f"AI 服務提取時間：{elapsed_time:.2f} 秒")
    
    async def test_ai_service_fallback_performance(
        self,
        mock_ai_service_client,
    ):
        """
        測試 AI 服務失敗時回退機制的效能
        """
        # 模擬 AI 服務失敗
        mock_ai_service_client.extract_threat_info.side_effect = Exception("AI 服務錯誤")
        
        extraction_service = ThreatExtractionService(
            ai_service_client=mock_ai_service_client,
            use_fallback=True,
        )
        
        text = "Windows Server 2019 存在 CVE-2024-12345 漏洞，攻擊者使用 T1566.001 進行攻擊"
        
        # 測量回退機制時間
        start_time = time.time()
        
        result = await extraction_service.extract_threat_info(text)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 驗證回退機制成功
        assert result.source == "rule_based"
        assert len(result.cves) > 0
        
        # 驗證效能要求（回退機制應該很快，≤ 1 秒）
        assert elapsed_time <= 1.0, f"回退機制時間 {elapsed_time:.2f} 秒超過 1 秒限制"
        
        print(f"回退機制時間：{elapsed_time:.2f} 秒")

