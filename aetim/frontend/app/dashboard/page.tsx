/**
 * 系統狀態儀表板頁面
 * 
 * 顯示系統狀態資訊。
 * 符合 AC-027-1, AC-027-2, AC-027-4。
 */

"use client";

import React, { useState, useEffect } from "react";
import { usePermission } from "@/hooks/usePermission";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { getSystemStatus, type SystemStatus } from "@/lib/api/system_status";

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

export default function DashboardPage() {
  const { hasPermission } = usePermission();
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    loadSystemStatus();
    
    // 自動刷新（每 30 秒）
    const interval = setInterval(() => {
      if (autoRefresh) {
        loadSystemStatus();
      }
    }, 30000);
    
    return () => clearInterval(interval);
  }, [autoRefresh]);

  /**
   * 載入系統狀態
   */
  const loadSystemStatus = async () => {
    try {
      setError(null);
      const data = await getSystemStatus();
      setStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入系統狀態失敗");
    } finally {
      setLoading(false);
    }
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

  return (
    <PermissionGate permissions={["system_config:view"]}>
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">系統狀態儀表板</h1>
            <p className="mt-2 text-gray-600">
              監控系統運作狀況（符合 AC-027-1：提供儀表板顯示系統狀態）
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
              onClick={loadSystemStatus}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              重新整理
            </button>
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
        ) : status ? (
          <div className="space-y-6">
            {/* 系統健康狀態卡片 */}
            <div className="rounded-lg border border-gray-200 bg-white p-6">
              <h2 className="mb-4 text-xl font-semibold text-gray-900">系統健康狀態</h2>
              <div className="flex items-center space-x-4">
                <div
                  className={`h-4 w-4 rounded-full ${
                    HEALTH_STATUS_COLORS[status.system_health.status as keyof typeof HEALTH_STATUS_COLORS] ||
                    HEALTH_STATUS_COLORS.unknown
                  }`}
                />
                <span className="text-lg font-medium">
                  {getHealthStatusText(status.system_health.status)}
                </span>
                <span className="text-sm text-gray-500">
                  {new Date(status.system_health.timestamp).toLocaleString("zh-TW")}
                </span>
              </div>
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
                {Object.entries(status.system_health.checks).map(([key, value]) => (
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
                    {status.recent_threat_count.last_24_hours}
                  </div>
                  <div className="text-sm text-gray-600">過去 24 小時</div>
                </div>
                <div className="mt-4">
                  <div className="text-lg font-semibold text-gray-900">
                    {status.recent_threat_count.last_7_days}
                  </div>
                  <div className="text-sm text-gray-600">過去 7 天</div>
                </div>
              </div>

              {/* 待處理的嚴重威脅數量 */}
              <div className="rounded-lg border border-gray-200 bg-white p-6">
                <h3 className="text-sm font-medium text-gray-500">待處理的嚴重威脅</h3>
                <div className="mt-2">
                  <div className="text-2xl font-bold text-red-600">
                    {status.critical_threat_count}
                  </div>
                  <div className="text-sm text-gray-600">風險分數 ≥ 8.0</div>
                </div>
              </div>

              {/* 威脅情資來源狀態 */}
              <div className="rounded-lg border border-gray-200 bg-white p-6">
                <h3 className="text-sm font-medium text-gray-500">威脅情資來源狀態</h3>
                <div className="mt-2">
                  <div className="text-2xl font-bold text-gray-900">
                    {status.threat_collection_status.length}
                  </div>
                  <div className="text-sm text-gray-600">啟用的來源</div>
                </div>
                <div className="mt-4">
                  <div className="text-sm text-gray-600">
                    正常：{" "}
                    {
                      status.threat_collection_status.filter((s) => s.status === "healthy")
                        .length
                    }
                  </div>
                  <div className="text-sm text-yellow-600">
                    警告：{" "}
                    {
                      status.threat_collection_status.filter((s) => s.status === "warning")
                        .length
                    }
                  </div>
                  <div className="text-sm text-red-600">
                    錯誤：{" "}
                    {
                      status.threat_collection_status.filter((s) => s.status === "error")
                        .length
                    }
                  </div>
                </div>
              </div>
            </div>

            {/* 威脅情資收集狀態（符合 AC-027-2：威脅情資收集狀態） */}
            <div className="rounded-lg border border-gray-200 bg-white p-6">
              <h2 className="mb-4 text-xl font-semibold text-gray-900">
                威脅情資收集狀態
              </h2>
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

            {/* 告警訊息（符合 AC-027-4：系統異常時顯示告警訊息） */}
            {(status.system_health.status === "unhealthy" ||
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
        ) : null}
      </div>
    </PermissionGate>
  );
}

