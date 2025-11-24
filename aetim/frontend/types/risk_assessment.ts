/**
 * 風險評估相關類型定義
 */

export type RiskLevel = "Critical" | "High" | "Medium" | "Low";

export interface RiskCalculationResponse {
  success: boolean;
  threat_id: string;
  risk_assessment_id: string;
  final_risk_score: number;
  risk_level: RiskLevel;
  calculated_at: string;
}

export interface RiskAssessmentDetailResponse {
  id: string;
  threat_id: string;
  threat_asset_association_id: string;
  base_cvss_score: number;
  asset_importance_weight: number;
  affected_asset_count: number;
  asset_count_weight: number;
  pir_match_weight?: number;
  cisa_kev_weight?: number;
  final_risk_score: number;
  risk_level: RiskLevel;
  calculation_details?: Record<string, any>;
  calculation_formula?: string;
  created_at: string;
  updated_at: string;
}

export interface RiskAssessmentHistoryResponse {
  id: string;
  risk_assessment_id: string;
  base_cvss_score: number;
  asset_importance_weight: number;
  affected_asset_count: number;
  asset_count_weight: number;
  pir_match_weight?: number;
  cisa_kev_weight?: number;
  final_risk_score: number;
  risk_level: RiskLevel;
  calculation_details?: Record<string, any>;
  calculated_at: string;
}

export interface RiskAssessmentHistoryListResponse {
  items: RiskAssessmentHistoryResponse[];
  total: number;
  threat_id: string;
}

export interface CalculateRiskRequest {
  threat_asset_association_id: string;
  threat_feed_name?: string;
}

