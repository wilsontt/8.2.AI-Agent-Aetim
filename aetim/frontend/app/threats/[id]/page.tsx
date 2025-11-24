/**
 * 威脅詳情頁面
 */

"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { Modal } from "@/components/ui/Modal";
import { getThreatById, updateThreatStatus } from "@/lib/api/threat";
import {
  getThreatAssociations,
  analyzeThreatAssociations,
} from "@/lib/api/association";
import {
  getRiskAssessment,
  calculateRisk,
} from "@/lib/api/risk_assessment";
import { AssociationVisualization } from "@/components/AssociationVisualization";
import { RiskAssessmentDisplay } from "@/components/RiskAssessmentDisplay";
import type { ThreatDetailResponse } from "@/types/threat";
import type {
  ThreatAssociationListResponse,
  ThreatAssociationParams,
} from "@/types/association";
import type { RiskAssessmentDetailResponse } from "@/types/risk_assessment";

export default function ThreatDetailPage() {
  const params = useParams();
  const router = useRouter();
  const threatId = params.id as string;

  const [threatDetail, setThreatDetail] = useState<ThreatDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [newStatus, setNewStatus] = useState<string>("");
  const [isUpdating, setIsUpdating] = useState(false);
  const [associations, setAssociations] = useState<ThreatAssociationListResponse | null>(null);
  const [associationsLoading, setAssociationsLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [associationParams, setAssociationParams] = useState<ThreatAssociationParams>({
    page: 1,
    page_size: 20,
    sort_by: "match_confidence",
    sort_order: "desc",
  });
  const [riskAssessment, setRiskAssessment] = useState<RiskAssessmentDetailResponse | null>(null);
  const [riskAssessmentLoading, setRiskAssessmentLoading] = useState(false);
  const [riskAssessmentError, setRiskAssessmentError] = useState<string | null>(null);
  const [isCalculatingRisk, setIsCalculatingRisk] = useState(false);

  useEffect(() => {
    if (threatId) {
      loadThreat();
      loadAssociations();
      loadRiskAssessment();
    }
  }, [threatId]);

  useEffect(() => {
    if (threatId) {
      loadAssociations();
    }
  }, [threatId, associationParams]);

  const loadThreat = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getThreatById(threatId);
      setThreatDetail(data);
      setNewStatus(data.threat.status);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入威脅詳情失敗");
    } finally {
      setLoading(false);
    }
  };

  const loadAssociations = async () => {
    try {
      setAssociationsLoading(true);
      const data = await getThreatAssociations(threatId, associationParams);
      setAssociations(data);
    } catch (err) {
      console.error("載入關聯失敗：", err);
    } finally {
      setAssociationsLoading(false);
    }
  };

  const loadRiskAssessment = async () => {
    try {
      setRiskAssessmentLoading(true);
      setRiskAssessmentError(null);
      const data = await getRiskAssessment(threatId);
      setRiskAssessment(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "載入風險評估失敗";
      // 如果風險評估不存在，不顯示錯誤（這是正常情況）
      if (errorMessage.includes("不存在")) {
        setRiskAssessment(null);
        setRiskAssessmentError(null);
      } else {
        setRiskAssessmentError(errorMessage);
      }
    } finally {
      setRiskAssessmentLoading(false);
    }
  };

  const handleCalculateRisk = async () => {
    if (!associations || associations.items.length === 0) {
      setRiskAssessmentError("請先執行關聯分析，建立威脅與資產的關聯");
      return;
    }

    try {
      setIsCalculatingRisk(true);
      setRiskAssessmentError(null);
      // 使用第一個關聯的 ID
      const firstAssociation = associations.items[0];
      await calculateRisk(threatId, {
        threat_asset_association_id: firstAssociation.id,
      });
      // 重新載入風險評估
      await loadRiskAssessment();
    } catch (err) {
      setRiskAssessmentError(err instanceof Error ? err.message : "計算風險分數失敗");
    } finally {
      setIsCalculatingRisk(false);
    }
  };

  const handleAnalyze = async () => {
    try {
      setIsAnalyzing(true);
      await analyzeThreatAssociations(threatId);
      // 重新載入威脅詳情和關聯
      await loadThreat();
      await loadAssociations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "執行關聯分析失敗");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleUpdateStatus = async () => {
    if (!threatDetail || !newStatus) return;

    try {
      setIsUpdating(true);
      await updateThreatStatus(threatId, { status: newStatus as any });
      setShowStatusModal(false);
      // 重新載入威脅詳情
      await loadThreat();
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新威脅狀態失敗");
    } finally {
      setIsUpdating(false);
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

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "New":
        return "新增";
      case "Analyzing":
        return "分析中";
      case "Processed":
        return "已處理";
      case "Closed":
        return "已關閉";
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-gray-500">載入中...</div>
      </div>
    );
  }

  if (error || !threatDetail) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error || "威脅不存在"}</p>
        </div>
        <Button variant="outline" onClick={() => router.push("/threats")} className="mt-4">
          返回清單
        </Button>
      </div>
    );
  }

  const { threat, associated_assets } = threatDetail;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">威脅詳情</h1>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => router.push("/threats")}>
            返回清單
          </Button>
          <Button variant="primary" onClick={() => setShowStatusModal(true)}>
            更新狀態
          </Button>
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
        {/* 基本資訊 */}
        <div className="mb-6">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">基本資訊</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div>
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm font-medium text-gray-500">CVE 編號</dt>
                  <dd className="mt-1 text-sm text-gray-900">{threat.cve_id || "-"}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">標題</dt>
                  <dd className="mt-1 text-sm text-gray-900">{threat.title}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">嚴重程度</dt>
                  <dd className="mt-1">
                    {threat.severity ? (
                      <span
                        className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getSeverityColor(threat.severity)}`}
                      >
                        {threat.severity}
                      </span>
                    ) : (
                      <span className="text-sm text-gray-500">-</span>
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">CVSS 基礎分數</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {threat.cvss_base_score?.toFixed(1) || "-"}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">CVSS 向量</dt>
                  <dd className="mt-1 text-sm text-gray-900 font-mono text-xs">
                    {threat.cvss_vector || "-"}
                  </dd>
                </div>
              </dl>
            </div>

            <div>
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm font-medium text-gray-500">狀態</dt>
                  <dd className="mt-1">
                    <span
                      className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getStatusColor(threat.status)}`}
                    >
                      {getStatusLabel(threat.status)}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">發布日期</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {threat.published_date
                      ? new Date(threat.published_date).toLocaleDateString("zh-TW")
                      : "-"}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">收集時間</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {threat.collected_at
                      ? new Date(threat.collected_at).toLocaleString("zh-TW")
                      : "-"}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">來源 URL</dt>
                  <dd className="mt-1">
                    {threat.source_url ? (
                      <a
                        href={threat.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:text-blue-800"
                      >
                        {threat.source_url}
                      </a>
                    ) : (
                      <span className="text-sm text-gray-500">-</span>
                    )}
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        </div>

        {/* 描述 */}
        {threat.description && (
          <div className="mb-6">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">描述</h2>
            <p className="text-sm text-gray-900 whitespace-pre-wrap">{threat.description}</p>
          </div>
        )}

        {/* 產品清單 */}
        {threat.products.length > 0 && (
          <div className="mb-6">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">受影響產品</h2>
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
                  {threat.products.map((product) => (
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
          </div>
        )}

        {/* TTPs */}
        {threat.ttps.length > 0 && (
          <div className="mb-6">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">TTPs (戰術、技術和程序)</h2>
            <div className="flex flex-wrap gap-2">
              {threat.ttps.map((ttp, index) => (
                <span
                  key={index}
                  className="inline-flex rounded-md bg-blue-50 px-3 py-1 text-sm font-medium text-blue-800"
                >
                  {ttp}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* IOCs */}
        {(threat.iocs.ips?.length || threat.iocs.domains?.length || threat.iocs.hashes?.length) && (
          <div className="mb-6">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">IOCs (入侵指標)</h2>
            <div className="space-y-4">
              {threat.iocs.ips && threat.iocs.ips.length > 0 && (
                <div>
                  <h3 className="mb-2 text-sm font-medium text-gray-700">IP 位址</h3>
                  <div className="flex flex-wrap gap-2">
                    {threat.iocs.ips.map((ip, index) => (
                      <span
                        key={index}
                        className="inline-flex rounded-md bg-red-50 px-3 py-1 text-sm font-mono text-red-800"
                      >
                        {ip}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {threat.iocs.domains && threat.iocs.domains.length > 0 && (
                <div>
                  <h3 className="mb-2 text-sm font-medium text-gray-700">網域</h3>
                  <div className="flex flex-wrap gap-2">
                    {threat.iocs.domains.map((domain, index) => (
                      <span
                        key={index}
                        className="inline-flex rounded-md bg-orange-50 px-3 py-1 text-sm font-mono text-orange-800"
                      >
                        {domain}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {threat.iocs.hashes && threat.iocs.hashes.length > 0 && (
                <div>
                  <h3 className="mb-2 text-sm font-medium text-gray-700">雜湊值</h3>
                  <div className="flex flex-wrap gap-2">
                    {threat.iocs.hashes.map((hash, index) => (
                      <span
                        key={index}
                        className="inline-flex rounded-md bg-purple-50 px-3 py-1 text-xs font-mono text-purple-800"
                      >
                        {hash}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 關聯的資產（使用新的 API） */}
        <div className="mb-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">關聯的資產</h2>
            <Button
              variant="primary"
              onClick={handleAnalyze}
              isLoading={isAnalyzing}
              disabled={isAnalyzing}
            >
              執行關聯分析
            </Button>
          </div>

          {/* 篩選和排序 */}
          <div className="mb-4 flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">最小信心分數：</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={associationParams.min_confidence || ""}
                onChange={(e) =>
                  setAssociationParams({
                    ...associationParams,
                    min_confidence: e.target.value ? parseFloat(e.target.value) : undefined,
                    page: 1,
                  })
                }
                className="w-20 rounded-md border border-gray-300 px-2 py-1 text-sm"
                placeholder="0.0"
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">匹配類型：</label>
              <Select
                value={associationParams.match_type || ""}
                onChange={(e) =>
                  setAssociationParams({
                    ...associationParams,
                    match_type: e.target.value || undefined,
                    page: 1,
                  })
                }
                options={[
                  { value: "", label: "全部" },
                  { value: "exact_product_exact_version", label: "精確產品+精確版本" },
                  { value: "exact_product_version_range", label: "精確產品+版本範圍" },
                  { value: "exact_product_major_version", label: "精確產品+主版本" },
                  { value: "exact_product_no_version", label: "精確產品+無版本" },
                  { value: "fuzzy_product_exact_version", label: "模糊產品+精確版本" },
                  { value: "fuzzy_product_version_range", label: "模糊產品+版本範圍" },
                  { value: "fuzzy_product_major_version", label: "模糊產品+主版本" },
                  { value: "fuzzy_product_no_version", label: "模糊產品+無版本" },
                  { value: "os_match", label: "作業系統匹配" },
                ]}
              />
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">排序：</label>
              <Select
                value={associationParams.sort_by || "match_confidence"}
                onChange={(e) =>
                  setAssociationParams({
                    ...associationParams,
                    sort_by: e.target.value as "match_confidence" | "created_at",
                  })
                }
                options={[
                  { value: "match_confidence", label: "信心分數" },
                  { value: "created_at", label: "建立時間" },
                ]}
              />
              <Select
                value={associationParams.sort_order || "desc"}
                onChange={(e) =>
                  setAssociationParams({
                    ...associationParams,
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

          {associationsLoading ? (
            <div className="text-center text-gray-500">載入中...</div>
          ) : associations && associations.items.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        資產 ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        匹配類型
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        匹配信心分數
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        匹配詳情
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        建立時間
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {associations.items.map((association) => (
                      <tr key={association.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <button
                            onClick={() => router.push(`/assets/${association.asset_id}`)}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            {association.asset_id}
                          </button>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {association.match_type}
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
                        <td className="px-6 py-4 text-sm text-gray-900">
                          {association.match_details?.matched_products &&
                          association.match_details.matched_products.length > 0 ? (
                            <div className="space-y-1">
                              {association.match_details.matched_products.map((product, idx) => (
                                <div key={idx} className="text-xs">
                                  {product.threat_product && product.asset_product && (
                                    <span>
                                      {product.threat_product} ({product.threat_version || "N/A"}) ↔{" "}
                                      {product.asset_product} ({product.asset_version || "N/A"})
                                    </span>
                                  )}
                                  {product.threat_os && product.asset_os && (
                                    <span>
                                      OS: {product.threat_os} ↔ {product.asset_os}
                                    </span>
                                  )}
                                </div>
                              ))}
                            </div>
                          ) : (
                            "-"
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {association.created_at
                            ? new Date(association.created_at).toLocaleString("zh-TW")
                            : "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {/* 分頁 */}
              {associations.total_pages > 1 && (
                <div className="mt-4 flex items-center justify-between">
                  <div className="text-sm text-gray-700">
                    顯示 {((associationParams.page || 1) - 1) * (associationParams.page_size || 20) + 1} 到{" "}
                    {Math.min(
                      (associationParams.page || 1) * (associationParams.page_size || 20),
                      associations.total,
                    )}{" "}
                    筆，共 {associations.total} 筆
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={() =>
                        setAssociationParams({
                          ...associationParams,
                          page: (associationParams.page || 1) - 1,
                        })
                      }
                      disabled={(associationParams.page || 1) <= 1}
                    >
                      上一頁
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() =>
                        setAssociationParams({
                          ...associationParams,
                          page: (associationParams.page || 1) + 1,
                        })
                      }
                      disabled={(associationParams.page || 1) >= associations.total_pages}
                    >
                      下一頁
                    </Button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <p className="text-sm text-gray-500">目前沒有關聯的資產</p>
          )}
        </div>

        {/* 關聯分析視覺化 */}
        {associations && associations.items.length > 0 && (
          <div className="mb-6">
            <AssociationVisualization
              associations={associations.items}
              threatId={threat.id}
              threatTitle={threat.title}
            />
          </div>
        )}

        {/* 風險評估區塊 */}
        <div className="mb-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">風險評估</h2>
            <Button
              variant="primary"
              onClick={handleCalculateRisk}
              isLoading={isCalculatingRisk}
              disabled={isCalculatingRisk || !associations || associations.items.length === 0}
            >
              {riskAssessment ? "重新計算風險分數" : "計算風險分數"}
            </Button>
          </div>

          {riskAssessmentLoading ? (
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <div className="text-center text-gray-500">載入風險評估中...</div>
            </div>
          ) : riskAssessmentError ? (
            <div className="rounded-lg border border-red-200 bg-red-50 p-6 shadow-sm">
              <p className="text-sm text-red-800">{riskAssessmentError}</p>
            </div>
          ) : riskAssessment ? (
            <RiskAssessmentDisplay riskAssessment={riskAssessment} />
          ) : (
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <p className="text-sm text-gray-500">
                尚未進行風險評估。請先執行關聯分析，然後點擊「計算風險分數」按鈕。
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 更新狀態模態 */}
      <Modal
        isOpen={showStatusModal}
        onClose={() => setShowStatusModal(false)}
        title="更新威脅狀態"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">目前狀態</label>
            <p className="mt-1 text-sm text-gray-900">
              <span
                className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${getStatusColor(threat.status)}`}
              >
                {getStatusLabel(threat.status)}
              </span>
            </p>
          </div>

          <div>
            <Select
              label="新狀態"
              id="new_status"
              name="new_status"
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value)}
              options={[
                { value: "New", label: "新增" },
                { value: "Analyzing", label: "分析中" },
                { value: "Processed", label: "已處理" },
                { value: "Closed", label: "已關閉" },
              ]}
            />
          </div>

          {error && (
            <div className="rounded-md bg-red-50 p-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setShowStatusModal(false)}>
              取消
            </Button>
            <Button variant="primary" onClick={handleUpdateStatus} isLoading={isUpdating}>
              確認更新
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

