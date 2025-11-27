/**
 * 系統狀態儀表板頁面
 * 
 * 顯示系統狀態資訊和威脅統計圖表。
 * 符合 AC-027-1, AC-027-2, AC-027-4, AC-028-1, AC-028-2。
 */

"use client";

import React, { useState, useEffect } from "react";
import { usePermission } from "@/hooks/usePermission";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { getSystemStatus, type SystemStatus } from "@/lib/api/system_status";
import {
  getThreatTrend,
  getRiskDistribution,
  getAffectedAssetStatistics,
  getThreatSourceStatistics,
} from "@/lib/api/threat_statistics";
import { getAssetStatistics } from "@/lib/api/asset_statistics";
import type {
  ThreatTrendResponse,
  RiskDistributionResponse,
  AffectedAssetStatisticsResponse,
  ThreatSourceStatisticsResponse,
} from "@/types/threat_statistics";
import type { AssetStatistics } from "@/types/asset_statistics";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { exportChartAsPNG, exportChartAsPDF, exportMultipleChartsAsPDF } from "@/lib/utils/chartExport";

// 狀態顏色映射（符合 AC-027-4：顏色編碼）
const STATUS_COLORS = {
  healthy: "bg-green-100 text-green-800 border-green-300",
  warning: "bg-yellow-100 text-yellow-800 border-yellow-300",
  error: "bg-red-100 text-red-800 border-red-300",
  unknown: "bg-gray-100 text-gray-800 border-gray-300",
};

const HEALTH_STATUS_COLORS = {
  healthy: "bg-green-500",
  degraded: "bg-yellow-500",
  unhealthy: "bg-red-500",
};

// 風險等級顏色
const RISK_COLORS = {
  Critical: "#DC2626", // red-600
  High: "#F59E0B", // amber-500
  Medium: "#3B82F6", // blue-500
  Low: "#10B981", // green-500
};

// 時間範圍選項
const TIME_RANGE_OPTIONS = [
  { value: "7d", label: "最近 7 天", days: 7 },
  { value: "30d", label: "最近 30 天", days: 30 },
  { value: "90d", label: "最近 90 天", days: 90 },
  { value: "custom", label: "自訂範圍", days: null },
];

export default function DashboardPage() {
  const { hasPermission } = usePermission();
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [threatTrend, setThreatTrend] = useState<ThreatTrendResponse | null>(null);
  const [riskDistribution, setRiskDistribution] = useState<RiskDistributionResponse | null>(null);
  const [affectedAssets, setAffectedAssets] = useState<AffectedAssetStatisticsResponse | null>(null);
  const [threatSources, setThreatSources] = useState<ThreatSourceStatisticsResponse | null>(null);
  const [assetStatistics, setAssetStatistics] = useState<AssetStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [timeRange, setTimeRange] = useState("30d");
  const [customStartDate, setCustomStartDate] = useState("");
  const [customEndDate, setCustomEndDate] = useState("");
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadAllData();
    
    // 自動刷新（每 30 秒）
    const interval = setInterval(() => {
      if (autoRefresh) {
        loadAllData();
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, [autoRefresh, timeRange, customStartDate, customEndDate]);

  /**
   * 載入所有資料
   */
  const loadAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 計算時間範圍
      const { startDate, endDate } = getDateRange();

      // 並行載入所有資料
      const [
        systemStatusData,
        threatTrendData,
        riskDistributionData,
        affectedAssetsData,
        threatSourcesData,
        assetStatisticsData,
      ] = await Promise.all([
        getSystemStatus(),
        getThreatTrend(startDate, endDate, "day"),
        getRiskDistribution(startDate, endDate),
        getAffectedAssetStatistics(startDate, endDate),
        getThreatSourceStatistics(startDate, endDate),
        getAssetStatistics(),
      ]);

      setStatus(systemStatusData);
      setThreatTrend(threatTrendData);
      setRiskDistribution(riskDistributionData);
      setAffectedAssets(affectedAssetsData);
      setThreatSources(threatSourcesData);
      setAssetStatistics(assetStatisticsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入資料失敗");
    } finally {
      setLoading(false);
    }
  };

  /**
   * 取得日期範圍
   */
  const getDateRange = () => {
    const endDate = new Date();
    endDate.setHours(23, 59, 59, 999);

    let startDate: Date;
    if (timeRange === "custom") {
      startDate = customStartDate ? new Date(customStartDate) : new Date();
      startDate.setHours(0, 0, 0, 0);
    } else {
      const option = TIME_RANGE_OPTIONS.find((opt) => opt.value === timeRange);
      const days = option?.days || 30;
      startDate = new Date();
      startDate.setDate(startDate.getDate() - days);
      startDate.setHours(0, 0, 0, 0);
    }

    return {
      startDate: startDate.toISOString().split("T")[0],
      endDate: endDate.toISOString().split("T")[0],
    };
  };

  /**
   * 格式化時間
   */
  const formatTime = (timeStr: string | null) => {
    if (!timeStr) {
      return "尚未收集";
    }
    const date = new Date(timeStr);
    return date.toLocaleString("zh-TW");
  };

  /**
   * 取得狀態顯示文字
   */
  const getStatusText = (status: string) => {
    const statusMap: Record<string, string> = {
      healthy: "正常",
      warning: "警告",
      error: "錯誤",
      unknown: "未知",
    };
    return statusMap[status] || status;
  };

  /**
   * 取得健康狀態顯示文字
   */
  const getHealthStatusText = (status: string) => {
    const statusMap: Record<string, string> = {
      healthy: "正常",
      degraded: "降級",
      unhealthy: "異常",
    };
    return statusMap[status] || status;
  };

  /**
   * 準備風險分布圖表資料
   */
  const prepareRiskDistributionData = () => {
    if (!riskDistribution) return [];
    return Object.entries(riskDistribution.distribution).map(([key, value]) => ({
      name: key === "Critical" ? "嚴重" : key === "High" ? "高" : key === "Medium" ? "中" : "低",
      value,
      color: RISK_COLORS[key as keyof typeof RISK_COLORS],
    }));
  };

  /**
   * 準備受影響資產統計資料
   */
  const prepareAffectedAssetsData = () => {
    if (!affectedAssets) return [];
    return Object.entries(affectedAssets.by_type).map(([key, value]) => ({
      name: key || "未知",
      count: value,
    }));
  };

  /**
   * 準備威脅來源統計資料
   */
  const prepareThreatSourcesData = () => {
    if (!threatSources) return [];
    return threatSources.data.map((item) => ({
      name: item.source_name,
      count: item.count,
      priority: item.priority,
    }));
  };

  /**
   * 匯出單一圖表為 PNG
   */
  const handleExportPNG = async (elementId: string, filename: string) => {
    try {
      setExporting(true);
      await exportChartAsPNG(elementId, filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : "匯出 PNG 失敗");
    } finally {
      setExporting(false);
    }
  };

  /**
   * 匯出單一圖表為 PDF
   */
  const handleExportPDF = async (elementId: string, filename: string, title?: string) => {
    try {
      setExporting(true);
      await exportChartAsPDF(elementId, filename, title);
    } catch (err) {
      setError(err instanceof Error ? err.message : "匯出 PDF 失敗");
    } finally {
      setExporting(false);
    }
  };

  /**
   * 匯出所有圖表為 PDF
   */
  const handleExportAllPDF = async () => {
    try {
      setExporting(true);
      const charts = [
        { id: "threat-trend-chart", title: "威脅數量趨勢" },
        { id: "risk-distribution-chart", title: "風險分數分布" },
        { id: "affected-assets-chart", title: "受影響資產統計" },
        { id: "threat-sources-chart", title: "威脅來源統計" },
      ];
      await exportMultipleChartsAsPDF(charts, "威脅統計圖表");
    } catch (err) {
      setError(err instanceof Error ? err.message : "匯出 PDF 失敗");
    } finally {
      setExporting(false);
    }
  };

  return (
    <PermissionGate permissions={["system_config:view", "threat:view"]}>
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">系統狀態儀表板</h1>
            <p className="mt-2 text-gray-600">
              監控系統運作狀況與威脅統計（符合 AC-027-1, AC-028-1）
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm text-gray-600">自動刷新（30 秒）</span>
            </label>
            <button
              onClick={loadAllData}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              重新整理
            </button>
          </div>
        </div>

        {/* 時間範圍篩選器（符合 AC-028-2：支援時間範圍篩選） */}
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4">
          <div className="flex items-center space-x-4">
            <label className="text-sm font-medium text-gray-700">時間範圍：</label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500"
            >
              {TIME_RANGE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {timeRange === "custom" && (
              <>
                <label className="text-sm text-gray-700">開始日期：</label>
                <input
                  type="date"
                  value={customStartDate}
                  onChange={(e) => setCustomStartDate(e.target.value)}
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500"
                />
                <label className="text-sm text-gray-700">結束日期：</label>
                <input
                  type="date"
                  value={customEndDate}
                  onChange={(e) => setCustomEndDate(e.target.value)}
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500"
                />
              </>
            )}
          </div>
        </div>

        {/* 錯誤訊息 */}
        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">錯誤</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
              <p className="mt-4 text-gray-600">載入中...</p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* 系統狀態區塊（AC-027-1, AC-027-2） */}
            <div className="space-y-6">
              {/* 系統健康狀態卡片 */}
              <div className="rounded-lg border border-gray-200 bg-white p-6">
                <h2 className="mb-4 text-xl font-semibold text-gray-900">系統健康狀態</h2>
                <div className="flex items-center space-x-4">
                  <div
                    className={`h-4 w-4 rounded-full ${
                      HEALTH_STATUS_COLORS[status?.system_health.status as keyof typeof HEALTH_STATUS_COLORS] ||
                      HEALTH_STATUS_COLORS.healthy
                    }`}
                  />
                  <span className="text-lg font-medium">
                    {status ? getHealthStatusText(status.system_health.status) : "-"}
                  </span>
                  <span className="text-sm text-gray-500">
                    {status
                      ? new Date(status.system_health.timestamp).toLocaleString("zh-TW")
                      : "-"}
                  </span>
                </div>
                <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
                  {status &&
                    Object.entries(status.system_health.checks).map(([key, value]) => (
                      <div key={key} className="rounded-md bg-gray-50 p-3">
                        <div className="text-sm font-medium text-gray-700">
                          {key === "database" ? "資料庫" : key === "redis" ? "Redis" : "AI 服務"}
                        </div>
                        <div className="mt-1 text-sm text-gray-600">{value}</div>
                      </div>
                    ))}
                </div>
              </div>

              {/* 統計卡片（符合 AC-027-2：儀表板必須顯示所有必要資訊） */}
              <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                {/* 最近收集的威脅數量 */}
                <div className="rounded-lg border border-gray-200 bg-white p-6">
                  <h3 className="text-sm font-medium text-gray-500">最近收集的威脅數量</h3>
                  <div className="mt-2">
                    <div className="text-2xl font-bold text-gray-900">
                      {status?.recent_threat_count.last_24_hours || 0}
                    </div>
                    <div className="text-sm text-gray-600">過去 24 小時</div>
                  </div>
                  <div className="mt-4">
                    <div className="text-lg font-semibold text-gray-900">
                      {status?.recent_threat_count.last_7_days || 0}
                    </div>
                    <div className="text-sm text-gray-600">過去 7 天</div>
                  </div>
                </div>

                {/* 待處理的嚴重威脅數量 */}
                <div className="rounded-lg border border-gray-200 bg-white p-6">
                  <h3 className="text-sm font-medium text-gray-500">待處理的嚴重威脅</h3>
                  <div className="mt-2">
                    <div className="text-2xl font-bold text-red-600">
                      {status?.critical_threat_count || 0}
                    </div>
                    <div className="text-sm text-gray-600">風險分數 ≥ 8.0</div>
                  </div>
                </div>

                {/* 威脅情資來源狀態 */}
                <div className="rounded-lg border border-gray-200 bg-white p-6">
                  <h3 className="text-sm font-medium text-gray-500">威脅情資來源狀態</h3>
                  <div className="mt-2">
                    <div className="text-2xl font-bold text-gray-900">
                      {status?.threat_collection_status.length || 0}
                    </div>
                    <div className="text-sm text-gray-600">啟用的來源</div>
                  </div>
                  <div className="mt-4">
                    <div className="text-sm text-gray-600">
                      正常：{" "}
                      {status?.threat_collection_status.filter((s) => s.status === "healthy").length || 0}
                    </div>
                    <div className="text-sm text-yellow-600">
                      警告：{" "}
                      {status?.threat_collection_status.filter((s) => s.status === "warning").length || 0}
                    </div>
                    <div className="text-sm text-red-600">
                      錯誤：{" "}
                      {status?.threat_collection_status.filter((s) => s.status === "error").length || 0}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* 資產統計區塊 */}
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900">資產統計</h2>

              {/* 資產統計卡片 */}
              <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
                {/* 資產總數 */}
                <div className="rounded-lg border border-gray-200 bg-white p-6">
                  <h3 className="text-sm font-medium text-gray-500">資產總數</h3>
                  <div className="mt-2">
                    <div className="text-2xl font-bold text-gray-900">
                      {assetStatistics?.total_count || 0}
                    </div>
                    <div className="text-sm text-gray-600">筆資產</div>
                  </div>
                </div>

                {/* 受威脅影響的資產 */}
                <div className="rounded-lg border border-gray-200 bg-white p-6">
                  <h3 className="text-sm font-medium text-gray-500">受威脅影響的資產</h3>
                  <div className="mt-2">
                    <div className="text-2xl font-bold text-red-600">
                      {assetStatistics?.affected_assets.count || 0}
                    </div>
                    <div className="text-sm text-gray-600">
                      {assetStatistics?.affected_assets.percentage || 0}%
                    </div>
                  </div>
                </div>

                {/* 對外暴露資產 */}
                <div className="rounded-lg border border-gray-200 bg-white p-6">
                  <h3 className="text-sm font-medium text-gray-500">對外暴露資產</h3>
                  <div className="mt-2">
                    <div className="text-2xl font-bold text-yellow-600">
                      {assetStatistics?.public_facing_count || 0}
                    </div>
                    <div className="text-sm text-gray-600">需特別關注</div>
                  </div>
                </div>

                {/* 高敏感度資產 */}
                <div className="rounded-lg border border-gray-200 bg-white p-6">
                  <h3 className="text-sm font-medium text-gray-500">高敏感度資產</h3>
                  <div className="mt-2">
                    <div className="text-2xl font-bold text-orange-600">
                      {assetStatistics?.by_sensitivity["高"] || 0}
                    </div>
                    <div className="text-sm text-gray-600">資料敏感度高</div>
                  </div>
                </div>
              </div>

              {/* 資產分布圖表 */}
              <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                {/* 依資產類型統計 */}
                <div className="rounded-lg border border-gray-200 bg-white p-6">
                  <h3 className="mb-4 text-lg font-semibold text-gray-900">依資產類型統計</h3>
                  {assetStatistics && Object.keys(assetStatistics.by_type).length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={Object.entries(assetStatistics.by_type).map(([name, count]) => ({ name: name || "未知", count }))}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                        <YAxis tick={{ fontSize: 10 }} />
                        <Tooltip />
                        <Bar dataKey="count" fill="#3B82F6" name="資產數量" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex h-[250px] items-center justify-center text-gray-500">
                      沒有資料
                    </div>
                  )}
                </div>

                {/* 依資料敏感度統計 */}
                <div className="rounded-lg border border-gray-200 bg-white p-6">
                  <h3 className="mb-4 text-lg font-semibold text-gray-900">依資料敏感度統計</h3>
                  {assetStatistics && Object.keys(assetStatistics.by_sensitivity).length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie
                          data={Object.entries(assetStatistics.by_sensitivity).map(([name, value]) => ({
                            name,
                            value,
                            color: name === "高" ? "#DC2626" : name === "中" ? "#F59E0B" : "#10B981",
                          }))}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          outerRadius={70}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {Object.entries(assetStatistics.by_sensitivity).map(([name], index) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={name === "高" ? "#DC2626" : name === "中" ? "#F59E0B" : "#10B981"}
                            />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex h-[250px] items-center justify-center text-gray-500">
                      沒有資料
                    </div>
                  )}
                </div>

                {/* 依業務關鍵性統計 */}
                <div className="rounded-lg border border-gray-200 bg-white p-6">
                  <h3 className="mb-4 text-lg font-semibold text-gray-900">依業務關鍵性統計</h3>
                  {assetStatistics && Object.keys(assetStatistics.by_criticality).length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie
                          data={Object.entries(assetStatistics.by_criticality).map(([name, value]) => ({
                            name,
                            value,
                            color: name === "高" ? "#DC2626" : name === "中" ? "#F59E0B" : "#10B981",
                          }))}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          outerRadius={70}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {Object.entries(assetStatistics.by_criticality).map(([name], index) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={name === "高" ? "#DC2626" : name === "中" ? "#F59E0B" : "#10B981"}
                            />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex h-[250px] items-center justify-center text-gray-500">
                      沒有資料
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 威脅統計區塊（AC-028-1：提供威脅情資的統計圖表） */}
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-900">威脅統計</h2>
                <button
                  onClick={handleExportAllPDF}
                  disabled={exporting}
                  className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                >
                  {exporting ? "匯出中..." : "匯出所有圖表為 PDF"}
                </button>
              </div>

              {/* 威脅數量趨勢圖表 */}
              <div className="rounded-lg border border-gray-200 bg-white p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">威脅數量趨勢</h3>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleExportPNG("threat-trend-chart", "威脅數量趨勢")}
                      disabled={exporting || !threatTrend || threatTrend.data.length === 0}
                      className="rounded-md bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                    >
                      PNG
                    </button>
                    <button
                      onClick={() => handleExportPDF("threat-trend-chart", "威脅數量趨勢", "威脅數量趨勢")}
                      disabled={exporting || !threatTrend || threatTrend.data.length === 0}
                      className="rounded-md bg-red-600 px-3 py-1 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
                    >
                      PDF
                    </button>
                  </div>
                </div>
                <div id="threat-trend-chart">
                  {threatTrend && threatTrend.data.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart data={threatTrend.data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="date"
                          tick={{ fontSize: 12 }}
                          angle={-45}
                          textAnchor="end"
                          height={80}
                        />
                        <YAxis tick={{ fontSize: 12 }} />
                        <Tooltip />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="count"
                          stroke="#3B82F6"
                          strokeWidth={2}
                          name="威脅數量"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex h-[300px] items-center justify-center text-gray-500">
                      沒有資料
                    </div>
                  )}
                </div>
              </div>

              {/* 風險分數分布圖表 */}
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <div className="rounded-lg border border-gray-200 bg-white p-6">
                  <div className="mb-4 flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900">風險分數分布</h3>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleExportPNG("risk-distribution-chart", "風險分數分布")}
                        disabled={exporting || !riskDistribution || riskDistribution.total === 0}
                        className="rounded-md bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                      >
                        PNG
                      </button>
                      <button
                        onClick={() => handleExportPDF("risk-distribution-chart", "風險分數分布", "風險分數分布")}
                        disabled={exporting || !riskDistribution || riskDistribution.total === 0}
                        className="rounded-md bg-red-600 px-3 py-1 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
                      >
                        PDF
                      </button>
                    </div>
                  </div>
                  <div id="risk-distribution-chart">
                    {riskDistribution && riskDistribution.total > 0 ? (
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={prepareRiskDistributionData()}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {prepareRiskDistributionData().map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex h-[300px] items-center justify-center text-gray-500">
                        沒有資料
                      </div>
                    )}
                  </div>
                </div>

                {/* 受影響資產統計圖表 */}
                <div className="rounded-lg border border-gray-200 bg-white p-6">
                  <div className="mb-4 flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-900">受影響資產統計（依類型）</h3>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleExportPNG("affected-assets-chart", "受影響資產統計")}
                        disabled={exporting || !affectedAssets || Object.keys(affectedAssets.by_type).length === 0}
                        className="rounded-md bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                      >
                        PNG
                      </button>
                      <button
                        onClick={() => handleExportPDF("affected-assets-chart", "受影響資產統計", "受影響資產統計")}
                        disabled={exporting || !affectedAssets || Object.keys(affectedAssets.by_type).length === 0}
                        className="rounded-md bg-red-600 px-3 py-1 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
                      >
                        PDF
                      </button>
                    </div>
                  </div>
                  <div id="affected-assets-chart">
                    {affectedAssets && Object.keys(affectedAssets.by_type).length > 0 ? (
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={prepareAffectedAssetsData()}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                          <YAxis tick={{ fontSize: 12 }} />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="count" fill="#3B82F6" name="受影響資產數量" />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="flex h-[300px] items-center justify-center text-gray-500">
                        沒有資料
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* 威脅來源統計圖表 */}
              <div className="rounded-lg border border-gray-200 bg-white p-6">
                <div className="mb-4 flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">威脅來源統計</h3>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleExportPNG("threat-sources-chart", "威脅來源統計")}
                      disabled={exporting || !threatSources || threatSources.data.length === 0}
                      className="rounded-md bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                    >
                      PNG
                    </button>
                    <button
                      onClick={() => handleExportPDF("threat-sources-chart", "威脅來源統計", "威脅來源統計")}
                      disabled={exporting || !threatSources || threatSources.data.length === 0}
                      className="rounded-md bg-red-600 px-3 py-1 text-xs font-medium text-white hover:bg-red-700 disabled:opacity-50"
                    >
                      PDF
                    </button>
                  </div>
                </div>
                <div id="threat-sources-chart">
                  {threatSources && threatSources.data.length > 0 ? (
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={prepareThreatSourcesData()} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" tick={{ fontSize: 12 }} />
                        <YAxis
                          dataKey="name"
                          type="category"
                          tick={{ fontSize: 12 }}
                          width={150}
                        />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="count" fill="#3B82F6" name="威脅數量" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex h-[400px] items-center justify-center text-gray-500">
                      沒有資料
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 威脅情資收集狀態（符合 AC-027-2：威脅情資收集狀態） */}
            {status && status.threat_collection_status.length > 0 && (
              <div className="rounded-lg border border-gray-200 bg-white p-6">
                <h2 className="mb-4 text-xl font-semibold text-gray-900">威脅情資收集狀態</h2>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                          來源名稱
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                          優先級
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                          收集頻率
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                          最後收集時間
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                          狀態
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 bg-white">
                      {status.threat_collection_status.map((feed) => (
                        <tr key={feed.feed_id}>
                          <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-gray-900">
                            {feed.feed_name}
                          </td>
                          <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                            {feed.priority}
                          </td>
                          <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                            {feed.collection_frequency}
                          </td>
                          <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                            {formatTime(feed.last_collection_time)}
                          </td>
                          <td className="whitespace-nowrap px-6 py-4 text-sm">
                            <span
                              className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                                STATUS_COLORS[feed.status] || STATUS_COLORS.unknown
                              }`}
                            >
                              {getStatusText(feed.status)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* 告警訊息（符合 AC-027-4：系統異常時顯示告警訊息） */}
            {status &&
              (status.system_health.status === "unhealthy" ||
                status.system_health.status === "degraded" ||
                status.threat_collection_status.some((s) => s.status === "error")) && (
                <div className="rounded-lg border border-red-300 bg-red-50 p-6">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg
                        className="h-5 w-5 text-red-400"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                          clipRule="evenodd"
                        />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-red-800">系統告警</h3>
                      <div className="mt-2 text-sm text-red-700">
                        <ul className="list-disc space-y-1 pl-5">
                          {status.system_health.status === "unhealthy" && (
                            <li>系統健康狀態異常，請檢查服務連線</li>
                          )}
                          {status.system_health.status === "degraded" && (
                            <li>系統部分服務降級，請檢查非關鍵服務</li>
                          )}
                          {status.threat_collection_status
                            .filter((s) => s.status === "error")
                            .map((s) => (
                              <li key={s.feed_id}>
                                威脅情資來源「{s.feed_name}」收集失敗
                              </li>
                            ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              )}
          </div>
        )}
      </div>
    </PermissionGate>
  );
}
