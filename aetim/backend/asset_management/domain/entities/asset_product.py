"""
資產產品實體

資產產品資訊（產品名稱、版本）。
"""

from typing import Optional
from dataclasses import dataclass
import uuid


@dataclass
class AssetProduct:
    """
    資產產品實體
    
    實體具有唯一識別碼，用於追蹤產品資訊。
    """
    
    id: str
    product_name: str
    product_version: Optional[str] = None
    product_type: Optional[str] = None  # OS 或 Application
    original_text: Optional[str] = None  # 原始文字（用於比對）
    
    def __post_init__(self):
        """驗證實體的有效性"""
        if not self.product_name or not self.product_name.strip():
            raise ValueError("產品名稱不能為空")
        
        # 如果沒有 ID，自動生成
        if not self.id:
            object.__setattr__(self, "id", str(uuid.uuid4()))
    
    def __eq__(self, other):
        """實體透過 ID 相等性比較"""
        if not isinstance(other, AssetProduct):
            return False
        return self.id == other.id
    
    def __hash__(self):
        """實體必須可雜湊"""
        return hash(self.id)
    
    def __repr__(self):
        return (
            f"AssetProduct(id='{self.id}', "
            f"product_name='{self.product_name}', "
            f"product_version='{self.product_version}')"
        )

