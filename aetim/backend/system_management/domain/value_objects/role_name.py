"""
角色名稱值物件

定義系統支援的角色名稱。
符合 AC-023-2。
"""

from enum import Enum


class RoleName(str, Enum):
    """
    角色名稱枚舉
    
    符合 AC-023-2：定義所有角色（CISO、IT Admin、Analyst、Viewer）
    """
    
    CISO = "CISO"
    IT_ADMIN = "IT_Admin"
    ANALYST = "Analyst"
    VIEWER = "Viewer"
    
    def __str__(self) -> str:
        return self.value

