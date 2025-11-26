/**
 * 報告清單頁面
 */

"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Pagination } from "@/components/ui/Pagination";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Table } from "@/components/ui/Table";
import {
  getReports,
  downloadReport,
  type Report,
  type ReportSearchParams,
  type ReportType,
  type FileFormat,
} from "@/lib/api/report";
import { debounce } from "@/lib/utils/debounce";

export default function ReportsPage() {
  const router = useRouter();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [sortBy, setSortBy] = useState<string>("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // 搜尋狀態
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);

  // 篩選狀態
  const [filters, setFilters] = useState<ReportSearchParams>({
    report_type: undefined,
    file_format: undefined,
    start_date: undefined,
    end_date: undefined,
  });

  // 統計資訊
  const [statistics, setStatistics] = useState<{
    total: number;
    byType: Record<string, number>;
    byFormat: Record<string, number>;
  } | null>(null);

  // 載入報告清單
  const loadReports = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: ReportSearchParams = {
        page,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder,
        ...filters,
      };

      const response = await getReports(params);
      
      // 如果沒有搜尋條件，計算統計資訊
      if (!searchQuery.trim()) {
        calculateStatistics(response.items);
      }
      
      // 如果有搜尋條件，進行前端篩選
      let filteredItems = response.items;
      if (searchQuery.trim()) {
        filteredItems = response.items.filter((report) =>
          report.title.toLowerCase().includes(searchQuery.toLowerCase())
        );
      }
      
      setReports(filteredItems);
      setTotalCount(filteredItems.length);
      setTotalPages(Math.ceil(filteredItems.length / pageSize));
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入報告失敗");
    } finally {
      setLoading(false);
      setIsSearching(false);
    }
  };

  // 計算統計資訊
  const calculateStatistics = (items: Report[]) => {
    const byType: Record<string, number> = {};
    const byFormat: Record<string, number> = {};

    items.forEach((report) => {
      // 統計報告類型
      const typeKey = report.report_type;
      byType[typeKey] = (byType[typeKey] || 0) + 1;

      // 統計檔案格式
      const formatKey = report.file_format;
      byFormat[formatKey] = (byFormat[formatKey] || 0) + 1;
    });

    setStatistics({
      total: items.length,
      byType,
      byFormat,
    });
  };

  useEffect(() => {
    loadReports();
  }, [page, sortBy, sortOrder, filters]);

  // Debounced 搜尋函數
  const debouncedSearch = useMemo(
    () =>
      debounce(async (query: string) => {
        setIsSearching(true);
        try {
          setLoading(true);
          setError(null);

          const params: ReportSearchParams = {
            page: 1,
            page_size: pageSize,
            sort_by: sortBy,
            sort_order: sortOrder,
            ...filters,
          };

          const response = await getReports(params);
          
          // 進行前端篩選
          const filteredItems = response.items.filter((report) =>
            report.title.toLowerCase().includes(query.toLowerCase())
          );
          
          setReports(filteredItems);
          setTotalCount(filteredItems.length);
          setTotalPages(Math.ceil(filteredItems.length / pageSize));
        } catch (err) {
          setError(err instanceof Error ? err.message : "搜尋報告失敗");
        } finally {
          setLoading(false);
          setIsSearching(false);
        }
      }, 300),
    [pageSize, sortBy, sortOrder, filters]
  );

  // 處理搜尋
  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    if (value.trim()) {
      debouncedSearch(value);
    } else {
      setPage(1);
      loadReports();
    }
  };

  // 處理排序
  const handleSort = (key: string, order: "asc" | "desc") => {
    setSortBy(key);
    setSortOrder(order);
    setPage(1);
  };

  // 處理篩選
  const handleFilterChange = (key: keyof ReportSearchParams, value: any) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(1);
  };

  // 處理下載
  const handleDownload = async (reportId: string, format?: FileFormat) => {
    try {
      const blob = await downloadReport(reportId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `report-${reportId}.${format?.toLowerCase() || "html"}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(err instanceof Error ? err.message : "下載報告失敗");
    }
  };

  // 表格標題
  const tableHeaders = [
    { key: "title", label: "標題", sortable: true },
    { key: "report_type", label: "類型", sortable: true },
    { key: "file_format", label: "格式", sortable: true },
    { key: "created_at", label: "生成時間", sortable: true },
    { key: "actions", label: "操作", sortable: false },
  ];

  // 格式化報告類型
  const formatReportType = (type: ReportType): string => {
    const types: Record<ReportType, string> = {
      CISO_Weekly: "CISO 週報",
      IT_Ticket: "IT 工單",
    };
    return types[type] || type;
  };

  // 格式化檔案格式
  const formatFileFormat = (format: FileFormat): string => {
    return format;
  };

  // 格式化日期
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString("zh-TW", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">歷史報告檢視</h1>
        <Button
          onClick={() => router.push("/reports/generate")}
          className="bg-blue-600 text-white hover:bg-blue-700"
        >
          生成報告
        </Button>
      </div>

      {/* 報告統計 */}
      {statistics && !loading && (
        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="rounded-lg bg-white p-6 shadow">
            <h3 className="mb-2 text-sm font-medium text-gray-700">報告總數</h3>
            <p className="text-3xl font-bold text-blue-600">{statistics.total}</p>
          </div>
          <div className="rounded-lg bg-white p-6 shadow">
            <h3 className="mb-2 text-sm font-medium text-gray-700">報告類型分布</h3>
            <div className="mt-2 space-y-1">
              {Object.entries(statistics.byType).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">
                    {formatReportType(type as ReportType)}
                  </span>
                  <span className="text-sm font-semibold text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-lg bg-white p-6 shadow">
            <h3 className="mb-2 text-sm font-medium text-gray-700">檔案格式分布</h3>
            <div className="mt-2 space-y-1">
              {Object.entries(statistics.byFormat).map(([format, count]) => (
                <div key={format} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">{format}</span>
                  <span className="text-sm font-semibold text-gray-900">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 搜尋與篩選區域 */}
      <div className="mb-6 rounded-lg bg-white p-4 shadow">
        {/* 搜尋框 */}
        <div className="mb-4">
          <label className="mb-2 block text-sm font-medium text-gray-700">
            搜尋報告標題
          </label>
          <Input
            type="text"
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder="輸入報告標題關鍵字..."
            className="w-full"
          />
          {isSearching && (
            <p className="mt-1 text-sm text-gray-500">搜尋中...</p>
          )}
        </div>

        {/* 篩選選項 */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              報告類型
            </label>
            <Select
              value={filters.report_type || ""}
              onChange={(e) =>
                handleFilterChange("report_type", e.target.value || undefined)
              }
            >
              <option value="">全部</option>
              <option value="CISO_Weekly">CISO 週報</option>
              <option value="IT_Ticket">IT 工單</option>
            </Select>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              檔案格式
            </label>
            <Select
              value={filters.file_format || ""}
              onChange={(e) =>
                handleFilterChange("file_format", e.target.value || undefined)
              }
            >
              <option value="">全部</option>
              <option value="HTML">HTML</option>
              <option value="PDF">PDF</option>
              <option value="TEXT">TEXT</option>
              <option value="JSON">JSON</option>
            </Select>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              開始日期
            </label>
            <Input
              type="date"
              value={filters.start_date || ""}
              onChange={(e) =>
                handleFilterChange("start_date", e.target.value || undefined)
              }
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">
              結束日期
            </label>
            <Input
              type="date"
              value={filters.end_date || ""}
              onChange={(e) =>
                handleFilterChange("end_date", e.target.value || undefined)
              }
            />
          </div>
        </div>
      </div>

      {/* 錯誤訊息 */}
      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-4 text-red-800">{error}</div>
      )}

      {/* 報告表格 */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600">載入中...</p>
        </div>
      ) : (
        <>
          <div className="rounded-lg bg-white shadow">
            <Table
              headers={tableHeaders}
              data={reports.map((report) => ({
                id: report.id,
                title: report.title,
                report_type: formatReportType(report.report_type),
                file_format: formatFileFormat(report.file_format),
                created_at: formatDate(report.created_at),
                actions: (
                  <div className="flex gap-2">
                    <Button
                      onClick={() => router.push(`/reports/${report.id}`)}
                      className="bg-blue-600 text-white hover:bg-blue-700 text-sm px-3 py-1"
                    >
                      查看
                    </Button>
                    <Button
                      onClick={() => handleDownload(report.id)}
                      className="bg-green-600 text-white hover:bg-green-700 text-sm px-3 py-1"
                    >
                      下載
                    </Button>
                  </div>
                ),
              }))}
              onSort={handleSort}
              sortBy={sortBy}
              sortOrder={sortOrder}
              onRowClick={(row) => router.push(`/reports/${row.id}`)}
            />
          </div>

          {/* 分頁 */}
          {totalPages > 1 && (
            <div className="mt-6">
              <Pagination
                currentPage={page}
                totalPages={totalPages}
                totalItems={totalCount}
                onPageChange={setPage}
              />
            </div>
          )}
        </>
      )}
    </div>
  );
}

