/**
 * PIR 相關類型定義
 */

export interface PIR {
  id: string;
  name: string;
  description: string;
  priority: "高" | "中" | "低";
  condition_type: string;
  condition_value: string;
  is_enabled: boolean;
  created_at: string;
  updated_at: string;
  created_by: string;
  updated_by: string;
}

export interface PIRListResponse {
  data: PIR[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CreatePIRRequest {
  name: string;
  description: string;
  priority: "高" | "中" | "低";
  condition_type: string;
  condition_value: string;
  is_enabled?: boolean;
}

export interface UpdatePIRRequest {
  name?: string;
  description?: string;
  priority?: "高" | "中" | "低";
  condition_type?: string;
  condition_value?: string;
}

