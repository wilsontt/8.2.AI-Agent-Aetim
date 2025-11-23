"""
AI 服務工廠

提供 AI 服務客戶端的建立功能。
"""

import os
from typing import Optional

from .ai_service_client import AIServiceClient
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


def create_ai_service_client() -> Optional[AIServiceClient]:
    """
    建立 AI 服務客戶端
    
    從環境變數讀取 AI 服務 URL，如果未設定則返回 None。
    
    Returns:
        Optional[AIServiceClient]: AI 服務客戶端，如果未設定則返回 None
    """
    ai_service_url = os.getenv("AI_SERVICE_URL")
    
    if not ai_service_url:
        logger.warning("AI_SERVICE_URL 環境變數未設定，AI 服務功能將不可用")
        return None
    
    # 讀取超時設定（預設 30 秒）
    timeout = int(os.getenv("AI_SERVICE_TIMEOUT", "30"))
    
    logger.info(
        f"建立 AI 服務客戶端：{ai_service_url}（超時：{timeout} 秒）",
        extra={"ai_service_url": ai_service_url, "timeout": timeout}
    )
    
    return AIServiceClient(base_url=ai_service_url, timeout=timeout)

