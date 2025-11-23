/**
 * 資產詳情頁面
 */

"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { getAsset, deleteAsset } from "@/lib/api/asset";
import { getAssetThreats } from "@/lib/api/association";
import type { Asset } from "@/types/asset";
import type {
  AssetThreatAssociationListResponse,
  AssetThreatAssociationParams,
} from "@/types/association";

export default function AssetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const assetId = params.id as string;

  const [asset, setAsset] = useState<Asset | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [threatAssociations, setThreatAssociations] =
    useState<AssetThreatAssociationListResponse | null>(null);
  const [threatAssociationsLoading, setThreatAssociationsLoading] = useState(false);
  const [threatAssociationParams, setThreatAssociationParams] = useState<AssetThreatAssociationParams>(
    {
      page: 1,
      page_size: 20,
      sort_by: "match_confidence",
      sort_order: "desc",
    },
  );

  useEffect(() => {
    if (assetId) {
      loadAsset();
      loadThreatAssociations();
    }
  }, [assetId]);

  useEffect(() => {
    if (assetId) {
      loadThreatAssociations();
    }
  }, [assetId, threatAssociationParams]);

  const loadAsset = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAsset(assetId);
      setAsset(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入資產詳情失敗");
    } finally {
      setLoading(false);
    }
  };

  const loadThreatAssociations = async () => {
    try {
      setThreatAssociationsLoading(true);
      const data = await getAssetThreats(assetId, threatAssociationParams);
      setThreatAssociations(data);
    } catch (err) {
      console.error("載入關聯威脅失敗：", err);
    } finally {
      setThreatAssociationsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!asset) return;

    try {
      setIsDeleting(true);
      await deleteAsset(asset.id, true);
      router.push("/assets");
    } catch (err) {
      setError(err instanceof Error ? err.message : "刪除資產失敗");
    } finally {
      setIsDeleting(false);
      setShowDeleteModal(false);
    }
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

  const getStatusColor = (status?: string) => {
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

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-gray-500">載入中...</div>
      </div>
    );
  }

  if (error || !asset) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error || "資產不存在"}</p>
        </div>
        <Button variant="outline" onClick={() => router.push("/assets")} className="mt-4">
          返回清單
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">資產詳情</h1>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => router.push("/assets")}>
            返回清單
          </Button>
          <Button variant="outline" onClick={() => router.push(`/assets/${asset.id}/edit`)}>
            編輯
          </Button>
          <Button variant="danger" onClick={() => setShowDeleteModal(true)}>
            刪除
          </Button>
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div>
            <h2 className="mb-4 text-lg font-semibold text-gray-900">基本資訊</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">主機名稱</dt>
                <dd className="mt-1 text-sm text-gray-900">{asset.host_name}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">IP 位址</dt>
                <dd className="mt-1 text-sm text-gray-900">{asset.ip || "-"}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">作業系統</dt>
                <dd className="mt-1 text-sm text-gray-900">{asset.operating_system}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">負責人</dt>
                <dd className="mt-1 text-sm text-gray-900">{asset.owner}</dd>
              </div>
            </dl>
          </div>

          <div>
            <h2 className="mb-4 text-lg font-semibold text-gray-900">風險評估</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">資料敏感度</dt>
                <dd className="mt-1 text-sm text-gray-900">{asset.data_sensitivity}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">業務關鍵性</dt>
                <dd className="mt-1 text-sm text-gray-900">{asset.business_criticality}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">是否對外暴露</dt>
                <dd className="mt-1 text-sm text-gray-900">
                  {asset.is_public_facing ? "是" : "否"}
                </dd>
              </div>
            </dl>
          </div>
        </div>

        <div className="mt-6">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">運行的應用程式</h2>
          <p className="text-sm text-gray-900 whitespace-pre-wrap">{asset.running_applications}</p>
        </div>

        <div className="mt-6">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">產品清單</h2>
          {asset.products.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      產品名稱
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      版本
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      類型
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {asset.products.map((product) => (
                    <tr key={product.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {product.product_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {product.product_version || "-"}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {product.product_type || "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-gray-500">沒有產品資訊</p>
          )}
        </div>

        {/* 關聯的威脅 */}
        <div className="mt-6">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">關聯的威脅</h2>

          {/* 篩選和排序 */}
          <div className="mb-4 flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">最小信心分數：</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={threatAssociationParams.min_confidence || ""}
                onChange={(e) =>
                  setThreatAssociationParams({
                    ...threatAssociationParams,
                    min_confidence: e.target.value ? parseFloat(e.target.value) : undefined,
                    page: 1,
                  })
                }
                className="w-20 rounded-md border border-gray-300 px-2 py-1 text-sm"
                placeholder="0.0"
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">威脅嚴重程度：</label>
              <Select
                value={threatAssociationParams.threat_severity || ""}
                onChange={(e) =>
                  setThreatAssociationParams({
                    ...threatAssociationParams,
                    threat_severity: (e.target.value || undefined) as
                      | "Critical"
                      | "High"
                      | "Medium"
                      | "Low"
                      | undefined,
                    page: 1,
                  })
                }
                options={[
                  { value: "", label: "全部" },
                  { value: "Critical", label: "嚴重" },
                  { value: "High", label: "高" },
                  { value: "Medium", label: "中" },
                  { value: "Low", label: "低" },
                ]}
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">威脅狀態：</label>
              <Select
                value={threatAssociationParams.threat_status || ""}
                onChange={(e) =>
                  setThreatAssociationParams({
                    ...threatAssociationParams,
                    threat_status: (e.target.value || undefined) as
                      | "New"
                      | "Analyzing"
                      | "Processed"
                      | "Closed"
                      | undefined,
                    page: 1,
                  })
                }
                options={[
                  { value: "", label: "全部" },
                  { value: "New", label: "新增" },
                  { value: "Analyzing", label: "分析中" },
                  { value: "Processed", label: "已處理" },
                  { value: "Closed", label: "已關閉" },
                ]}
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">排序：</label>
              <Select
                value={threatAssociationParams.sort_by || "match_confidence"}
                onChange={(e) =>
                  setThreatAssociationParams({
                    ...threatAssociationParams,
                    sort_by: e.target.value as
                      | "match_confidence"
                      | "threat_cvss_base_score"
                      | "created_at",
                  })
                }
                options={[
                  { value: "match_confidence", label: "信心分數" },
                  { value: "threat_cvss_base_score", label: "CVSS 分數" },
                  { value: "created_at", label: "建立時間" },
                ]}
              />
              <Select
                value={threatAssociationParams.sort_order || "desc"}
                onChange={(e) =>
                  setThreatAssociationParams({
                    ...threatAssociationParams,
                    sort_order: e.target.value as "asc" | "desc",
                  })
                }
                options={[
                  { value: "desc", label: "降序" },
                  { value: "asc", label: "升序" },
                ]}
              />
            </div>
          </div>

          {threatAssociationsLoading ? (
            <div className="text-center text-gray-500">載入中...</div>
          ) : threatAssociations && threatAssociations.items.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        威脅 ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        CVE 編號
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        標題
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        嚴重程度
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        CVSS 分數
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        狀態
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        匹配信心分數
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        匹配類型
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {threatAssociations.items.map((association) => (
                      <tr key={association.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <button
                            onClick={() => router.push(`/threats/${association.threat_id}`)}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            {association.threat_id}
                          </button>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {association.threat_cve_id || "-"}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          {association.threat_title || "-"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {association.threat_severity ? (
                            <span
                              className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getSeverityColor(association.threat_severity)}`}
                            >
                              {association.threat_severity}
                            </span>
                          ) : (
                            <span className="text-gray-500">-</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {association.threat_cvss_base_score?.toFixed(1) || "-"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {association.threat_status ? (
                            <span
                              className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getStatusColor(association.threat_status)}`}
                            >
                              {association.threat_status}
                            </span>
                          ) : (
                            <span className="text-gray-500">-</span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <span
                            className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                              association.match_confidence >= 0.9
                                ? "bg-green-100 text-green-800"
                                : association.match_confidence >= 0.7
                                  ? "bg-yellow-100 text-yellow-800"
                                  : "bg-red-100 text-red-800"
                            }`}
                          >
                            {(association.match_confidence * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {association.match_type}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {/* 分頁 */}
              {threatAssociations.total_pages > 1 && (
                <div className="mt-4 flex items-center justify-between">
                  <div className="text-sm text-gray-700">
                    顯示{" "}
                    {(threatAssociationParams.page || 1) - 1 * (threatAssociationParams.page_size || 20) + 1}{" "}
                    到{" "}
                    {Math.min(
                      (threatAssociationParams.page || 1) * (threatAssociationParams.page_size || 20),
                      threatAssociations.total,
                    )}{" "}
                    筆，共 {threatAssociations.total} 筆
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={() =>
                        setThreatAssociationParams({
                          ...threatAssociationParams,
                          page: (threatAssociationParams.page || 1) - 1,
                        })
                      }
                      disabled={(threatAssociationParams.page || 1) <= 1}
                    >
                      上一頁
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() =>
                        setThreatAssociationParams({
                          ...threatAssociationParams,
                          page: (threatAssociationParams.page || 1) + 1,
                        })
                      }
                      disabled={(threatAssociationParams.page || 1) >= threatAssociations.total_pages}
                    >
                      下一頁
                    </Button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <p className="text-sm text-gray-500">目前沒有關聯的威脅</p>
          )}
        </div>
      </div>

      {/* 刪除確認模態 */}
      {showDeleteModal && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            <div
              className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
              onClick={() => setShowDeleteModal(false)}
            />
            <div className="inline-block transform overflow-hidden rounded-lg bg-white text-left align-bottom shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:align-middle">
              <div className="border-b border-gray-200 px-6 py-4">
                <h3 className="text-lg font-medium text-gray-900">確認刪除</h3>
              </div>
              <div className="px-6 py-4">
                <p>確定要刪除資產「{asset.host_name}」嗎？此操作無法復原。</p>
              </div>
              <div className="border-t border-gray-200 px-6 py-4">
                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setShowDeleteModal(false)}>
                    取消
                  </Button>
                  <Button variant="danger" onClick={handleDelete} isLoading={isDeleting}>
                    確認刪除
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

