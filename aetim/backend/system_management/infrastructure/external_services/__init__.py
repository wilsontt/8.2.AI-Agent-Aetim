"""
外部服務模組

提供與外部服務整合的功能。
"""

from .oauth2_service import (
    OAuth2Service,
    OAuth2Config,
    TokenInfo,
    UserInfo,
    TokenValidator,
)

__all__ = [
    "OAuth2Service",
    "OAuth2Config",
    "TokenInfo",
    "UserInfo",
    "TokenValidator",
]

