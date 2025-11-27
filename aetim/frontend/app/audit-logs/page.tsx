/**
 * 稽核日誌查詢介面
 * 
 * 提供稽核日誌的查詢、篩選、排序和匯出功能。
 * 符合 AC-027-1, AC-027-2, AC-027-3, AC-027-4。
 */

"use client";

import React, { useState, useEffect } from "react";
import { usePermission } from "@/hooks/usePermission";
import { PermissionGate } from "@/components/auth/PermissionGate";
import { getAuditLogs, exportAuditLogsCSV, exportAuditLogsJSON } from "@/lib/api/audit_log";
import type { AuditLog, AuditLogFilterParams } from "@/types/audit_log";

// 操作類型選項
const ACTION_OPTIONS = [
  { value: "", label: "全部" },
  { value: "CREATE", label: "建立" },
  { value: "UPDATE", label: "更新" },
  { value: "DELETE", label: "刪除" },
  { value: "IMPORT", label: "匯入" },
  { value: "VIEW", label: "檢視" },
  { value: "TOGGLE", label: "切換" },
  { value: "EXPORT", label: "匯出" },
  { value: "LOGIN", label: "登入" },
  { value: "LOGOUT", label: "登出" },
];

// 資源類型選項
const RESOURCE_TYPE_OPTIONS = [
  { value: "", label: "全部" },
  { value: "Asset", label: "資產" },
  { value: "PIR", label: "優先情資需求" },
  { value: "ThreatFeed", label: "威脅情資來源" },
  { value: "Threat", label: "威脅" },
  { value: "Report", label: "報告" },
  { value: "NotificationRule", label: "通知規則" },
  { value: "SystemConfiguration", label: "系統設定" },
  { value: "User", label: "使用者" },
];

export default function AuditLogsPage() {
  const { hasPermission } = usePermission();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [sortBy, setSortBy] = useState<string>("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [exporting, setExporting] = useState(false);

  // 篩選條件
  const [filters, setFilters] = useState<AuditLogFilterParams>({
    action: "",
    resource_type: "",
    user_id: "",
    start_date: "",
    end_date: "",
  });

  useEffect(() => {
    loadAuditLogs();
  }, [currentPage, pageSize, sortBy, sortOrder, filters]);

  /**
   * 載入稽核日誌
   */
  const loadAuditLogs = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: AuditLogFilterParams = {
        ...filters,
        page: currentPage,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder,
      };

      // 移除空值
      Object.keys(params).forEach((key) => {
        if (params[key as keyof AuditLogFilterParams] === "") {
          delete params[key as keyof AuditLogFilterParams];
        }
      });

      const response = await getAuditLogs(params);
      setLogs(response.data);
      setTotalCount(response.total_count);
      setTotalPages(response.total_pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入稽核日誌失敗");
    } finally {
      setLoading(false);
    }
  };

  /**
   * 處理篩選變更
   */
  const handleFilterChange = (key: keyof AuditLogFilterParams, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setCurrentPage(1); // 重置到第一頁
  };

  /**
   * 處理排序變更
   */
  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
  };

  /**
   * 匯出為 CSV
   */
  const handleExportCSV = async () => {
    try {
      setExporting(true);
      const blob = await exportAuditLogsCSV(filters);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit_logs_${new Date().toISOString().split("T")[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "匯出失敗");
    } finally {
      setExporting(false);
    }
  };

  /**
   * 匯出為 JSON
   */
  const handleExportJSON = async () => {
    try {
      setExporting(true);
      const blob = await exportAuditLogsJSON(filters);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit_logs_${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "匯出失敗");
    } finally {
      setExporting(false);
    }
  };

  /**
   * 格式化時間
   */
  const formatTime = (timeStr: string) => {
    const date = new Date(timeStr);
    return date.toLocaleString("zh-TW");
  };

  /**
   * 格式化操作類型
   */
  const formatAction = (action: string) => {
    const actionMap: Record<string, string> = {
      CREATE: "建立",
      UPDATE: "更新",
      DELETE: "刪除",
      IMPORT: "匯入",
      VIEW: "檢視",
      TOGGLE: "切換",
      EXPORT: "匯出",
      LOGIN: "登入",
      LOGOUT: "登出",
    };
    return actionMap[action] || action;
  };

  return (
    <PermissionGate permissions={["audit_log:view"]}>
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">稽核日誌查詢</h1>
            <p className="mt-2 text-gray-600">查詢與匯出系統操作記錄</p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={handleExportCSV}
              disabled={exporting}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              {exporting ? "匯出中..." : "匯出 CSV"}
            </button>
            <button
              onClick={handleExportJSON}
              disabled={exporting}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {exporting ? "匯出中..." : "匯出 JSON"}
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

        {/* 篩選條件 */}
        <div className="mb-6 rounded-lg border border-gray-200 bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">篩選條件</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
            {/* 操作類型 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">操作類型</label>
              <select
                value={filters.action || ""}
                onChange={(e) => handleFilterChange("action", e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500"
              >
                {ACTION_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* 資源類型 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">資源類型</label>
              <select
                value={filters.resource_type || ""}
                onChange={(e) => handleFilterChange("resource_type", e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500"
              >
                {RESOURCE_TYPE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* 使用者 ID */}
            <div>
              <label className="block text-sm font-medium text-gray-700">使用者 ID</label>
              <input
                type="text"
                value={filters.user_id || ""}
                onChange={(e) => handleFilterChange("user_id", e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500"
                placeholder="輸入使用者 ID"
              />
            </div>

            {/* 開始日期 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">開始日期</label>
              <input
                type="date"
                value={filters.start_date || ""}
                onChange={(e) => handleFilterChange("start_date", e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500"
              />
            </div>

            {/* 結束日期 */}
            <div>
              <label className="block text-sm font-medium text-gray-700">結束日期</label>
              <input
                type="date"
                value={filters.end_date || ""}
                onChange={(e) => handleFilterChange("end_date", e.target.value)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        {/* 稽核日誌表格 */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
              <p className="mt-4 text-gray-600">載入中...</p>
            </div>
          </div>
        ) : (
          <div className="rounded-lg border border-gray-200 bg-white">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th
                      className="cursor-pointer px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 hover:bg-gray-100"
                      onClick={() => handleSort("created_at")}
                    >
                      時間{" "}
                      {sortBy === "created_at" && (sortOrder === "asc" ? "↑" : "↓")}
                    </th>
                    <th
                      className="cursor-pointer px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 hover:bg-gray-100"
                      onClick={() => handleSort("action")}
                    >
                      操作類型{" "}
                      {sortBy === "action" && (sortOrder === "asc" ? "↑" : "↓")}
                    </th>
                    <th
                      className="cursor-pointer px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 hover:bg-gray-100"
                      onClick={() => handleSort("resource_type")}
                    >
                      資源類型{" "}
                      {sortBy === "resource_type" && (sortOrder === "asc" ? "↑" : "↓")}
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      資源 ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      使用者 ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                      IP 位址
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {logs.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-4 text-center text-sm text-gray-500">
                        沒有找到稽核日誌
                      </td>
                    </tr>
                  ) : (
                    logs.map((log) => (
                      <tr key={log.id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                          {formatTime(log.created_at)}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                          {formatAction(log.action)}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                          {log.resource_type}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                          {log.resource_id || "-"}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                          {log.user_id || "-"}
                        </td>
                        <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                          {log.ip_address || "-"}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* 分頁控制 */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6">
                <div className="flex flex-1 justify-between sm:hidden">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                  >
                    上一頁
                  </button>
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                  >
                    下一頁
                  </button>
                </div>
                <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm text-gray-700">
                      顯示 <span className="font-medium">{(currentPage - 1) * pageSize + 1}</span> 到{" "}
                      <span className="font-medium">
                        {Math.min(currentPage * pageSize, totalCount)}
                      </span>{" "}
                      筆，共 <span className="font-medium">{totalCount}</span> 筆
                    </p>
                  </div>
                  <div>
                    <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                      <button
                        onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                        disabled={currentPage === 1}
                        className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
                      >
                        上一頁
                      </button>
                      {Array.from({ length: totalPages }, (_, i) => i + 1)
                        .filter((page) => {
                          // 顯示當前頁前後各 2 頁
                          return (
                            page === 1 ||
                            page === totalPages ||
                            (page >= currentPage - 2 && page <= currentPage + 2)
                          );
                        })
                        .map((page, index, array) => {
                          // 處理省略號
                          if (index > 0 && page - array[index - 1] > 1) {
                            return (
                              <React.Fragment key={`ellipsis-${page}`}>
                                <span className="relative inline-flex items-center px-4 py-2 text-sm font-semibold text-gray-700 ring-1 ring-inset ring-gray-300 focus:z-20 focus:outline-offset-0">
                                  ...
                                </span>
                                <button
                                  onClick={() => setCurrentPage(page)}
                                  className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ${
                                    currentPage === page
                                      ? "z-10 bg-blue-600 text-white focus:z-20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
                                      : "text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0"
                                  }`}
                                >
                                  {page}
                                </button>
                              </React.Fragment>
                            );
                          }
                          return (
                            <button
                              key={page}
                              onClick={() => setCurrentPage(page)}
                              className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ${
                                currentPage === page
                                  ? "z-10 bg-blue-600 text-white focus:z-20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
                                  : "text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0"
                              }`}
                            >
                              {page}
                            </button>
                          );
                        })}
                      <button
                        onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                        disabled={currentPage === totalPages}
                        className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
                      >
                        下一頁
                      </button>
                    </nav>
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

