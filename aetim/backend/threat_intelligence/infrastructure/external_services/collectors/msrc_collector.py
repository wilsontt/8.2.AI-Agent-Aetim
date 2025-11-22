"""
MSRC 收集器

從 Microsoft Security Response Center (MSRC) 收集威脅情資。
"""

import httpx
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..collector_interface import ICollector
from ....domain.aggregates.threat import Threat
from ....domain.aggregates.threat_feed import ThreatFeed
from ....domain.value_objects.threat_severity import ThreatSeverity
from shared_kernel.infrastructure.logging import get_logger

logger = get_logger(__name__)


class MSRCCollector(ICollector):
    """
    MSRC 收集器
    
    從 Microsoft Security Response Center (MSRC) 收集威脅情資。
    
    API 端點：
    - Security Updates API: https://api.msrc.microsoft.com/cvrf/v2.0/updates
    - CVRF Document API: https://api.msrc.microsoft.com/cvrf/v2.0/cvrf/{ID}
    """
    
    # MSRC API 基礎 URL
    MSRC_API_BASE_URL = "https://api.msrc.microsoft.com/cvrf/v2.0"
    
    # 請求超時時間（秒）
    REQUEST_TIMEOUT = 30
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 MSRC 收集器
        
        Args:
            api_key: MSRC API 金鑰（可選）
        """
        self.api_key = api_key
    
    async def collect(
        self,
        feed: ThreatFeed,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Threat]:
        """
        收集 MSRC 威脅情資
        
        Args:
            feed: 威脅情資來源聚合根
            start_date: 開始日期（用於增量收集）
            end_date: 結束日期（如果為 None 則使用當前時間）
        
        Returns:
            List[Threat]: 收集到的威脅列表
        
        Raises:
            Exception: 當收集失敗時
        """
        logger.info(
            f"開始收集 MSRC 威脅情資",
            extra={
                "feed_id": feed.id,
                "feed_name": feed.name,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            }
        )
        
        if not end_date:
            end_date = datetime.utcnow()
        
        try:
            # 1. 取得安全更新列表
            updates = await self._fetch_updates()
            
            if not updates:
                logger.warning(
                    "MSRC API 返回空的安全更新列表",
                    extra={"feed_id": feed.id}
                )
                return []
            
            logger.info(
                f"從 MSRC API 取得 {len(updates)} 個安全更新",
                extra={"feed_id": feed.id, "count": len(updates)}
            )
            
            # 2. 過濾日期範圍（如果指定）
            if start_date:
                updates = [
                    update for update in updates
                    if self._is_update_in_date_range(update, start_date, end_date)
                ]
            
            # 3. 取得每個更新的詳細資訊並轉換為 Threat
            all_threats = []
            for update in updates:
                try:
                    threats = await self._fetch_and_parse_cvrf(update, feed)
                    all_threats.extend(threats)
                except Exception as e:
                    logger.warning(
                        f"解析安全更新失敗：{str(e)}",
                        extra={
                            "feed_id": feed.id,
                            "update_id": update.get("ID"),
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
            error_msg = f"MSRC API 請求失敗：{str(e)}"
            logger.error(error_msg, extra={"feed_id": feed.id, "error": str(e)})
            raise Exception(error_msg) from e
        except json.JSONDecodeError as e:
            error_msg = f"MSRC API 回應格式錯誤：{str(e)}"
            logger.error(error_msg, extra={"feed_id": feed.id, "error": str(e)})
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"收集 MSRC 威脅情資時發生未預期錯誤：{str(e)}"
            logger.error(error_msg, extra={"feed_id": feed.id, "error": str(e)})
            raise
    
    async def _fetch_updates(self) -> List[Dict[str, Any]]:
        """
        取得安全更新列表
        
        Returns:
            List[Dict]: 安全更新列表
        """
        url = f"{self.MSRC_API_BASE_URL}/updates"
        
        headers = {}
        if self.api_key:
            headers["apiKey"] = self.api_key
        
        async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        
        return data.get("value", [])
    
    async def _fetch_and_parse_cvrf(
        self,
        update: Dict[str, Any],
        feed: ThreatFeed,
    ) -> List[Threat]:
        """
        取得並解析 CVRF 文件
        
        Args:
            update: 安全更新資訊
            feed: 威脅情資來源聚合根
        
        Returns:
            List[Threat]: 威脅列表
        """
        update_id = update.get("ID")
        if not update_id:
            return []
        
        url = f"{self.MSRC_API_BASE_URL}/cvrf/{update_id}"
        
        headers = {}
        if self.api_key:
            headers["apiKey"] = self.api_key
        
        async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            cvrf_data = response.json()
        
        # 解析 CVRF 文件
        threats = []
        
        # 提取文件資訊
        document_title = cvrf_data.get("DocumentTitle", "")
        document_tracking = cvrf_data.get("DocumentTracking", {})
        document_notes = cvrf_data.get("DocumentNotes", [])
        
        # 提取發布日期
        published_date = None
        initial_release_date = document_tracking.get("InitialReleaseDate")
        if initial_release_date:
            try:
                published_date = datetime.fromisoformat(initial_release_date.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        
        # 提取漏洞資訊
        vulnerabilities = cvrf_data.get("Vulnerability", [])
        
        for vuln in vulnerabilities:
            try:
                threat = self._parse_vulnerability(
                    vuln,
                    feed,
                    document_title,
                    document_notes,
                    published_date,
                )
                if threat:
                    threats.append(threat)
            except Exception as e:
                logger.warning(
                    f"解析漏洞失敗：{str(e)}",
                    extra={
                        "feed_id": feed.id,
                        "update_id": update_id,
                        "error": str(e),
                    }
                )
                continue
        
        return threats
    
    def _parse_vulnerability(
        self,
        vuln: Dict[str, Any],
        feed: ThreatFeed,
        document_title: str,
        document_notes: List[Dict],
        published_date: Optional[datetime],
    ) -> Threat | None:
        """
        解析單一漏洞資料並轉換為 Threat 聚合根
        
        Args:
            vuln: 漏洞資料字典
            feed: 威脅情資來源聚合根
            document_title: 文件標題
            document_notes: 文件備註
            published_date: 發布日期
        
        Returns:
            Threat: 威脅聚合根，如果解析失敗則返回 None
        """
        try:
            # 提取 CVE ID
            cve_id = vuln.get("CVE")
            if not cve_id:
                logger.warning("漏洞缺少 CVE 編號，跳過", extra={"vuln": vuln})
                return None
            
            # 提取標題
            title = f"{cve_id}: {document_title}" if document_title else cve_id
            
            # 提取描述
            notes = vuln.get("Notes", [])
            description = ""
            for note in notes:
                if note.get("Type") == "Description" and note.get("Lang") == "en":
                    description = note.get("Text", "")
                    break
            
            if not description:
                # 如果沒有找到描述，使用文件備註
                for note in document_notes:
                    if note.get("Type") == "General" and note.get("Lang") == "en":
                        description = note.get("Value", "")
                        break
            
            if not description:
                description = f"Microsoft Security Update: {cve_id}"
            
            # 提取 CVSS 分數
            cvss_base_score = None
            cvss_vector = None
            severity = None
            
            cvss_sets = vuln.get("CVSSScoreSets", [])
            if cvss_sets:
                cvss = cvss_sets[0]  # 使用第一個 CVSS 分數集
                base_score = cvss.get("BaseScore")
                if base_score is not None:
                    try:
                        cvss_base_score = float(base_score)
                    except (ValueError, TypeError):
                        pass
                
                vector_string = cvss.get("Vector")
                if vector_string:
                    cvss_vector = vector_string
            
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
                source_url=f"https://msrc.microsoft.com/update-guide/vulnerability/{cve_id}",
                published_date=published_date,
                collected_at=datetime.utcnow(),
            )
            
            # 提取產品資訊（從 ProductStatuses）
            product_statuses = vuln.get("ProductStatuses", [])
            for status in product_statuses:
                products = status.get("ProductID", [])
                for product_id in products:
                    # 從 ProductTree 中查找產品資訊
                    # 這裡簡化處理，實際需要從 CVRF 的 ProductTree 中查找
                    # 暫時使用 product_id 作為產品名稱
                    threat.add_product(
                        product_name=product_id,
                        original_text=product_id,
                    )
            
            # 儲存原始資料（JSON 格式）
            threat.raw_data = json.dumps(vuln, ensure_ascii=False)
            
            return threat
            
        except Exception as e:
            logger.error(
                f"解析漏洞資料失敗：{str(e)}",
                extra={
                    "feed_id": feed.id,
                    "cve_id": vuln.get("CVE"),
                    "error": str(e),
                }
            )
            return None
    
    def _is_update_in_date_range(
        self,
        update: Dict[str, Any],
        start_date: datetime,
        end_date: datetime,
    ) -> bool:
        """
        檢查更新是否在日期範圍內
        
        Args:
            update: 安全更新資訊
            start_date: 開始日期
            end_date: 結束日期
        
        Returns:
            bool: 是否在日期範圍內
        """
        release_date_str = update.get("ReleaseDate")
        if not release_date_str:
            return True  # 如果沒有發布日期，包含在內
        
        try:
            release_date = datetime.fromisoformat(release_date_str.replace("Z", "+00:00"))
            return start_date <= release_date <= end_date
        except (ValueError, AttributeError):
            return True  # 如果無法解析日期，包含在內
    
    def get_collector_type(self) -> str:
        """
        取得收集器類型
        
        Returns:
            str: 收集器類型
        """
        return "MSRC"

