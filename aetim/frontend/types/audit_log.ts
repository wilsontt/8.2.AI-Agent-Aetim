/**
 * 稽核日誌類型定義
 */

export interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, any> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface AuditLogListResponse {
  data: AuditLog[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AuditLogFilterParams {
  user_id?: string;
  action?: string;
  resource_type?: string;
  resource_id?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

