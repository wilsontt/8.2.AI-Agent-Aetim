/**
 * 系統狀態類型定義
 */

export interface ThreatCollectionStatus {
  feed_id: string;
  feed_name: string;
  priority: string;
  last_collection_time: string | null;
  last_collection_status: string | null;
  status: "healthy" | "warning" | "error" | "unknown";
  collection_frequency: string;
}

export interface RecentThreatCount {
  last_24_hours: number;
  last_7_days: number;
}

export interface SystemHealthCheck {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  checks: {
    database?: string;
    redis?: string;
    ai_service?: string;
  };
}

export interface SystemStatus {
  timestamp: string;
  threat_collection_status: ThreatCollectionStatus[];
  recent_threat_count: RecentThreatCount;
  critical_threat_count: number;
  system_health: SystemHealthCheck;
}

