/**
 * 威脅相關類型定義
 */

export interface ThreatProduct {
  id: string;
  product_name: string;
  product_version?: string;
  product_type?: string;
  original_text?: string;
}

export interface Threat {
  id: string;
  threat_feed_id: string;
  title: string;
  description?: string;
  cve_id?: string;
  cvss_base_score?: number;
  cvss_vector?: string;
  severity?: "Critical" | "High" | "Medium" | "Low";
  status: "New" | "Analyzing" | "Processed" | "Closed";
  source_url?: string;
  published_date?: string;
  collected_at?: string;
  products: ThreatProduct[];
  ttps: string[];
  iocs: {
    ips?: string[];
    domains?: string[];
    hashes?: string[];
  };
  created_at: string;
  updated_at: string;
}

export interface ThreatListResponse {
  items: Threat[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ThreatDetailResponse {
  threat: Threat;
  associated_assets: Array<{
    asset_id: string;
    match_confidence: number;
    match_type: string;
    match_details?: string;
    created_at?: string;
  }>;
}

export interface ThreatSearchParams {
  page?: number;
  page_size?: number;
  status?: "New" | "Analyzing" | "Processed" | "Closed";
  threat_feed_id?: string;
  cve_id?: string;
  product_name?: string;
  min_cvss_score?: number;
  max_cvss_score?: number;
  sort_by?: "created_at" | "updated_at" | "cvss_base_score" | "published_date";
  sort_order?: "asc" | "desc";
}

export interface UpdateThreatStatusRequest {
  status: "New" | "Analyzing" | "Processed" | "Closed";
}

