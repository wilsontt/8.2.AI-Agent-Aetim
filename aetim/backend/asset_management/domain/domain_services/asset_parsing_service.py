"""
資產解析服務

負責從文字描述中解析產品名稱、版本和作業系統資訊。
"""

import re
from typing import List, Optional
from ..entities.asset_product import AssetProduct


class AssetParsingService:
    """
    資產解析服務
    
    解析產品名稱與版本、作業系統資訊。
    """
    
    # 常見產品名稱模式
    PRODUCT_PATTERNS = [
        # 標準格式：產品名稱 版本號
        (r"^([A-Za-z][A-Za-z0-9\s\-\.]+?)\s+(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)", "standard"),
        # 包含版本資訊：產品名稱 (版本資訊)
        (r"^([A-Za-z][A-Za-z0-9\s\-\.]+?)\s*\(([^)]+)\)", "parentheses"),
        # 包含版本資訊：產品名稱, 版本號
        (r"^([A-Za-z][A-Za-z0-9\s\-\.]+?),\s*(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)", "comma"),
        # 包含版本資訊：產品名稱 - 版本號
        (r"^([A-Za-z][A-Za-z0-9\s\-\.]+?)\s*-\s*(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)", "dash"),
        # 包含版本資訊：產品名稱 v版本號
        (r"^([A-Za-z][A-Za-z0-9\s\-\.]+?)\s+v(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)", "version_prefix"),
    ]
    
    # 常見作業系統模式
    OS_PATTERNS = [
        # Windows Server 版本
        (r"Windows\s+Server\s+(\d{4})\s+(.+?)(?:\s+\d+)?$", "windows_server"),
        # Windows 版本
        (r"Windows\s+(\d+\.\d+|\d{2})", "windows"),
        # Linux 發行版
        (r"(Ubuntu|Debian|CentOS|Red\s+Hat|Fedora|SUSE)\s+(\d+\.\d+)", "linux"),
        # VMware ESXi
        (r"VMware\s+ESXi\s+(\d+\.\d+(?:\.\d+)?)", "vmware_esxi"),
    ]
    
    def parse_products(self, running_applications: str) -> List[AssetProduct]:
        """
        從「運行的應用程式」欄位解析產品名稱與版本
        
        解析規則：
        1. 標準格式：產品名稱 版本號（例如：Microsoft SQL Server 2017）
        2. 包含版本資訊：產品名稱 (版本資訊)（例如：VMware ESXi, 7.0.4）
        3. 自行開發系統：保留完整描述（例如：自行開發 EEP(delphi7) 文件倉儲管理系統 v3.0）
        
        Args:
            running_applications: 運行的應用程式文字描述
        
        Returns:
            List[AssetProduct]: 產品清單
        """
        if not running_applications or not running_applications.strip():
            return []
        
        products = []
        
        # 分割多個應用程式（以換行、分號或逗號分隔）
        app_list = re.split(r"[\n;,]|,\s*", running_applications)
        
        for app_text in app_list:
            app_text = app_text.strip()
            if not app_text:
                continue
            
            # 檢查是否為自行開發系統
            if "自行開發" in app_text or "自開發" in app_text:
                # 保留完整描述
                product = AssetProduct(
                    id="",  # 自動生成
                    product_name=app_text,
                    product_version=None,
                    product_type="Application",
                    original_text=app_text,
                )
                products.append(product)
                continue
            
            # 嘗試匹配各種產品格式
            matched = False
            for pattern, pattern_type in self.PRODUCT_PATTERNS:
                match = re.match(pattern, app_text, re.IGNORECASE)
                if match:
                    product_name = match.group(1).strip()
                    product_version = match.group(2).strip() if match.lastindex >= 2 else None
                    
                    # 清理產品名稱（移除多餘空格）
                    product_name = re.sub(r"\s+", " ", product_name)
                    
                    product = AssetProduct(
                        id="",  # 自動生成
                        product_name=product_name,
                        product_version=product_version,
                        product_type="Application",
                        original_text=app_text,
                    )
                    products.append(product)
                    matched = True
                    break
            
            # 如果沒有匹配到任何模式，將整個文字作為產品名稱
            if not matched:
                product = AssetProduct(
                    id="",  # 自動生成
                    product_name=app_text,
                    product_version=None,
                    product_type="Application",
                    original_text=app_text,
                )
                products.append(product)
        
        return products
    
    def parse_os_info(self, operating_system: str) -> dict:
        """
        從「作業系統」欄位解析 OS 資訊
        
        Args:
            operating_system: 作業系統文字描述
        
        Returns:
            dict: 包含 os_name 和 os_version 的字典
        """
        if not operating_system or not operating_system.strip():
            return {"os_name": None, "os_version": None}
        
        # 嘗試匹配各種作業系統格式
        for pattern, pattern_type in self.OS_PATTERNS:
            match = re.search(pattern, operating_system, re.IGNORECASE)
            if match:
                if pattern_type == "windows_server":
                    os_name = f"Windows Server {match.group(1)}"
                    os_version = match.group(2).strip()
                elif pattern_type == "windows":
                    os_name = "Windows"
                    os_version = match.group(1)
                elif pattern_type == "linux":
                    os_name = match.group(1)
                    os_version = match.group(2)
                elif pattern_type == "vmware_esxi":
                    os_name = "VMware ESXi"
                    os_version = match.group(1)
                else:
                    os_name = operating_system
                    os_version = None
                
                return {
                    "os_name": os_name,
                    "os_version": os_version,
                    "original_text": operating_system,
                }
        
        # 如果沒有匹配到任何模式，返回原始文字
        return {
            "os_name": operating_system,
            "os_version": None,
            "original_text": operating_system,
        }

