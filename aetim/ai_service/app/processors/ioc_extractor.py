"""
IOC 提取器

從文字內容中提取 IOCs（Indicators of Compromise）。
符合 AC-009-4 要求：識別 IOC（入侵指標）。
"""

import re
from typing import List, Set, Dict, Optional
from ipaddress import ip_address, IPv4Address, IPv6Address, AddressValueError


class IOCExtractor:
    """
    IOC 提取器
    
    從文字中提取 IP 位址、網域、檔案雜湊值等 IOC。
    """
    
    # IP 位址正則表達式（IPv4）
    IPV4_PATTERN = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    
    # IPv6 正則表達式（簡化版）
    IPV6_PATTERN = r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
    
    # 網域正則表達式
    DOMAIN_PATTERN = r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b'
    
    # 檔案雜湊值正則表達式
    # MD5: 32 個十六進位字元
    # SHA1: 40 個十六進位字元
    # SHA256: 64 個十六進位字元
    HASH_PATTERN = r'\b[a-fA-F0-9]{32,64}\b'
    
    # 常見的誤判網域（需要過濾）
    EXCLUDED_DOMAINS = [
        "example.com",
        "localhost",
        "127.0.0.1",
    ]
    
    # 常見的誤判雜湊值（需要過濾）
    EXCLUDED_HASHES = [
        "00000000000000000000000000000000",  # 全零 MD5
        "ffffffffffffffffffffffffffffffff",  # 全 F MD5
    ]
    
    def extract(self, text: str) -> Dict[str, List[str]]:
        """
        提取 IOCs
        
        從文字中提取所有類型的 IOC（IP、網域、雜湊值）。
        
        Args:
            text: 要提取的文字內容
        
        Returns:
            Dict[str, List[str]]: IOC 字典，包含 'ips'、'domains'、'hashes' 鍵
        
        Examples:
            >>> extractor = IOCExtractor()
            >>> extractor.extract("IP: 192.168.1.1, Domain: example.com")
            {'ips': ['192.168.1.1'], 'domains': ['example.com'], 'hashes': []}
        """
        if not text or not isinstance(text, str):
            return {"ips": [], "domains": [], "hashes": []}
        
        return {
            "ips": self._extract_ips(text),
            "domains": self._extract_domains(text),
            "hashes": self._extract_hashes(text),
        }
    
    def _extract_ips(self, text: str) -> List[str]:
        """
        提取 IP 位址
        
        從文字中提取 IPv4 和 IPv6 位址，並驗證格式正確性。
        
        Args:
            text: 文字內容
        
        Returns:
            List[str]: IP 位址列表（已去重、已驗證）
        """
        ips: Set[str] = set()
        
        # 提取 IPv4
        ipv4_matches = re.findall(self.IPV4_PATTERN, text)
        for ip_str in ipv4_matches:
            if self._is_valid_ip(ip_str):
                ips.add(ip_str)
        
        # 提取 IPv6（簡化處理）
        ipv6_matches = re.findall(self.IPV6_PATTERN, text)
        for ip_str in ipv6_matches:
            if self._is_valid_ip(ip_str):
                ips.add(ip_str)
        
        return sorted(list(ips))
    
    def _extract_domains(self, text: str) -> List[str]:
        """
        提取網域
        
        從文字中提取網域名稱，並過濾常見的誤判。
        
        Args:
            text: 文字內容
        
        Returns:
            List[str]: 網域列表（已去重、已過濾）
        """
        matches = re.findall(self.DOMAIN_PATTERN, text)
        domains: Set[str] = set()
        
        for domain in matches:
            domain_lower = domain.lower()
            
            # 過濾常見的誤判
            if self._should_exclude_domain(domain_lower):
                continue
            
            # 過濾 email 地址（如果包含 @ 符號）
            if '@' in domain:
                continue
            
            # 過濾過短的網域（可能是誤判）
            if len(domain) < 4:
                continue
            
            domains.add(domain_lower)
        
        return sorted(list(domains))
    
    def _extract_hashes(self, text: str) -> List[str]:
        """
        提取檔案雜湊值
        
        從文字中提取 MD5、SHA1、SHA256 雜湊值。
        
        Args:
            text: 文字內容
        
        Returns:
            List[str]: 雜湊值列表（已去重、已驗證）
        """
        matches = re.findall(self.HASH_PATTERN, text)
        hashes: Set[str] = set()
        
        for hash_str in matches:
            hash_lower = hash_str.lower()
            
            # 過濾常見的誤判
            if hash_lower in self.EXCLUDED_HASHES:
                continue
            
            # 只保留符合標準長度的雜湊值
            # MD5: 32, SHA1: 40, SHA256: 64
            if len(hash_str) in [32, 40, 64]:
                hashes.add(hash_lower)
        
        return sorted(list(hashes))
    
    def _is_valid_ip(self, ip_str: str) -> bool:
        """
        驗證 IP 位址格式是否有效
        
        Args:
            ip_str: IP 位址字串
        
        Returns:
            bool: 如果格式有效則返回 True
        """
        if not ip_str:
            return False
        
        try:
            ip_address(ip_str)
            return True
        except (AddressValueError, ValueError):
            return False
    
    def _should_exclude_domain(self, domain: str) -> bool:
        """
        判斷是否應該排除網域（常見的誤判）
        
        Args:
            domain: 網域字串
        
        Returns:
            bool: 如果應該排除則返回 True
        """
        if not domain:
            return True
        
        domain_lower = domain.lower()
        
        # 檢查是否在排除列表中
        if domain_lower in self.EXCLUDED_DOMAINS:
            return True
        
        # 排除常見的本地網域
        if domain_lower.startswith("localhost") or domain_lower.startswith("127."):
            return True
        
        # 排除常見的測試網域
        if "test" in domain_lower and "example" in domain_lower:
            return True
        
        return False

