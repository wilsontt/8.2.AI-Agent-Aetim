"""
CVE 編號提取器

從文字內容中提取 CVE（Common Vulnerabilities and Exposures）編號。
符合 AC-009-1 要求：格式為 CVE-YYYY-NNNNN。
"""

import re
from typing import Optional, List, Set


class CVEExtractor:
    """
    CVE 編號提取器
    
    使用正則表達式從文字中提取 CVE 編號。
    支援各種格式變體（大小寫、空格等）。
    """
    
    # CVE 格式：CVE-YYYY-NNNNN
    # YYYY: 4 位數年份（1999-2099）
    # NNNNN: 4-7 位數序號
    CVE_PATTERN = r'CVE[-\s]?(\d{4})[-\s]?(\d{4,7})'
    
    # 年份範圍驗證（CVE 從 1999 年開始）
    MIN_YEAR = 1999
    MAX_YEAR = 2099
    
    def extract(self, text: str) -> Optional[str]:
        """
        提取單一 CVE 編號
        
        從文字中提取第一個符合格式的 CVE 編號。
        
        Args:
            text: 要提取的文字內容
        
        Returns:
            Optional[str]: CVE 編號（標準化格式，大寫），如果未找到則返回 None
        
        Examples:
            >>> extractor = CVEExtractor()
            >>> extractor.extract("This vulnerability is CVE-2024-12345")
            'CVE-2024-12345'
            >>> extractor.extract("No CVE here")
            None
        """
        if not text or not isinstance(text, str):
            return None
        
        matches = re.finditer(self.CVE_PATTERN, text, re.IGNORECASE)
        
        for match in matches:
            year_str = match.group(1)
            number_str = match.group(2)
            
            # 驗證年份範圍
            year = int(year_str)
            if self.MIN_YEAR <= year <= self.MAX_YEAR:
                # 標準化格式：CVE-YYYY-NNNNN（大寫）
                cve = f"CVE-{year_str}-{number_str}".upper()
                return cve
        
        return None
    
    def extract_all(self, text: str) -> List[str]:
        """
        提取所有 CVE 編號
        
        從文字中提取所有符合格式的 CVE 編號，並進行去重處理。
        
        Args:
            text: 要提取的文字內容
        
        Returns:
            List[str]: CVE 編號列表（標準化格式，大寫，已去重）
        
        Examples:
            >>> extractor = CVEExtractor()
            >>> extractor.extract_all("CVE-2024-12345 and CVE-2024-67890")
            ['CVE-2024-12345', 'CVE-2024-67890']
            >>> extractor.extract_all("CVE-2024-12345 and CVE-2024-12345")
            ['CVE-2024-12345']
        """
        if not text or not isinstance(text, str):
            return []
        
        cves: Set[str] = set()
        matches = re.finditer(self.CVE_PATTERN, text, re.IGNORECASE)
        
        for match in matches:
            year_str = match.group(1)
            number_str = match.group(2)
            
            # 驗證年份範圍
            year = int(year_str)
            if self.MIN_YEAR <= year <= self.MAX_YEAR:
                # 標準化格式：CVE-YYYY-NNNNN（大寫）
                cve = f"CVE-{year_str}-{number_str}".upper()
                cves.add(cve)
        
        # 轉換為列表並排序（按年份和序號）
        return sorted(list(cves))
    
    def is_valid_cve(self, cve: str) -> bool:
        """
        驗證 CVE 編號格式是否正確
        
        Args:
            cve: CVE 編號字串
        
        Returns:
            bool: 如果格式正確則返回 True，否則返回 False
        
        Examples:
            >>> extractor = CVEExtractor()
            >>> extractor.is_valid_cve("CVE-2024-12345")
            True
            >>> extractor.is_valid_cve("CVE-1999-1")
            False
            >>> extractor.is_valid_cve("INVALID")
            False
        """
        if not cve or not isinstance(cve, str):
            return False
        
        # 標準化格式檢查
        match = re.match(r'CVE-(\d{4})-(\d{4,7})', cve, re.IGNORECASE)
        if not match:
            return False
        
        year_str = match.group(1)
        number_str = match.group(2)
        
        # 驗證年份範圍
        year = int(year_str)
        if not (self.MIN_YEAR <= year <= self.MAX_YEAR):
            return False
        
        # 驗證序號長度（4-7 位數）
        if not (4 <= len(number_str) <= 7):
            return False
        
        return True

