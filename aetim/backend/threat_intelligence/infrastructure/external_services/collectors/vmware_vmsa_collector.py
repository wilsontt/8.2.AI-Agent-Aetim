"""
VMware VMSA 收集器

從 VMware Security Advisories (VMSA) 收集威脅情資。
"""

import httpx
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from xml.etree import ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from ..collector_interface import ICollector
from ....domain.aggregates.threat import Threat
from ....domain.aggregates.threat_feed import ThreatFeed
from ....domain.value_objects.threat_severity import ThreatSeverity
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class VMwareVMSACollector(ICollector):
    """
    VMware VMSA 收集器
    
    從 VMware Security Advisories (VMSA) 收集威脅情資。
    
    資料來源：
    - RSS Feed: https://www.vmware.com/security/advisories.xml
    - HTML 頁面: https://www.vmware.com/security/advisories.html
    """
    
    # VMware VMSA RSS Feed URL
    VMSA_RSS_URL = "https://www.vmware.com/security/advisories.xml"
    
    # VMware VMSA HTML 頁面 URL
    VMSA_HTML_URL = "https://www.vmware.com/security/advisories.html"
    
    # 請求超時時間（秒）
    REQUEST_TIMEOUT = 30
    
    def __init__(self, ai_service_client: Optional[Any] = None):
        """
        初始化 VMware VMSA 收集器
        
        Args:
            ai_service_client: AI 服務客戶端（可選，用於處理非結構化內容）
        """
        self.ai_service_client = ai_service_client
    
    async def collect(self, feed: ThreatFeed) -> List[Threat]:
        """
        收集 VMware VMSA 威脅情資
        
        Args:
            feed: 威脅情資來源聚合根
        
        Returns:
            List[Threat]: 收集到的威脅列表
        
        Raises:
            Exception: 當收集失敗時
        """
        logger.info(
            f"開始收集 VMware VMSA 威脅情資",
            extra={"feed_id": feed.id, "feed_name": feed.name}
        )
        
        try:
            # 1. 嘗試從 RSS Feed 收集
            threats = await self._collect_from_rss(feed)
            
            # 如果 RSS Feed 沒有資料，嘗試從 HTML 頁面收集
            if not threats:
                logger.info(
                    "RSS Feed 沒有資料，嘗試從 HTML 頁面收集",
                    extra={"feed_id": feed.id}
                )
                threats = await self._collect_from_html(feed)
            
            logger.info(
                f"成功收集 {len(threats)} 個威脅",
                extra={"feed_id": feed.id, "threats_count": len(threats)}
            )
            
            return threats
            
        except Exception as e:
            error_msg = f"收集 VMware VMSA 威脅情資時發生未預期錯誤：{str(e)}"
            logger.error(error_msg, extra={"feed_id": feed.id, "error": str(e)})
            raise
    
    async def _collect_from_rss(self, feed: ThreatFeed) -> List[Threat]:
        """
        從 RSS Feed 收集威脅情資
        
        Args:
            feed: 威脅情資來源聚合根
        
        Returns:
            List[Threat]: 收集到的威脅列表
        """
        try:
            async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                response = await client.get(self.VMSA_RSS_URL)
                response.raise_for_status()
                xml_content = response.text
            
            # 解析 XML
            root = ET.fromstring(xml_content)
            
            # 提取所有 item 元素
            items = root.findall(".//item")
            
            threats = []
            for item in items:
                try:
                    threat = await self._parse_rss_item(item, feed)
                    if threat:
                        threats.append(threat)
                except Exception as e:
                    logger.warning(
                        f"解析 RSS item 失敗：{str(e)}",
                        extra={"feed_id": feed.id, "error": str(e)}
                    )
                    continue
            
            return threats
            
        except httpx.HTTPError as e:
            logger.warning(
                f"從 RSS Feed 收集失敗：{str(e)}",
                extra={"feed_id": feed.id, "error": str(e)}
            )
            return []
        except ET.ParseError as e:
            logger.warning(
                f"解析 RSS Feed XML 失敗：{str(e)}",
                extra={"feed_id": feed.id, "error": str(e)}
            )
            return []
    
    async def _collect_from_html(self, feed: ThreatFeed) -> List[Threat]:
        """
        從 HTML 頁面收集威脅情資
        
        Args:
            feed: 威脅情資來源聚合根
        
        Returns:
            List[Threat]: 收集到的威脅列表
        """
        try:
            async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                response = await client.get(self.VMSA_HTML_URL)
                response.raise_for_status()
                html_content = response.text
            
            # 使用正則表達式提取公告連結
            # VMware VMSA HTML 頁面通常包含指向個別公告的連結
            # 格式：<a href="/security/advisories/VMSA-YYYY-XXXX.html">VMSA-YYYY-XXXX</a>
            vmsa_pattern = r'href=["\'](/security/advisories/VMSA-\d{4}-\d{4,5}\.html)["\']'
            matches = re.findall(vmsa_pattern, html_content)
            
            threats = []
            for match in matches:
                try:
                    # 建立完整 URL
                    advisory_url = urljoin(self.VMSA_HTML_URL, match)
                    
                    # 解析個別公告頁面
                    threat = await self._parse_advisory_page(advisory_url, feed)
                    if threat:
                        threats.append(threat)
                except Exception as e:
                    logger.warning(
                        f"解析公告頁面失敗：{str(e)}",
                        extra={"feed_id": feed.id, "url": match, "error": str(e)}
                    )
                    continue
            
            return threats
            
        except httpx.HTTPError as e:
            logger.warning(
                f"從 HTML 頁面收集失敗：{str(e)}",
                extra={"feed_id": feed.id, "error": str(e)}
            )
            return []
    
    async def _parse_rss_item(self, item: ET.Element, feed: ThreatFeed) -> Threat | None:
        """
        解析 RSS item 元素
        
        Args:
            item: RSS item 元素
            feed: 威脅情資來源聚合根
        
        Returns:
            Threat: 威脅聚合根，如果解析失敗則返回 None
        """
        try:
            # 提取標題
            title_elem = item.find("title")
            title = title_elem.text if title_elem is not None else ""
            
            # 提取描述
            description_elem = item.find("description")
            description = description_elem.text if description_elem is not None else ""
            
            # 提取連結
            link_elem = item.find("link")
            link = link_elem.text if link_elem is not None else ""
            
            # 提取發布日期
            pub_date_elem = item.find("pubDate")
            published_date = None
            if pub_date_elem is not None and pub_date_elem.text:
                try:
                    # RSS 日期格式：Wed, 15 Jan 2024 10:00:00 GMT
                    from email.utils import parsedate_to_datetime
                    published_date = parsedate_to_datetime(pub_date_elem.text)
                except (ValueError, TypeError):
                    pass
            
            # 從標題或描述中提取 VMSA 編號
            vmsa_match = re.search(r'VMSA-(\d{4})-(\d{4,5})', title)
            vmsa_id = vmsa_match.group(0) if vmsa_match else None
            
            # 使用 AI 服務處理非結構化內容（AC-008-7）
            if self.ai_service_client:
                try:
                    ai_text = f"{title}\n\n{description}"
                    ai_result = await self.ai_service_client.extract_threat_info(ai_text)
                    
                    # 提取 CVE 編號
                    cve_ids = ai_result.get("cve", [])
                    
                    # 提取產品資訊
                    products = ai_result.get("products", [])
                    
                    # 提取 TTPs
                    ttps = ai_result.get("ttps", [])
                    
                    # 提取 IOCs
                    iocs = ai_result.get("iocs", {})
                    
                except Exception as e:
                    logger.warning(
                        f"AI 服務處理失敗：{str(e)}",
                        extra={"feed_id": feed.id, "vmsa_id": vmsa_id, "error": str(e)}
                    )
                    cve_ids = []
                    products = []
                    ttps = []
                    iocs = {}
            else:
                # 如果沒有 AI 服務，使用正則表達式提取 CVE
                cve_ids = re.findall(r'CVE-\d{4}-\d{4,7}', f"{title} {description}")
                products = []
                ttps = []
                iocs = {}
            
            # 如果沒有找到 CVE，跳過（因為無法建立有效的威脅）
            if not cve_ids:
                logger.warning(
                    f"未找到 CVE 編號，跳過此公告",
                    extra={"feed_id": feed.id, "vmsa_id": vmsa_id, "title": title}
                )
                return None
            
            # 為每個 CVE 建立一個威脅
            threats = []
            for cve_id in cve_ids:
                threat = Threat.create(
                    threat_feed_id=feed.id,
                    title=f"{vmsa_id}: {title}" if vmsa_id else title,
                    description=description,
                    cve_id=cve_id,
                    source_url=link if link else None,
                    published_date=published_date,
                    collected_at=datetime.utcnow(),
                )
                
                # 新增產品資訊
                for product_info in products:
                    threat.add_product(
                        product_name=product_info.get("name", ""),
                        product_version=product_info.get("version"),
                    )
                
                # 新增 TTPs
                for ttp in ttps:
                    threat.add_ttp(ttp)
                
                # 新增 IOCs
                for ioc_type, values in iocs.items():
                    for value in values:
                        threat.add_ioc(ioc_type, value)
                
                # 儲存原始資料
                threat.raw_data = json.dumps({
                    "vmsa_id": vmsa_id,
                    "title": title,
                    "description": description,
                    "link": link,
                }, ensure_ascii=False)
                
                threats.append(threat)
            
            # 如果只有一個 CVE，直接返回；否則返回第一個（其他可以作為額外的威脅）
            return threats[0] if threats else None
            
        except Exception as e:
            logger.error(
                f"解析 RSS item 失敗：{str(e)}",
                extra={"feed_id": feed.id, "error": str(e)}
            )
            return None
    
    async def _parse_advisory_page(self, url: str, feed: ThreatFeed) -> Threat | None:
        """
        解析個別公告頁面
        
        Args:
            url: 公告頁面 URL
            feed: 威脅情資來源聚合根
        
        Returns:
            Threat: 威脅聚合根，如果解析失敗則返回 None
        """
        try:
            async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                response = await client.get(url)
                response.raise_for_status()
                html_content = response.text
            
            # 提取 VMSA 編號
            vmsa_match = re.search(r'VMSA-(\d{4})-(\d{4,5})', html_content)
            vmsa_id = vmsa_match.group(0) if vmsa_match else None
            
            # 提取標題（通常在 <h1> 或 <title> 標籤中）
            title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.DOTALL)
            title = title_match.group(1).strip() if title_match else ""
            
            # 提取描述（通常在 <p> 或 <div> 標籤中）
            # 這裡使用簡單的正則表達式，實際可能需要更複雜的 HTML 解析
            description_match = re.search(
                r'<div[^>]*class=["\']description["\'][^>]*>(.*?)</div>',
                html_content,
                re.DOTALL
            )
            description = description_match.group(1).strip() if description_match else ""
            
            # 如果沒有找到描述，使用標題
            if not description:
                description = title
            
            # 使用 AI 服務處理非結構化內容（AC-008-7）
            if self.ai_service_client:
                try:
                    ai_text = f"{title}\n\n{description}\n\n{html_content[:5000]}"  # 限制長度
                    ai_result = await self.ai_service_client.extract_threat_info(ai_text)
                    
                    cve_ids = ai_result.get("cve", [])
                    products = ai_result.get("products", [])
                    ttps = ai_result.get("ttps", [])
                    iocs = ai_result.get("iocs", {})
                    
                except Exception as e:
                    logger.warning(
                        f"AI 服務處理失敗：{str(e)}",
                        extra={"feed_id": feed.id, "url": url, "error": str(e)}
                    )
                    cve_ids = re.findall(r'CVE-\d{4}-\d{4,7}', html_content)
                    products = []
                    ttps = []
                    iocs = {}
            else:
                # 如果沒有 AI 服務，使用正則表達式提取 CVE
                cve_ids = re.findall(r'CVE-\d{4}-\d{4,7}', html_content)
                products = []
                ttps = []
                iocs = {}
            
            # 如果沒有找到 CVE，跳過
            if not cve_ids:
                return None
            
            # 為每個 CVE 建立一個威脅（這裡簡化，只返回第一個）
            cve_id = cve_ids[0]
            
            threat = Threat.create(
                threat_feed_id=feed.id,
                title=f"{vmsa_id}: {title}" if vmsa_id else title,
                description=description,
                cve_id=cve_id,
                source_url=url,
                published_date=None,  # HTML 頁面可能沒有明確的發布日期
                collected_at=datetime.utcnow(),
            )
            
            # 新增產品資訊
            for product_info in products:
                threat.add_product(
                    product_name=product_info.get("name", ""),
                    product_version=product_info.get("version"),
                )
            
            # 新增 TTPs
            for ttp in ttps:
                threat.add_ttp(ttp)
            
            # 新增 IOCs
            for ioc_type, values in iocs.items():
                for value in values:
                    threat.add_ioc(ioc_type, value)
            
            # 儲存原始資料
            threat.raw_data = json.dumps({
                "vmsa_id": vmsa_id,
                "title": title,
                "description": description,
                "url": url,
            }, ensure_ascii=False)
            
            return threat
            
        except Exception as e:
            logger.error(
                f"解析公告頁面失敗：{str(e)}",
                extra={"feed_id": feed.id, "url": url, "error": str(e)}
            )
            return None
    
    def get_collector_type(self) -> str:
        """
        取得收集器類型
        
        Returns:
            str: 收集器類型
        """
        return "VMWARE_VMSA"

