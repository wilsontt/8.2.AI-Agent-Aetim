/**
 * 報告類型定義
 */

export type ReportType = "CISO_Weekly" | "IT_Ticket";

export type FileFormat = "HTML" | "PDF" | "TEXT" | "JSON";

export type TicketStatus = "Pending" | "InProgress" | "Resolved" | "Closed";

export interface Report {
  id: string;
  report_type: ReportType;
  title: string;
  file_path?: string;
  file_format: FileFormat;
  metadata?: Record<string, any>;
  ticket_status?: TicketStatus;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface ReportListResponse {
  items: Report[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ReportDetailResponse {
  id: string;
  report_type: ReportType;
  title: string;
  file_path?: string;
  file_format: FileFormat;
  metadata?: Record<string, any>;
  ticket_status?: TicketStatus;
  content?: string; // 報告內容（用於預覽）
  created_at: string;
  updated_at: string;
  created_by: string;
}

export interface ReportSearchParams {
  page?: number;
  page_size?: number;
  report_type?: ReportType;
  file_format?: FileFormat;
  ticket_status?: TicketStatus;
  start_date?: string;
  end_date?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}

export interface GenerateReportRequest {
  report_type: ReportType;
  start_date?: string;
  end_date?: string;
  file_format?: FileFormat;
}

export interface GenerateReportResponse {
  report_id: string;
  status: string;
  message?: string;
}

