"""
TWCERT 收集器

從台灣電腦網路危機處理暨協調中心 (TWCERT/CC) 收集威脅情資。
"""

import httpx
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from xml.etree import ElementTree as ET
from urllib.parse import urljoin

from ..collector_interface import ICollector
from ....domain.aggregates.threat import Threat
from ....domain.aggregates.threat_feed import ThreatFeed
from ....domain.value_objects.threat_severity import ThreatSeverity
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class TWCERTCollector(ICollector):
    """
    TWCERT 收集器
    
    從台灣電腦網路危機處理暨協調中心 (TWCERT/CC) 收集威脅情資。
    
    資料來源：
    - TWCERT/CC 官方網站
    - RSS Feed（如果有）
    """
    
    # TWCERT/CC 官方網站 URL
    TWCERT_BASE_URL = "https://www.twcert.org.tw"
    
    # TWCERT/CC 資安情資頁面 URL
    TWCERT_ADVISORY_URL = "https://www.twcert.org.tw/twcert/advisory"
    
    # 請求超時時間（秒）
    REQUEST_TIMEOUT = 30
    
    def __init__(self, ai_service_client: Optional[Any] = None):
        """
        初始化 TWCERT 收集器
        
        Args:
            ai_service_client: AI 服務客戶端（必填，用於處理中文非結構化內容）
        """
        if not ai_service_client:
            logger.warning(
                "TWCERT 收集器未提供 AI 服務客戶端，將無法處理中文非結構化內容"
            )
        self.ai_service_client = ai_service_client
    
    async def collect(self, feed: ThreatFeed) -> List[Threat]:
        """
        收集 TWCERT 威脅情資
        
        Args:
            feed: 威脅情資來源聚合根
        
        Returns:
            List[Threat]: 收集到的威脅列表
        
        Raises:
            Exception: 當收集失敗時
        """
        logger.info(
            f"開始收集 TWCERT 威脅情資",
            extra={"feed_id": feed.id, "feed_name": feed.name}
        )
        
        if not self.ai_service_client:
            error_msg = "TWCERT 收集器需要 AI 服務客戶端來處理中文非結構化內容"
            logger.error(error_msg, extra={"feed_id": feed.id})
            raise ValueError(error_msg)
        
        try:
            # 1. 從 TWCERT/CC 網站收集通報
            advisories = await self._fetch_advisories()
            
            if not advisories:
                logger.warning(
                    "TWCERT 網站返回空的通報列表",
                    extra={"feed_id": feed.id}
                )
                return []
            
            logger.info(
                f"從 TWCERT 網站取得 {len(advisories)} 個通報",
                extra={"feed_id": feed.id, "count": len(advisories)}
            )
            
            # 2. 解析每個通報並轉換為 Threat
            all_threats = []
            for advisory in advisories:
                try:
                    threats = await self._parse_advisory(advisory, feed)
                    all_threats.extend(threats)
                except Exception as e:
                    logger.warning(
                        f"解析通報失敗：{str(e)}",
                        extra={
                            "feed_id": feed.id,
                            "advisory_url": advisory.get("url"),
                            "error": str(e),
                        }
                    )
                    continue
            
            logger.info(
                f"成功解析 {len(all_threats)} 個威脅",
                extra={"feed_id": feed.id, "threats_count": len(all_threats)}
            )
            
            return all_threats
            
        except httpx.HTTPError as e:
            error_msg = f"TWCERT 網站請求失敗：{str(e)}"
            logger.error(error_msg, extra={"feed_id": feed.id, "error": str(e)})
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"收集 TWCERT 威脅情資時發生未預期錯誤：{str(e)}"
            logger.error(error_msg, extra={"feed_id": feed.id, "error": str(e)})
            raise
    
    async def _fetch_advisories(self) -> List[Dict[str, Any]]:
        """
        取得通報列表
        
        Returns:
            List[Dict]: 通報列表，每個通報包含 url, title, date 等資訊
        """
        try:
            async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                response = await client.get(self.TWCERT_ADVISORY_URL)
                response.raise_for_status()
                html_content = response.text
            
            # 使用正則表達式提取通報連結
            # TWCERT/CC 網站結構可能因更新而變化，這裡使用簡單的正則表達式
            # 實際可能需要更複雜的 HTML 解析
            
            # 提取通報連結（格式可能為：<a href="/twcert/advisory/TA-XXXX-XXXX">標題</a>）
            advisory_pattern = r'<a[^>]*href=["\'](/twcert/advisory/[^"\']+)["\'][^>]*>([^<]+)</a>'
            matches = re.findall(advisory_pattern, html_content)
            
            advisories = []
            for match in matches:
                url_path, title = match
                full_url = urljoin(self.TWCERT_BASE_URL, url_path)
                
                # 提取日期（如果有的話）
                date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', html_content)
                date_str = date_match.group(1) if date_match else None
                
                advisories.append({
                    "url": full_url,
                    "title": title.strip(),
                    "date": date_str,
                })
            
            return advisories
            
        except Exception as e:
            logger.error(
                f"取得通報列表失敗：{str(e)}",
                extra={"error": str(e)}
            )
            return []
    
    async def _parse_advisory(
        self,
        advisory: Dict[str, Any],
        feed: ThreatFeed,
    ) -> List[Threat]:
        """
        解析單一通報並轉換為 Threat 聚合根
        
        Args:
            advisory: 通報資訊字典
            feed: 威脅情資來源聚合根
        
        Returns:
            List[Threat]: 威脅列表（一個通報可能包含多個 CVE）
        """
        try:
            url = advisory.get("url")
            if not url:
                return []
            
            # 1. 取得通報頁面內容
            async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                response = await client.get(url)
                response.raise_for_status()
                html_content = response.text
            
            # 2. 提取標題和內容
            title = advisory.get("title", "")
            
            # 提取內容（通常在 <div class="content"> 或類似的標籤中）
            content_match = re.search(
                r'<div[^>]*class=["\']content["\'][^>]*>(.*?)</div>',
                html_content,
                re.DOTALL
            )
            content = content_match.group(1) if content_match else html_content
            
            # 移除 HTML 標籤（簡單處理）
            content_text = re.sub(r'<[^>]+>', ' ', content)
            content_text = re.sub(r'\s+', ' ', content_text).strip()
            
            # 3. 提取發布日期
            published_date = None
            date_str = advisory.get("date")
            if date_str:
                try:
                    # 嘗試解析日期格式：YYYY-MM-DD 或 YYYY/MM/DD
                    date_str = date_str.replace("/", "-")
                    published_date = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    pass
            
            # 4. 使用 AI 服務處理非結構化中文內容（AC-008-7）
            ai_text = f"{title}\n\n{content_text}"
            
            try:
                ai_result = await self.ai_service_client.extract_threat_info(ai_text)
                
                # 提取 CVE 編號
                cve_ids = ai_result.get("cve", [])
                
                # 提取產品資訊
                products = ai_result.get("products", [])
                
                # 提取 TTPs
                ttps = ai_result.get("ttps", [])
                
                # 提取 IOCs
                iocs = ai_result.get("iocs", {})
                
                logger.debug(
                    f"AI 服務處理 TWCERT 通報完成",
                    extra={
                        "url": url,
                        "cve_count": len(cve_ids),
                        "product_count": len(products),
                        "ttp_count": len(ttps),
                        "confidence": ai_result.get("confidence", 0.0),
                    }
                )
                
            except Exception as e:
                logger.warning(
                    f"AI 服務處理失敗：{str(e)}",
                    extra={"url": url, "error": str(e)}
                )
                # 如果 AI 服務失敗，嘗試使用正則表達式提取 CVE
                cve_ids = re.findall(r'CVE-\d{4}-\d{4,7}', ai_text)
                products = []
                ttps = []
                iocs = {}
            
            # 5. 如果沒有找到 CVE，建立一個沒有 CVE 的威脅（使用標題作為識別）
            if not cve_ids:
                logger.warning(
                    f"未找到 CVE 編號，使用標題建立威脅",
                    extra={"url": url, "title": title}
                )
                # 為沒有 CVE 的通報建立一個威脅
                threat = Threat.create(
                    threat_feed_id=feed.id,
                    title=title,
                    description=content_text[:1000],  # 限制描述長度
                    cve_id=None,
                    source_url=url,
                    published_date=published_date,
                    collected_at=datetime.utcnow(),
                )
                
                # 新增產品資訊、TTPs、IOCs
                for product_info in products:
                    threat.add_product(
                        product_name=product_info.get("name", ""),
                        product_version=product_info.get("version"),
                    )
                
                for ttp in ttps:
                    threat.add_ttp(ttp)
                
                for ioc_type, values in iocs.items():
                    for value in values:
                        threat.add_ioc(ioc_type, value)
                
                # 儲存原始資料
                threat.raw_data = json.dumps({
                    "title": title,
                    "content": content_text,
                    "url": url,
                }, ensure_ascii=False)
                
                return [threat]
            
            # 6. 為每個 CVE 建立一個威脅
            threats = []
            for cve_id in cve_ids:
                threat = Threat.create(
                    threat_feed_id=feed.id,
                    title=f"{cve_id}: {title}",
                    description=content_text[:1000],  # 限制描述長度
                    cve_id=cve_id,
                    source_url=url,
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
                    "title": title,
                    "content": content_text,
                    "url": url,
                    "cve_id": cve_id,
                }, ensure_ascii=False)
                
                threats.append(threat)
            
            return threats
            
        except Exception as e:
            logger.error(
                f"解析通報失敗：{str(e)}",
                extra={
                    "feed_id": feed.id,
                    "advisory_url": advisory.get("url"),
                    "error": str(e),
                }
            )
            return []
    
    def get_collector_type(self) -> str:
        """
        取得收集器類型
        
        Returns:
            str: 收集器類型
        """
        return "TWCERT"

