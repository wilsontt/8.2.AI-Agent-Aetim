"""
CISA KEV 收集器

從 CISA Known Exploited Vulnerabilities (KEV) 目錄收集威脅情資。
"""

import httpx
import json
from typing import List, Dict, Any
from datetime import datetime
from ..collector_interface import ICollector
from ....domain.aggregates.threat import Threat
from ....domain.aggregates.threat_feed import ThreatFeed
from ....domain.value_objects.threat_severity import ThreatSeverity
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class CISAKEVCollector(ICollector):
    """
    CISA KEV 收集器
    
    從 CISA Known Exploited Vulnerabilities (KEV) 目錄收集威脅情資。
    
    API 端點：
    - JSON Feed: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
    """
    
    # CISA KEV JSON Feed URL
    KEV_API_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    
    # 請求超時時間（秒）
    REQUEST_TIMEOUT = 30
    
    def __init__(self):
        """初始化 CISA KEV 收集器"""
        pass
    
    async def collect(self, feed: ThreatFeed) -> List[Threat]:
        """
        收集 CISA KEV 威脅情資
        
        Args:
            feed: 威脅情資來源聚合根
        
        Returns:
            List[Threat]: 收集到的威脅列表
        
        Raises:
            Exception: 當收集失敗時
        """
        logger.info(
            f"開始收集 CISA KEV 威脅情資",
            extra={"feed_id": feed.id, "feed_name": feed.name}
        )
        
        try:
            # 1. 呼叫 CISA KEV API
            async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
                response = await client.get(self.KEV_API_URL)
                response.raise_for_status()
                data = response.json()
            
            # 2. 解析 JSON 回應
            vulnerabilities = data.get("vulnerabilities", [])
            
            if not vulnerabilities:
                logger.warning(
                    "CISA KEV API 返回空的漏洞列表",
                    extra={"feed_id": feed.id}
                )
                return []
            
            logger.info(
                f"從 CISA KEV API 取得 {len(vulnerabilities)} 個漏洞",
                extra={"feed_id": feed.id, "count": len(vulnerabilities)}
            )
            
            # 3. 轉換為 Threat 聚合根
            threats = []
            for vuln in vulnerabilities:
                try:
                    threat = self._parse_vulnerability(vuln, feed)
                    if threat:
                        threats.append(threat)
                except Exception as e:
                    logger.warning(
                        f"解析漏洞失敗：{str(e)}",
                        extra={
                            "feed_id": feed.id,
                            "cve_id": vuln.get("cveID"),
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
            error_msg = f"CISA KEV API 請求失敗：{str(e)}"
            logger.error(error_msg, extra={"feed_id": feed.id, "error": str(e)})
            raise Exception(error_msg) from e
        except json.JSONDecodeError as e:
            error_msg = f"CISA KEV API 回應格式錯誤：{str(e)}"
            logger.error(error_msg, extra={"feed_id": feed.id, "error": str(e)})
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"收集 CISA KEV 威脅情資時發生未預期錯誤：{str(e)}"
            logger.error(error_msg, extra={"feed_id": feed.id, "error": str(e)})
            raise
    
    def _parse_vulnerability(self, vuln: Dict[str, Any], feed: ThreatFeed) -> Threat | None:
        """
        解析單一漏洞資料並轉換為 Threat 聚合根
        
        Args:
            vuln: 漏洞資料字典
            feed: 威脅情資來源聚合根
        
        Returns:
            Threat: 威脅聚合根，如果解析失敗則返回 None
        """
        try:
            # 提取基本資訊
            cve_id = vuln.get("cveID")
            if not cve_id:
                logger.warning("漏洞缺少 CVE 編號，跳過", extra={"vuln": vuln})
                return None
            
            # 提取標題和描述
            vendor_project = vuln.get("vendorProject", "")
            product = vuln.get("product", "")
            vulnerability_name = vuln.get("vulnerabilityName", "")
            
            # 組合標題
            title_parts = []
            if vendor_project:
                title_parts.append(vendor_project)
            if product:
                title_parts.append(product)
            if vulnerability_name:
                title_parts.append(vulnerability_name)
            
            title = " - ".join(title_parts) if title_parts else f"CVE-{cve_id}"
            
            # 提取描述
            description = vuln.get("shortDescription", "")
            if not description:
                description = f"Known Exploited Vulnerability: {title}"
            
            # 提取日期
            date_added = vuln.get("dateAdded")
            published_date = None
            if date_added:
                try:
                    # CISA KEV 日期格式：YYYY-MM-DD
                    published_date = datetime.strptime(date_added, "%Y-%m-%d")
                except ValueError:
                    logger.warning(
                        f"無法解析日期格式：{date_added}",
                        extra={"cve_id": cve_id, "date_added": date_added}
                    )
            
            # 提取 CVSS 分數（如果有）
            cvss_base_score = None
            if "cvssScore" in vuln:
                try:
                    cvss_base_score = float(vuln["cvssScore"])
                except (ValueError, TypeError):
                    pass
            
            # 根據 CVSS 分數決定嚴重程度（如果沒有 CVSS，預設為 High，因為是已知被利用的漏洞）
            severity = None
            if cvss_base_score is not None:
                # Threat.create 會根據 CVSS 分數自動決定嚴重程度
                pass
            else:
                # 沒有 CVSS 分數，但這是已知被利用的漏洞，預設為 High
                severity = ThreatSeverity("High")
            
            # 建立威脅聚合根
            threat = Threat.create(
                threat_feed_id=feed.id,
                title=title,
                description=description,
                cve_id=cve_id,
                cvss_base_score=cvss_base_score,
                severity=severity,
                source_url=f"https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
                published_date=published_date,
                collected_at=datetime.utcnow(),
            )
            
            # 提取產品資訊
            if vendor_project and product:
                # 嘗試從 product 欄位提取版本資訊
                product_parts = product.split()
                product_name = vendor_project
                product_version = None
                
                # 簡單的版本提取邏輯（例如：Microsoft Windows 10 可能包含版本）
                if len(product_parts) > 1:
                    # 檢查最後一個部分是否為版本號
                    last_part = product_parts[-1]
                    if any(char.isdigit() for char in last_part):
                        product_version = last_part
                        product_name = " ".join(product_parts[:-1])
                    else:
                        product_name = product
                else:
                    product_name = product
                
                threat.add_product(
                    product_name=product_name,
                    product_version=product_version,
                    original_text=product,
                )
            
            # 提取其他資訊
            required_action = vuln.get("requiredAction", "")
            if required_action:
                # 將 requiredAction 加入描述
                threat.description = f"{threat.description}\n\nRequired Action: {required_action}"
            
            # 儲存原始資料（JSON 格式）
            threat.raw_data = json.dumps(vuln, ensure_ascii=False)
            
            return threat
            
        except Exception as e:
            logger.error(
                f"解析漏洞資料失敗：{str(e)}",
                extra={
                    "feed_id": feed.id,
                    "cve_id": vuln.get("cveID"),
                    "error": str(e),
                }
            )
            return None
    
    def get_collector_type(self) -> str:
        """
        取得收集器類型
        
        Returns:
            str: 收集器類型
        """
        return "CISA_KEV"

