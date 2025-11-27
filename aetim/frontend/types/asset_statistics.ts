/**
 * 資產統計類型定義
 */

export interface AssetStatistics {
  total_count: number;
  by_type: Record<string, number>;
  by_sensitivity: Record<string, number>;
  by_criticality: Record<string, number>;
  affected_assets: {
    count: number;
    percentage: number;
  };
  public_facing_count: number;
}

