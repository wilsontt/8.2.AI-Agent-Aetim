/**
 * 威脅情資來源相關類型定義
 */

export interface ThreatFeed {
  id: string;
  name: string;
  description?: string;
  priority: "P0" | "P1" | "P2" | "P3";
  is_enabled: boolean;
  collection_frequency?: string;
  collection_strategy?: string;
  last_collection_time?: string;
  last_collection_status?: "success" | "failed" | "in_progress";
  last_collection_error?: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  updated_by: string;
}

export interface ThreatFeedListResponse {
  data: ThreatFeed[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CreateThreatFeedRequest {
  name: string;
  description?: string;
  priority: "P0" | "P1" | "P2" | "P3";
  collection_frequency: string;
  collection_strategy?: string;
  api_key?: string;
  is_enabled?: boolean;
}

export interface UpdateThreatFeedRequest {
  name?: string;
  description?: string;
  priority?: "P0" | "P1" | "P2" | "P3";
  collection_frequency?: string;
  collection_strategy?: string;
  api_key?: string;
}

export interface CollectionStatusResponse {
  threat_feed_id: string;
  name: string;
  last_collection_time?: string;
  last_collection_status?: "success" | "failed" | "in_progress";
  last_collection_error?: string;
  is_enabled: boolean;
  collection_frequency?: string;
}

