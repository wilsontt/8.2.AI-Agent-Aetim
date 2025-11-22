"""
處理器

提供各種威脅資訊提取器（CVE、產品、TTP、IOC）。
"""

from .cve_extractor import CVEExtractor

__all__ = [
    "CVEExtractor",
]
