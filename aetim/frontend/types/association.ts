/**
 * 關聯分析相關類型定義
 */

export interface ThreatAssetAssociation {
  id: string;
  threat_id: string;
  asset_id: string;
  match_confidence: number;
  match_type: string;
  match_details?: {
    matched_products?: Array<{
      threat_product?: string;
      threat_version?: string;
      asset_product?: string;
      asset_version?: string;
      threat_os?: string;
      asset_os?: string;
    }>;
    os_match?: boolean;
    match_type?: string;
  };
  created_at?: string;
}

export interface ThreatAssociationListResponse {
  items: ThreatAssetAssociation[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AssetThreatAssociation {
  id: string;
  threat_id: string;
  asset_id: string;
  match_confidence: number;
  match_type: string;
  match_details?: {
    matched_products?: Array<{
      threat_product?: string;
      threat_version?: string;
      asset_product?: string;
      asset_version?: string;
      threat_os?: string;
      asset_os?: string;
    }>;
    os_match?: boolean;
    match_type?: string;
  };
  created_at?: string;
  threat_title?: string;
  threat_cve_id?: string;
  threat_cvss_base_score?: number;
  threat_severity?: "Critical" | "High" | "Medium" | "Low";
  threat_status?: "New" | "Analyzing" | "Processed" | "Closed";
}

export interface AssetThreatAssociationListResponse {
  items: AssetThreatAssociation[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AssociationAnalysisResponse {
  success: boolean;
  threat_id: string;
  associations_created: number;
  errors: string[];
}

export interface AssociationAnalysisLogResponse {
  threat_id: string;
  analysis_started_at?: string;
  analysis_completed_at?: string;
  associations_created: number;
  associations_deleted: number;
  errors: string[];
  status: "not_started" | "in_progress" | "completed";
}

export interface ThreatAssociationParams {
  page?: number;
  page_size?: number;
  min_confidence?: number;
  match_type?: string;
  sort_by?: "match_confidence" | "created_at";
  sort_order?: "asc" | "desc";
}

export interface AssetThreatAssociationParams {
  page?: number;
  page_size?: number;
  min_confidence?: number;
  match_type?: string;
  threat_severity?: "Critical" | "High" | "Medium" | "Low";
  threat_status?: "New" | "Analyzing" | "Processed" | "Closed";
  sort_by?: "match_confidence" | "threat_cvss_base_score" | "created_at";
  sort_order?: "asc" | "desc";
}

