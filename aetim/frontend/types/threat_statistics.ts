/**
 * 威脅統計類型定義
 */

export interface ThreatTrendDataPoint {
  date: string;
  count: number;
}

export interface ThreatTrendResponse {
  data: ThreatTrendDataPoint[];
  start_date: string;
  end_date: string;
  interval: string;
}

export interface RiskDistributionResponse {
  distribution: {
    Critical: number;
    High: number;
    Medium: number;
    Low: number;
  };
  total: number;
}

export interface AffectedAssetStatisticsResponse {
  by_type: Record<string, number>;
  by_importance: Record<string, number>;
}

export interface ThreatSourceStatisticsDataPoint {
  source_name: string;
  priority: string;
  count: number;
}

export interface ThreatSourceStatisticsResponse {
  data: ThreatSourceStatisticsDataPoint[];
}

