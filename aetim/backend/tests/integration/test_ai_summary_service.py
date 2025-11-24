"""
AI 摘要服務整合測試

測試 AI 摘要服務的整合功能，包括 AI 服務呼叫、錯誤處理、回退機制。
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from reporting_notification.infrastructure.external_services.ai_summary_service import (
    AISummaryService,
)


class TestAISummaryService:
    """測試 AI 摘要服務"""

    @pytest.fixture
    def ai_summary_service(self):
        """建立 AI 摘要服務"""
        return AISummaryService(base_url="http://localhost:8001", timeout=30)

    @pytest.mark.asyncio
    async def test_generate_summary_success(self, ai_summary_service: AISummaryService):
        """測試成功生成摘要"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"summary": "這是生成的摘要內容"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await ai_summary_service.generate_summary(
                content="這是一段很長的內容，需要生成摘要...",
                target_length=100,
                language="zh-TW",
                style="executive",
            )

            assert result == "這是生成的摘要內容"

    @pytest.mark.asyncio
    async def test_generate_summary_timeout(self, ai_summary_service: AISummaryService):
        """測試超時處理"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )

            result = await ai_summary_service.generate_summary(
                content="這是一段很長的內容，需要生成摘要..." * 10,
                target_length=100,
            )

            # 應該使用回退機制
            assert len(result) <= 103  # 100 + "..."
            assert result.endswith("...")

    @pytest.mark.asyncio
    async def test_generate_summary_http_error(self, ai_summary_service: AISummaryService):
        """測試 HTTP 錯誤處理"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        http_error = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=http_error
            )

            result = await ai_summary_service.generate_summary(
                content="這是一段很長的內容，需要生成摘要..." * 10,
                target_length=100,
            )

            # 應該使用回退機制
            assert len(result) <= 103  # 100 + "..."
            assert result.endswith("...")

    @pytest.mark.asyncio
    async def test_generate_business_risk_description_success(
        self, ai_summary_service: AISummaryService
    ):
        """測試成功生成業務風險描述"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "business_description": "本週發現多個安全威脅，可能對業務運作造成影響。"
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await ai_summary_service.generate_business_risk_description(
                technical_description="CVE-2025-0001: Critical vulnerability in Apache HTTP Server"
            )

            assert "本週發現多個安全威脅" in result

    @pytest.mark.asyncio
    async def test_generate_business_risk_description_timeout(
        self, ai_summary_service: AISummaryService
    ):
        """測試業務風險描述生成超時處理"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )

            result = await ai_summary_service.generate_business_risk_description(
                technical_description="CVE-2025-0001: Critical vulnerability"
            )

            # 應該使用回退機制
            assert "本週發現多個安全威脅" in result
            assert "安全漏洞" in result or "威脅" in result

    @pytest.mark.asyncio
    async def test_generate_business_risk_description_http_error(
        self, ai_summary_service: AISummaryService
    ):
        """測試業務風險描述生成 HTTP 錯誤處理"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        http_error = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=http_error
            )

            result = await ai_summary_service.generate_business_risk_description(
                technical_description="CVE-2025-0001: Critical vulnerability"
            )

            # 應該使用回退機制
            assert "本週發現多個安全威脅" in result
            assert "安全漏洞" in result or "威脅" in result

    @pytest.mark.asyncio
    async def test_fallback_business_description(self, ai_summary_service: AISummaryService):
        """測試回退業務描述生成"""
        result = ai_summary_service._fallback_business_description(
            "CVE-2025-0001: Critical vulnerability in Apache HTTP Server"
        )

        # 驗證回退機制
        assert "本週發現多個安全威脅" in result
        assert "安全漏洞" in result  # CVE 被替換為安全漏洞
        assert "威脅" in result  # threat 被替換為威脅

    @pytest.mark.asyncio
    async def test_generate_summary_without_target_length(
        self, ai_summary_service: AISummaryService
    ):
        """測試生成摘要（無目標長度）"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"summary": "這是生成的摘要"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            result = await ai_summary_service.generate_summary(
                content="這是一段很長的內容，需要生成摘要..." * 10
            )

            assert result == "這是生成的摘要"

    @pytest.mark.asyncio
    async def test_generate_summary_fallback_without_target_length(
        self, ai_summary_service: AISummaryService
    ):
        """測試生成摘要回退（無目標長度）"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )

            result = await ai_summary_service.generate_summary(
                content="這是一段很長的內容，需要生成摘要..." * 10
            )

            # 應該使用預設長度（500）
            assert len(result) <= 503  # 500 + "..."
            assert result.endswith("...")

