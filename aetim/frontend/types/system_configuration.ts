/**
 * 系統設定類型定義
 */

export interface SystemConfiguration {
  id: string;
  key: string;
  value: string;
  category: string;
  description?: string;
  created_at: string;
  updated_at: string;
  updated_by: string;
}

export interface SystemConfigurationUpdateRequest {
  key: string;
  value: string;
  description?: string;
  category?: string;
}

export interface SystemConfigurationBatchUpdateRequest {
  configurations: SystemConfigurationUpdateRequest[];
}

export interface SystemConfigurationListResponse {
  configurations: SystemConfiguration[];
  total: number;
}

