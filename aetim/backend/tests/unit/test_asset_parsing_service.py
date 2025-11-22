"""
資產解析服務單元測試

測試產品名稱與版本解析、作業系統資訊解析。
"""

import pytest
from asset_management.domain.domain_services.asset_parsing_service import AssetParsingService


@pytest.mark.unit
class TestAssetParsingService:
    """測試資產解析服務"""
    
    def test_parse_products_standard_format(self):
        """測試標準格式：產品名稱 版本號"""
        service = AssetParsingService()
        
        products = service.parse_products("Microsoft SQL Server 2017")
        assert len(products) == 1
        assert products[0].product_name == "Microsoft SQL Server"
        assert products[0].product_version == "2017"
        assert products[0].product_type == "Application"
    
    def test_parse_products_with_parentheses(self):
        """測試包含版本資訊：產品名稱 (版本資訊)"""
        service = AssetParsingService()
        
        products = service.parse_products("VMware ESXi (7.0.4)")
        assert len(products) == 1
        assert "VMware ESXi" in products[0].product_name
        assert products[0].product_version == "7.0.4"
    
    def test_parse_products_with_comma(self):
        """測試包含版本資訊：產品名稱, 版本號"""
        service = AssetParsingService()
        
        products = service.parse_products("VMware ESXi, 7.0.4")
        assert len(products) == 1
        assert "VMware ESXi" in products[0].product_name
        assert products[0].product_version == "7.0.4"
    
    def test_parse_products_custom_developed(self):
        """測試自行開發系統"""
        service = AssetParsingService()
        
        products = service.parse_products("自行開發 EEP(delphi7) 文件倉儲管理系統 v3.0")
        assert len(products) == 1
        assert "自行開發" in products[0].product_name
        assert products[0].product_version is None  # 自行開發系統保留完整描述
    
    def test_parse_products_multiple_apps(self):
        """測試多個應用程式（以換行分隔）"""
        service = AssetParsingService()
        
        products = service.parse_products("nginx 1.18.0\napache 2.4.0")
        assert len(products) == 2
        assert products[0].product_name == "nginx"
        assert products[0].product_version == "1.18.0"
        assert products[1].product_name == "apache"
        assert products[1].product_version == "2.4.0"
    
    def test_parse_products_empty_string(self):
        """測試空字串"""
        service = AssetParsingService()
        
        products = service.parse_products("")
        assert len(products) == 0
    
    def test_parse_os_info_windows_server(self):
        """測試 Windows Server"""
        service = AssetParsingService()
        
        os_info = service.parse_os_info("Windows Server 2016 Standard 1607")
        assert os_info["os_name"] == "Windows Server 2016"
        assert os_info["os_version"] == "Standard 1607"
    
    def test_parse_os_info_windows(self):
        """測試 Windows"""
        service = AssetParsingService()
        
        os_info = service.parse_os_info("Windows 10")
        assert os_info["os_name"] == "Windows"
        assert os_info["os_version"] == "10"
    
    def test_parse_os_info_linux(self):
        """測試 Linux"""
        service = AssetParsingService()
        
        os_info = service.parse_os_info("Ubuntu 20.04")
        assert os_info["os_name"] == "Ubuntu"
        assert os_info["os_version"] == "20.04"
    
    def test_parse_os_info_vmware_esxi(self):
        """測試 VMware ESXi"""
        service = AssetParsingService()
        
        os_info = service.parse_os_info("VMware ESXi 7.0.3")
        assert os_info["os_name"] == "VMware ESXi"
        assert os_info["os_version"] == "7.0.3"
    
    def test_parse_os_info_unknown(self):
        """測試未知作業系統"""
        service = AssetParsingService()
        
        os_info = service.parse_os_info("Unknown OS 1.0")
        assert os_info["os_name"] == "Unknown OS 1.0"
        assert os_info["os_version"] is None

