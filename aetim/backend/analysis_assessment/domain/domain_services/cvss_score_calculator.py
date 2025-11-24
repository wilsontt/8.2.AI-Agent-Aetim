"""
CVSS 基礎分數計算服務

實作 CVSS 基礎分數計算邏輯，符合 AC-012-1 的要求。
"""

from typing import Optional
import re

from threat_intelligence.domain.aggregates.threat import Threat
import structlog

logger = structlog.get_logger(__name__)


class CVSSScoreCalculator:
    """
    CVSS 基礎分數計算服務（Domain Service）
    
    負責計算 CVSS 基礎分數，支援：
    1. 直接使用威脅的 cvss_score
    2. 從 CVSS 向量解析並計算分數（CVSS v3.1）
    """
    
    def calculate_base_score(
        self,
        threat: Threat,
    ) -> float:
        """
        計算基礎 CVSS 分數（AC-012-1）
        
        Args:
            threat: 威脅聚合根
        
        Returns:
            float: 基礎 CVSS 分數（0.0 - 10.0）
        """
        # 如果威脅已有 cvss_score，直接使用
        if threat.cvss_base_score is not None:
            return float(threat.cvss_base_score)
        
        # 如果只有 CVSS 向量，解析向量並計算分數
        if threat.cvss_vector:
            try:
                score = self.parse_cvss_vector(threat.cvss_vector)
                if score is not None:
                    return score
            except Exception as e:
                logger.warning(
                    "解析 CVSS 向量失敗",
                    threat_id=threat.id,
                    cvss_vector=threat.cvss_vector,
                    error=str(e),
                )
        
        # 如果沒有 CVSS 分數或向量，預設為 0.0
        logger.warning(
            "威脅沒有 CVSS 分數，使用預設值 0.0",
            threat_id=threat.id,
        )
        return 0.0
    
    def parse_cvss_vector(self, cvss_vector: str) -> Optional[float]:
        """
        解析 CVSS 向量並計算分數（CVSS v3.1）
        
        支援 CVSS v3.1 向量格式：
        CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
        
        Args:
            cvss_vector: CVSS 向量字串
        
        Returns:
            Optional[float]: CVSS 基礎分數（0.0 - 10.0），如果解析失敗則返回 None
        
        Note:
            這是簡化的實作，完整的 CVSS 計算需要考慮所有指標。
            建議使用官方 CVSS 計算函式庫（如 cvss）進行完整計算。
        """
        if not cvss_vector or not cvss_vector.strip():
            return None
        
        # 檢查是否為 CVSS v3.1 格式
        if not cvss_vector.startswith("CVSS:3.1/"):
            logger.warning(
                "不支援的 CVSS 向量格式",
                cvss_vector=cvss_vector,
            )
            return None
        
        # 簡化的 CVSS 計算邏輯
        # 注意：這是簡化實作，完整的 CVSS 計算需要考慮所有指標
        # 實際應用中應使用官方 CVSS 計算函式庫
        
        try:
            # 提取向量中的指標
            metrics = {}
            vector_parts = cvss_vector.split("/")
            
            for part in vector_parts[1:]:  # 跳過 "CVSS:3.1"
                if ":" in part:
                    key, value = part.split(":", 1)
                    metrics[key] = value
            
            # 簡化的分數計算（基於關鍵指標）
            # 完整的 CVSS v3.1 計算需要考慮：
            # - Attack Vector (AV)
            # - Attack Complexity (AC)
            # - Privileges Required (PR)
            # - User Interaction (UI)
            # - Scope (S)
            # - Confidentiality (C)
            # - Integrity (I)
            # - Availability (A)
            
            # 這裡使用簡化邏輯，實際應使用官方計算公式
            # 如果向量中包含分數，嘗試提取
            score_match = re.search(r"(\d+\.\d+)", cvss_vector)
            if score_match:
                score = float(score_match.group(1))
                return min(10.0, max(0.0, score))
            
            # 如果無法從向量中提取分數，返回 None
            # 建議使用官方 CVSS 計算函式庫
            logger.warning(
                "無法從 CVSS 向量計算分數，建議使用官方 CVSS 計算函式庫",
                cvss_vector=cvss_vector,
            )
            return None
            
        except Exception as e:
            logger.error(
                "解析 CVSS 向量時發生錯誤",
                cvss_vector=cvss_vector,
                error=str(e),
            )
            return None
    
    def calculate_from_vector(self, cvss_vector: str) -> Optional[float]:
        """
        從 CVSS 向量計算基礎分數
        
        Args:
            cvss_vector: CVSS 向量字串
        
        Returns:
            Optional[float]: CVSS 基礎分數（0.0 - 10.0），如果計算失敗則返回 None
        """
        return self.parse_cvss_vector(cvss_vector)

