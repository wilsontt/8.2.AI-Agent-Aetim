"""
AI 摘要服務

用於呼叫 AI 服務生成報告摘要和業務風險描述。
"""

import httpx
from typing import Optional
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class AISummaryService:
    """
    AI 摘要服務
    
    用於呼叫 AI 服務生成報告摘要和業務風險描述（AC-015-4）。
    """
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        初始化 AI 摘要服務
        
        Args:
            base_url: AI 服務的基礎 URL
            timeout: 請求超時時間（秒，預設 30 秒）
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
    
    async def generate_summary(
        self,
        content: str,
        target_length: Optional[int] = None,
        language: str = "zh-TW",
        style: str = "executive",
    ) -> str:
        """
        生成摘要
        
        Args:
            content: 要摘要的內容
            target_length: 目標長度（可選）
            language: 語言（預設：zh-TW）
            style: 風格（預設：executive）
        
        Returns:
            str: 生成的摘要
        
        Raises:
            httpx.HTTPError: HTTP 請求錯誤
            httpx.TimeoutException: 請求超時
            Exception: 其他錯誤
        """
        url = f"{self.base_url}/api/v1/ai/summarize"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json={
                        "content": content,
                        "target_length": target_length,
                        "language": language,
                        "style": style,
                    },
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                result = response.json()
                return result.get("summary", "")
        except httpx.TimeoutException as e:
            logger.warning(
                "AI 摘要服務請求超時，使用回退機制",
                extra={
                    "url": url,
                    "timeout": self.timeout,
                    "error": str(e),
                }
            )
            # 回退：返回前 N 個字元
            if target_length:
                return content[:target_length] + "..."
            return content[:500] + "..."
        except httpx.HTTPError as e:
            logger.warning(
                "AI 摘要服務請求失敗，使用回退機制",
                extra={
                    "url": url,
                    "status_code": e.response.status_code if hasattr(e, "response") else None,
                    "error": str(e),
                }
            )
            # 回退：返回前 N 個字元
            if target_length:
                return content[:target_length] + "..."
            return content[:500] + "..."
        except Exception as e:
            logger.error(
                "AI 摘要服務發生未知錯誤，使用回退機制",
                extra={"url": url, "error": str(e)},
                exc_info=True,
            )
            # 回退：返回前 N 個字元
            if target_length:
                return content[:target_length] + "..."
            return content[:500] + "..."
    
    async def generate_business_risk_description(
        self, technical_description: str
    ) -> str:
        """
        生成業務風險描述（AC-015-4）
        
        將技術描述轉換為非技術語言，說明威脅對業務的影響。
        
        Args:
            technical_description: 技術描述
        
        Returns:
            str: 業務風險描述（非技術語言）
        
        Raises:
            httpx.HTTPError: HTTP 請求錯誤
            httpx.TimeoutException: 請求超時
            Exception: 其他錯誤
        """
        url = f"{self.base_url}/api/v1/ai/translate-to-business"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json={"technical_description": technical_description},
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                result = response.json()
                return result.get("business_description", "")
        except httpx.TimeoutException as e:
            logger.warning(
                "AI 業務風險描述服務請求超時，使用回退機制",
                extra={
                    "url": url,
                    "timeout": self.timeout,
                    "error": str(e),
                }
            )
            # 回退：返回簡化的業務描述
            return self._fallback_business_description(technical_description)
        except httpx.HTTPError as e:
            logger.warning(
                "AI 業務風險描述服務請求失敗，使用回退機制",
                extra={
                    "url": url,
                    "status_code": e.response.status_code if hasattr(e, "response") else None,
                    "error": str(e),
                }
            )
            # 回退：返回簡化的業務描述
            return self._fallback_business_description(technical_description)
        except Exception as e:
            logger.error(
                "AI 業務風險描述服務發生未知錯誤，使用回退機制",
                extra={"url": url, "error": str(e)},
                exc_info=True,
            )
            # 回退：返回簡化的業務描述
            return self._fallback_business_description(technical_description)
    
    def _fallback_business_description(self, technical_description: str) -> str:
        """
        回退機制：生成簡化的業務描述
        
        Args:
            technical_description: 技術描述
        
        Returns:
            str: 簡化的業務描述
        """
        # 簡單的規則基礎轉換
        description = technical_description
        
        # 替換技術術語為業務術語
        replacements = {
            "CVE": "安全漏洞",
            "CVSS": "風險評分",
            "exploit": "攻擊",
            "vulnerability": "弱點",
            "threat": "威脅",
            "risk": "風險",
        }
        
        for tech_term, business_term in replacements.items():
            description = description.replace(tech_term, business_term)
        
        return f"本週發現多個安全威脅，可能對業務運作造成影響。建議優先處理高風險項目，確保系統安全。詳細技術資訊：{description[:200]}..."

