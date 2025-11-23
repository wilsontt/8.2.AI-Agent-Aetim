"""
AI 服務客戶端

用於呼叫 AI 服務進行威脅資訊提取。
"""

import httpx
from typing import Dict, List, Optional
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class AIServiceClient:
    """
    AI 服務客戶端
    
    用於呼叫 AI 服務進行威脅資訊提取。
    """
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        初始化 AI 服務客戶端
        
        Args:
            base_url: AI 服務的基礎 URL
            timeout: 請求超時時間（秒，預設 30 秒）
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
    
    async def health_check(self) -> bool:
        """
        檢查 AI 服務健康狀態
        
        Returns:
            bool: AI 服務是否可用
        """
        try:
            health_url = f"{self.base_url}/health"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(health_url)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.warning(
                f"AI 服務健康檢查失敗：{str(e)}",
                extra={"url": health_url, "error": str(e)}
            )
            return False
    
    async def extract_threat_info(self, text: str) -> Dict:
        """
        提取威脅資訊
        
        Args:
            text: 要提取的文字內容
        
        Returns:
            Dict: 提取結果，包含：
                - cves: List[str] - CVE 編號列表
                - products: List[Dict] - 產品資訊列表
                - ttps: List[str] - TTPs 列表
                - iocs: Dict[str, List[str]] - IOCs 字典
                - confidence: float - 信心分數
        
        Raises:
            httpx.HTTPError: HTTP 請求錯誤
            httpx.TimeoutException: 請求超時
            Exception: 其他錯誤
        """
        url = f"{self.base_url}/api/v1/ai/extract"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json={"text": text},
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as e:
            logger.error(
                f"AI 服務請求超時（{self.timeout} 秒）",
                extra={
                    "url": url,
                    "timeout": self.timeout,
                    "error": str(e),
                }
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                "AI 服務請求失敗",
                extra={
                    "url": url,
                    "status_code": e.response.status_code if hasattr(e, "response") else None,
                    "error": str(e),
                }
            )
            raise
        except Exception as e:
            logger.error(
                "AI 服務請求發生未預期錯誤",
                extra={
                    "url": url,
                    "error": str(e),
                }
            )
            raise

