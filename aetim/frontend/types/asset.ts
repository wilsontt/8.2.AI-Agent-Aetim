/**
 * 資產相關類型定義
 */

export interface Asset {
  id: string;
  host_name: string;
  ip?: string;
  item?: number;
  operating_system: string;
  running_applications: string;
  owner: string;
  data_sensitivity: "高" | "中" | "低";
  is_public_facing: boolean;
  business_criticality: "高" | "中" | "低";
  products: Product[];
  created_at: string;
  updated_at: string;
  created_by: string;
  updated_by: string;
}

export interface Product {
  id: string;
  product_name: string;
  product_version?: string;
  product_type?: string;
  original_text?: string;
}

export interface AssetListResponse {
  data: Asset[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CreateAssetRequest {
  host_name: string;
  ip?: string;
  item?: number;
  operating_system: string;
  running_applications: string;
  owner: string;
  data_sensitivity: "高" | "中" | "低";
  is_public_facing: boolean;
  business_criticality: "高" | "中" | "低";
}

export interface UpdateAssetRequest {
  host_name?: string;
  ip?: string;
  operating_system?: string;
  running_applications?: string;
  owner?: string;
  data_sensitivity?: "高" | "中" | "低";
  is_public_facing?: boolean;
  business_criticality?: "高" | "中" | "低";
}

export interface AssetSearchParams {
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  product_name?: string;
  product_version?: string;
  product_type?: string;
  is_public_facing?: boolean;
  data_sensitivity?: "高" | "中" | "低";
  business_criticality?: "高" | "中" | "低";
}

export interface ImportPreviewResponse {
  total_count: number;
  valid_count: number;
  invalid_count: number;
  preview_data: Array<{
    row: number;
    data: Record<string, string>;
  }>;
  errors: Array<{
    row: number;
    field: string;
    error: string;
  }>;
}

export interface ImportResultResponse {
  total_count: number;
  success_count: number;
  failure_count: number;
  results: Array<{
    row: number;
    success: boolean;
    asset_id?: string;
    error?: string;
  }>;
}

