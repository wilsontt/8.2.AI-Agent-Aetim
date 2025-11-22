"""
NVD 收集器

從 NVD (National Vulnerability Database) 收集威脅情資。
"""

import httpx
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..collector_interface import ICollector
from ....domain.aggregates.threat import Threat
from ....domain.aggregates.threat_feed import ThreatFeed
from ....domain.value_objects.threat_severity import ThreatSeverity
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class NVDCollector(ICollector):
    """
    NVD 收集器
    
    從 NVD (National Vulnerability Database) 收集威脅情資。
    
    API 端點：
    - REST API v2.0: https://services.nvd.nist.gov/rest/json/cves/2.0
    
    速率限制：
    - 無 API 金鑰：每 6 秒 5 個請求
    - 有 API 金鑰：每 6 秒 50 個請求
    """
    
    # NVD API 基礎 URL
    NVD_API_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    # 請求超時時間（秒）
    REQUEST_TIMEOUT = 30
    
    # 速率限制（每 6 秒 5 個請求，無 API 金鑰）
    RATE_LIMIT_REQUESTS = 5
    RATE_LIMIT_WINDOW = 6  # 秒
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 NVD 收集器
        
        Args:
            api_key: NVD API 金鑰（可選，有 API 金鑰可提高速率限制）
        """
        self.api_key = api_key
        self._rate_limiter = RateLimiter(
            max_requests=self.RATE_LIMIT_REQUESTS,
            window_seconds=self.RATE_LIMIT_WINDOW,
        )
    
    async def collect(
        self,
        feed: ThreatFeed,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Threat]:
        """
        收集 NVD 威脅情資
        
        Args:
            feed: 威脅情資來源聚合根
            start_date: 開始日期（用於增量收集，如果為 None 則收集最近 7 天的資料）
            end_date: 結束日期（如果為 None 則使用當前時間）
        
        Returns:
            List[Threat]: 收集到的威脅列表
        
        Raises:
            Exception: 當收集失敗時
        """
        logger.info(
            f"開始收集 NVD 威脅情資",
            extra={
                "feed_id": feed.id,
                "feed_name": feed.name,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            }
        )
        
        # 如果沒有指定日期，使用增量收集（最近 7 天）
        if not start_date:
            # 如果有最後收集時間，從最後收集時間開始
            if feed.last_collection_time:
                start_date = feed.last_collection_time
            else:
                # 否則收集最近 7 天的資料
                start_date = datetime.utcnow() - timedelta(days=7)
        
        if not end_date:
            end_date = datetime.utcnow()
        
        try:
            # 1. 使用分頁方式收集所有 CVE
            all_cves = []
            start_index = 0
            results_per_page = 2000  # NVD API 最大每頁 2000 筆
            
            while True:
                # 等待速率限制
                await self._rate_limiter.wait_if_needed()
                
                # 2. 呼叫 NVD API
                cves_batch = await self._fetch_cves_batch(
                    start_index=start_index,
                    results_per_page=results_per_page,
                    start_date=start_date,
                    end_date=end_date,
                )
                
                if not cves_batch:
                    break
                
                all_cves.extend(cves_batch)
                
                # 如果返回的資料少於每頁數量，表示已經是最後一頁
                if len(cves_batch) < results_per_page:
                    break
                
                start_index += results_per_page
                
                logger.debug(
                    f"已收集 {len(all_cves)} 個 CVE",
                    extra={"feed_id": feed.id, "count": len(all_cves)}
                )
            
            logger.info(
                f"從 NVD API 取得 {len(all_cves)} 個 CVE",
                extra={"feed_id": feed.id, "count": len(all_cves)}
            )
            
            # 3. 轉換為 Threat 聚合根
            threats = []
            for cve_data in all_cves:
                try:
                    threat = self._parse_cve(cve_data, feed)
                    if threat:
                        threats.append(threat)
                except Exception as e:
                    logger.warning(
                        f"解析 CVE 失敗：{str(e)}",
                        extra={
                            "feed_id": feed.id,
                            "cve_id": cve_data.get("id"),
                            "error": str(e),
                        }
                    )
                    continue
            
            logger.info(
                f"成功解析 {len(threats)} 個威脅",
                extra={"feed_id": feed.id, "threats_count": len(threats)}
            )
            
            return threats
            
        except httpx.HTTPError as e:
            error_msg = f"NVD API 請求失敗：{str(e)}"
            logger.error(error_msg, extra={"feed_id": feed.id, "error": str(e)})
            raise Exception(error_msg) from e
        except json.JSONDecodeError as e:
            error_msg = f"NVD API 回應格式錯誤：{str(e)}"
            logger.error(error_msg, extra={"feed_id": feed.id, "error": str(e)})
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"收集 NVD 威脅情資時發生未預期錯誤：{str(e)}"
            logger.error(error_msg, extra={"feed_id": feed.id, "error": str(e)})
            raise
    
    async def _fetch_cves_batch(
        self,
        start_index: int,
        results_per_page: int,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Dict[str, Any]]:
        """
        取得一批 CVE 資料
        
        Args:
            start_index: 起始索引
            results_per_page: 每頁結果數
            start_date: 開始日期
            end_date: 結束日期
        
        Returns:
            List[Dict]: CVE 資料列表
        """
        # 建立 API 請求 URL
        params = {
            "startIndex": start_index,
            "resultsPerPage": results_per_page,
            "pubStartDate": start_date.strftime("%Y-%m-%dT%H:%M:%S.000 UTC-00:00"),
            "pubEndDate": end_date.strftime("%Y-%m-%dT%H:%M:%S.000 UTC-00:00"),
        }
        
        # 如果有 API 金鑰，加入請求標頭
        headers = {}
        if self.api_key:
            headers["apiKey"] = self.api_key
        
        async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
            response = await client.get(
                self.NVD_API_BASE_URL,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        
        # 提取 CVE 列表
        vulnerabilities = data.get("vulnerabilities", [])
        return [vuln.get("cve", {}) for vuln in vulnerabilities if "cve" in vuln]
    
    def _parse_cve(self, cve_data: Dict[str, Any], feed: ThreatFeed) -> Threat | None:
        """
        解析單一 CVE 資料並轉換為 Threat 聚合根
        
        Args:
            cve_data: CVE 資料字典
            feed: 威脅情資來源聚合根
        
        Returns:
            Threat: 威脅聚合根，如果解析失敗則返回 None
        """
        try:
            # 提取 CVE ID
            cve_id = cve_data.get("id")
            if not cve_id:
                logger.warning("CVE 資料缺少 ID，跳過", extra={"cve_data": cve_data})
                return None
            
            # 提取描述
            descriptions = cve_data.get("descriptions", [])
            description = ""
            if descriptions:
                # 優先使用英文描述
                for desc in descriptions:
                    if desc.get("lang") == "en":
                        description = desc.get("value", "")
                        break
                # 如果沒有英文描述，使用第一個描述
                if not description and descriptions:
                    description = descriptions[0].get("value", "")
            
            if not description:
                description = f"CVE: {cve_id}"
            
            # 提取標題（使用 CVE ID 和描述的第一行）
            title = cve_id
            if description:
                title = f"{cve_id}: {description.split('.')[0][:100]}"
            
            # 提取發布日期
            published_date = None
            published = cve_data.get("published")
            if published:
                try:
                    # NVD 日期格式：2024-01-15T10:30:00.000
                    published_date = datetime.fromisoformat(published.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    logger.warning(
                        f"無法解析發布日期：{published}",
                        extra={"cve_id": cve_id, "published": published}
                    )
            
            # 提取 CVSS 分數
            cvss_base_score = None
            cvss_vector = None
            severity = None
            
            metrics = cve_data.get("metrics", {})
            
            # 優先使用 CVSS v3.1，其次 v3.0，最後 v2.0
            if "cvssMetricV31" in metrics:
                cvss_v31 = metrics["cvssMetricV31"][0] if metrics["cvssMetricV31"] else {}
                cvss_data = cvss_v31.get("cvssData", {})
                cvss_base_score = cvss_data.get("baseScore")
                cvss_vector = cvss_data.get("vectorString")
            elif "cvssMetricV30" in metrics:
                cvss_v30 = metrics["cvssMetricV30"][0] if metrics["cvssMetricV30"] else {}
                cvss_data = cvss_v30.get("cvssData", {})
                cvss_base_score = cvss_data.get("baseScore")
                cvss_vector = cvss_data.get("vectorString")
            elif "cvssMetricV2" in metrics:
                cvss_v2 = metrics["cvssMetricV2"][0] if metrics["cvssMetricV2"] else {}
                cvss_data = cvss_v2.get("cvssData", {})
                cvss_base_score = cvss_data.get("baseScore")
                cvss_vector = cvss_data.get("vectorString")
            
            # 根據 CVSS 分數決定嚴重程度
            if cvss_base_score is not None:
                # Threat.create 會根據 CVSS 分數自動決定嚴重程度
                pass
            else:
                # 沒有 CVSS 分數，預設為 Medium
                severity = ThreatSeverity("Medium")
            
            # 建立威脅聚合根
            threat = Threat.create(
                threat_feed_id=feed.id,
                title=title,
                description=description,
                cve_id=cve_id,
                cvss_base_score=cvss_base_score,
                cvss_vector=cvss_vector,
                severity=severity,
                source_url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                published_date=published_date,
                collected_at=datetime.utcnow(),
            )
            
            # 提取產品資訊（從 configurations）
            configurations = cve_data.get("configurations", [])
            for config in configurations:
                nodes = config.get("nodes", [])
                for node in nodes:
                    cpe_match = node.get("cpeMatch", [])
                    for cpe in cpe_match:
                        # 解析 CPE 字串：cpe:2.3:a:vendor:product:version:...
                        cpe_string = cpe.get("criteria", "")
                        if cpe_string:
                            product_info = self._parse_cpe(cpe_string)
                            if product_info:
                                threat.add_product(
                                    product_name=product_info["name"],
                                    product_version=product_info.get("version"),
                                    product_type=product_info.get("type"),
                                    original_text=cpe_string,
                                )
            
            # 儲存原始資料（JSON 格式）
            threat.raw_data = json.dumps(cve_data, ensure_ascii=False)
            
            return threat
            
        except Exception as e:
            logger.error(
                f"解析 CVE 資料失敗：{str(e)}",
                extra={
                    "feed_id": feed.id,
                    "cve_id": cve_data.get("id"),
                    "error": str(e),
                }
            )
            return None
    
    def _parse_cpe(self, cpe_string: str) -> Dict[str, str] | None:
        """
        解析 CPE 字串
        
        CPE 格式：cpe:2.3:a:vendor:product:version:update:edition:language:sw_edition:target_sw:target_hw:other
        
        Args:
            cpe_string: CPE 字串
        
        Returns:
            Dict: 包含 name, version, type 的字典，如果解析失敗則返回 None
        """
        try:
            parts = cpe_string.split(":")
            if len(parts) < 6:
                return None
            
            # CPE 類型：a=Application, o=Operating System, h=Hardware
            cpe_type = parts[2]
            vendor = parts[3]
            product = parts[4]
            version = parts[5] if len(parts) > 5 and parts[5] != "*" else None
            
            # 組合產品名稱
            if vendor and vendor != "*":
                product_name = f"{vendor} {product}" if product and product != "*" else vendor
            else:
                product_name = product if product and product != "*" else None
            
            if not product_name:
                return None
            
            # 決定產品類型
            product_type = None
            if cpe_type == "a":
                product_type = "Application"
            elif cpe_type == "o":
                product_type = "Operating System"
            elif cpe_type == "h":
                product_type = "Hardware"
            
            return {
                "name": product_name,
                "version": version,
                "type": product_type,
            }
        except Exception:
            return None
    
    def get_collector_type(self) -> str:
        """
        取得收集器類型
        
        Returns:
            str: 收集器類型
        """
        return "NVD"


class RateLimiter:
    """
    速率限制器
    
    用於控制 API 請求速率，符合 NVD API 的速率限制。
    """
    
    def __init__(self, max_requests: int, window_seconds: int):
        """
        初始化速率限制器
        
        Args:
            max_requests: 時間窗口內最大請求數
            window_seconds: 時間窗口（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._request_times = []
        self._lock = asyncio.Lock()
    
    async def wait_if_needed(self) -> None:
        """
        如果需要，等待直到可以發送請求
        
        這個方法會檢查是否超過速率限制，如果超過則等待。
        """
        async with self._lock:
            now = datetime.utcnow()
            
            # 移除超過時間窗口的請求時間
            cutoff_time = now - timedelta(seconds=self.window_seconds)
            self._request_times = [
                t for t in self._request_times if t > cutoff_time
            ]
            
            # 如果已達到最大請求數，等待
            if len(self._request_times) >= self.max_requests:
                # 計算需要等待的時間（最舊的請求時間 + 時間窗口 - 當前時間）
                oldest_request_time = min(self._request_times)
                wait_until = oldest_request_time + timedelta(seconds=self.window_seconds)
                wait_seconds = (wait_until - now).total_seconds()
                
                if wait_seconds > 0:
                    logger.debug(
                        f"速率限制：等待 {wait_seconds:.2f} 秒",
                        extra={"wait_seconds": wait_seconds}
                    )
                    await asyncio.sleep(wait_seconds)
                    
                    # 重新計算（移除過期的請求時間）
                    now = datetime.utcnow()
                    cutoff_time = now - timedelta(seconds=self.window_seconds)
                    self._request_times = [
                        t for t in self._request_times if t > cutoff_time
                    ]
            
            # 記錄當前請求時間
            self._request_times.append(datetime.utcnow())

