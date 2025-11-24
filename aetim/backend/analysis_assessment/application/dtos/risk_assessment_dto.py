"""
風險評估 DTO

定義風險評估相關的資料傳輸物件。
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class RiskCalculationResponse(BaseModel):
    """風險計算回應"""
    
    success: bool
    threat_id: str
    risk_assessment_id: str
    final_risk_score: float = Field(..., ge=0.0, le=10.0, description="最終風險分數（0.0-10.0）")
    risk_level: str = Field(..., description="風險等級（Critical/High/Medium/Low）")
    calculated_at: datetime = Field(..., description="計算時間")


class RiskAssessmentDetailResponse(BaseModel):
    """風險評估詳情回應（AC-013-1, AC-013-2）"""
    
    id: str
    threat_id: str
    threat_asset_association_id: str
    
    # 基礎分數
    base_cvss_score: float = Field(..., ge=0.0, le=10.0, description="基礎 CVSS 分數")
    
    # 加權因子
    asset_importance_weight: float = Field(..., description="資產重要性加權")
    affected_asset_count: int = Field(..., ge=0, description="受影響資產數量")
    asset_count_weight: float = Field(..., description="資產數量加權")
    pir_match_weight: Optional[float] = Field(None, description="PIR 符合度加權")
    cisa_kev_weight: Optional[float] = Field(None, description="CISA KEV 加權")
    
    # 最終結果
    final_risk_score: float = Field(..., ge=0.0, le=10.0, description="最終風險分數")
    risk_level: str = Field(..., description="風險等級（Critical/High/Medium/Low）")
    
    # 計算詳情
    calculation_details: Optional[Dict[str, Any]] = Field(None, description="計算詳情（JSON 格式）")
    calculation_formula: Optional[str] = Field(None, description="計算公式")
    
    # 時間戳記
    created_at: datetime
    updated_at: datetime


class RiskAssessmentHistoryResponse(BaseModel):
    """風險評估歷史記錄回應（AC-013-3）"""
    
    id: str
    risk_assessment_id: str
    
    # 基礎分數
    base_cvss_score: float = Field(..., ge=0.0, le=10.0, description="基礎 CVSS 分數")
    
    # 加權因子
    asset_importance_weight: float = Field(..., description="資產重要性加權")
    asset_count_weight: float = Field(..., description="資產數量加權")
    pir_match_weight: Optional[float] = Field(None, description="PIR 符合度加權")
    cisa_kev_weight: Optional[float] = Field(None, description="CISA KEV 加權")
    
    # 最終結果
    final_risk_score: float = Field(..., ge=0.0, le=10.0, description="最終風險分數")
    risk_level: str = Field(..., description="風險等級（Critical/High/Medium/Low）")
    
    # 計算詳情
    calculation_details: Optional[Dict[str, Any]] = Field(None, description="計算詳情（JSON 格式）")
    
    # 時間戳記
    calculated_at: datetime = Field(..., description="計算時間")


class RiskAssessmentHistoryListResponse(BaseModel):
    """風險評估歷史記錄清單回應"""
    
    items: List[RiskAssessmentHistoryResponse]
    total: int
    threat_id: str

