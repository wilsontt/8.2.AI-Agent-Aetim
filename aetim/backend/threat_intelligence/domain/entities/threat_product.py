"""
威脅產品實體

表示威脅影響的產品資訊。
"""

from dataclasses import dataclass
from typing import Optional
import uuid


@dataclass
class ThreatProduct:
    """
    威脅產品實體
    
    表示威脅影響的特定產品及其版本。
    """
    
    id: str
    product_name: str
    product_version: Optional[str] = None
    product_type: Optional[str] = None  # 例如：Operating System, Application, Framework
    original_text: Optional[str] = None  # 原始文字（用於追蹤來源）
    
    def __post_init__(self):
        """驗證實體的有效性"""
        if not self.product_name or not self.product_name.strip():
            raise ValueError("產品名稱不能為空")
        
        # 如果未提供 ID，自動生成
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def __str__(self) -> str:
        if self.product_version:
            return f"{self.product_name} {self.product_version}"
        return self.product_name

