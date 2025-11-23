/**
 * 威脅清單頁面
 */

"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Table } from "@/components/ui/Table";
import { Pagination } from "@/components/ui/Pagination";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import {
  getThreats,
  searchThreats,
  type Threat,
  type ThreatSearchParams,
} from "@/lib/api/threat";

export default function ThreatsPage() {
  const router = useRouter();
  const [threats, setThreats] = useState<Threat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [sortBy, setSortBy] = useState<string | undefined>("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // 搜尋與篩選狀態
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [filters, setFilters] = useState<ThreatSearchParams>({
    status: undefined,
    cve_id: undefined,
    product_name: undefined,
    min_cvss_score: undefined,
    max_cvss_score: undefined,
  });

  useEffect(() => {
    loadThreats();
  }, [page, sortBy, sortOrder, filters]);

  const loadThreats = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: ThreatSearchParams = {
        page,
        page_size: pageSize,
        sort_by: sortBy as any,
        sort_order: sortOrder,
        ...filters,
      };

      let response;
      if (isSearching && searchQuery.trim()) {
        response = await searchThreats(searchQuery, page, pageSize);
      } else {
        response = await getThreats(params);
      }

      setThreats(response.items);
      setTotalCount(response.total);
      setTotalPages(response.total_pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入威脅清單失敗");
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (key: string, order: "asc" | "desc") => {
    setSortBy(key);
    setSortOrder(order);
    setPage(1);
  };

  const handleRowClick = (row: Threat) => {
    router.push(`/threats/${row.id}`);
  };

  const handleSearch = () => {
    setIsSearching(true);
    setPage(1);
    loadThreats();
  };

  const handleClearSearch = () => {
    setSearchQuery("");
    setIsSearching(false);
    setPage(1);
    loadThreats();
  };

  const handleFilterChange = (key: keyof ThreatSearchParams, value: any) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value || undefined,
    }));
    setPage(1);
  };

  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case "Critical":
        return "bg-red-100 text-red-800";
      case "High":
        return "bg-orange-100 text-orange-800";
      case "Medium":
        return "bg-yellow-100 text-yellow-800";
      case "Low":
        return "bg-green-100 text-green-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "New":
        return "bg-blue-100 text-blue-800";
      case "Analyzing":
        return "bg-yellow-100 text-yellow-800";
      case "Processed":
        return "bg-green-100 text-green-800";
      case "Closed":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">威脅清單</h1>
      </div>

      {/* 搜尋與篩選區域 */}
      <div className="mb-6 rounded-lg border border-gray-200 bg-white p-4 shadow">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {/* 搜尋框 */}
          <div className="lg:col-span-2">
            <Input
              label="搜尋威脅"
              id="search"
              name="search"
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="輸入關鍵字搜尋標題或描述..."
              onKeyPress={(e) => {
                if (e.key === "Enter") {
                  handleSearch();
                }
              }}
            />
          </div>

          {/* 狀態篩選 */}
          <div>
            <Select
              label="狀態"
              id="status"
              name="status"
              value={filters.status || ""}
              onChange={(e) => handleFilterChange("status", e.target.value || undefined)}
              options={[
                { value: "", label: "全部" },
                { value: "New", label: "新增" },
                { value: "Analyzing", label: "分析中" },
                { value: "Processed", label: "已處理" },
                { value: "Closed", label: "已關閉" },
              ]}
            />
          </div>

          {/* CVSS 分數篩選 */}
          <div>
            <Select
              label="CVSS 分數"
              id="cvss_filter"
              name="cvss_filter"
              value={
                filters.min_cvss_score !== undefined
                  ? `min_${filters.min_cvss_score}`
                  : filters.max_cvss_score !== undefined
                    ? `max_${filters.max_cvss_score}`
                    : ""
              }
              onChange={(e) => {
                const value = e.target.value;
                if (value.startsWith("min_")) {
                  handleFilterChange("min_cvss_score", parseFloat(value.replace("min_", "")));
                  handleFilterChange("max_cvss_score", undefined);
                } else if (value.startsWith("max_")) {
                  handleFilterChange("max_cvss_score", parseFloat(value.replace("max_", "")));
                  handleFilterChange("min_cvss_score", undefined);
                } else {
                  handleFilterChange("min_cvss_score", undefined);
                  handleFilterChange("max_cvss_score", undefined);
                }
              }}
              options={[
                { value: "", label: "全部" },
                { value: "min_7.0", label: "高風險 (≥7.0)" },
                { value: "min_4.0", label: "中風險 (≥4.0)" },
                { value: "max_3.9", label: "低風險 (≤3.9)" },
              ]}
            />
          </div>
        </div>

        <div className="mt-4 flex space-x-2">
          <Button onClick={handleSearch} isLoading={loading}>
            搜尋
          </Button>
          {isSearching && (
            <Button variant="outline" onClick={handleClearSearch}>
              清除搜尋
            </Button>
          )}
        </div>
      </div>

      {/* 錯誤訊息 */}
      {error && (
        <div className="mb-4 rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* 威脅表格 */}
      {loading ? (
        <div className="text-center text-gray-500">載入中...</div>
      ) : threats.length > 0 ? (
        <>
          <div className="mb-4 overflow-x-auto rounded-lg border border-gray-200 bg-white shadow">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort("cve_id", sortBy === "cve_id" && sortOrder === "asc" ? "desc" : "asc")}
                  >
                    CVE 編號
                    {sortBy === "cve_id" && (
                      <span className="ml-1">{sortOrder === "asc" ? "↑" : "↓"}</span>
                    )}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    標題
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    嚴重程度
                  </th>
                  <th
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() =>
                      handleSort(
                        "cvss_base_score",
                        sortBy === "cvss_base_score" && sortOrder === "asc" ? "desc" : "asc",
                      )
                    }
                  >
                    CVSS 分數
                    {sortBy === "cvss_base_score" && (
                      <span className="ml-1">{sortOrder === "asc" ? "↑" : "↓"}</span>
                    )}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    狀態
                  </th>
                  <th
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() =>
                      handleSort(
                        "created_at",
                        sortBy === "created_at" && sortOrder === "asc" ? "desc" : "asc",
                      )
                    }
                  >
                    收集時間
                    {sortBy === "created_at" && (
                      <span className="ml-1">{sortOrder === "asc" ? "↑" : "↓"}</span>
                    )}
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {threats.map((threat) => (
                  <tr
                    key={threat.id}
                    className="cursor-pointer hover:bg-gray-50"
                    onClick={() => handleRowClick(threat)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {threat.cve_id || "-"}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <div className="max-w-md truncate" title={threat.title}>
                        {threat.title}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {threat.severity && (
                        <span
                          className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getSeverityColor(threat.severity)}`}
                        >
                          {threat.severity}
                        </span>
                      )}
                      {!threat.severity && <span className="text-sm text-gray-500">-</span>}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {threat.cvss_base_score?.toFixed(1) || "-"}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getStatusColor(threat.status)}`}
                      >
                        {threat.status === "New"
                          ? "新增"
                          : threat.status === "Analyzing"
                            ? "分析中"
                            : threat.status === "Processed"
                              ? "已處理"
                              : "已關閉"}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {threat.collected_at
                        ? new Date(threat.collected_at).toLocaleString("zh-TW")
                        : "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 分頁控制 */}
          {totalPages > 0 && (
            <div className="mt-4">
              <Pagination
                currentPage={page}
                totalPages={totalPages}
                pageSize={pageSize}
                totalCount={totalCount}
                onPageChange={setPage}
              />
            </div>
          )}
        </>
      ) : (
        <div className="rounded-lg border border-gray-200 bg-white p-8 text-center shadow">
          <p className="text-gray-500">目前沒有威脅資料</p>
        </div>
      )}
    </div>
  );
}

