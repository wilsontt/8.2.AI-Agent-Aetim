/**
 * 風險評估詳情組件
 * 
 * 顯示風險分數計算的詳細資訊，包含：
 * - 基礎 CVSS 分數與各加權因子的貢獻（AC-013-2）
 * - 視覺化呈現（堆疊圖、圓形圖等）
 * - 計算公式說明
 */

"use client";

import React from "react";
import type { RiskAssessmentDetailResponse, RiskLevel } from "@/types/risk_assessment";

interface RiskAssessmentDetailProps {
  riskAssessment: RiskAssessmentDetailResponse;
}

const getRiskLevelColor = (level: RiskLevel): string => {
  switch (level) {
    case "Critical":
      return "bg-red-500 text-white";
    case "High":
      return "bg-orange-500 text-white";
    case "Medium":
      return "bg-yellow-500 text-white";
    case "Low":
      return "bg-green-500 text-white";
    default:
      return "bg-gray-500 text-white";
  }
};

const getRiskLevelLabel = (level: RiskLevel): string => {
  switch (level) {
    case "Critical":
      return "嚴重";
    case "High":
      return "高";
    case "Medium":
      return "中";
    case "Low":
      return "低";
    default:
      return level;
  }
};

const getRiskScoreColor = (score: number): string => {
  if (score >= 9.0) return "text-red-600";
  if (score >= 7.0) return "text-orange-600";
  if (score >= 4.0) return "text-yellow-600";
  return "text-green-600";
};

const formatWeight = (weight: number | undefined): string => {
  if (weight === undefined || weight === null) return "-";
  return weight > 0 ? `+${weight.toFixed(2)}` : weight.toFixed(2);
};

const getWeightDescription = (
  type: string,
  value: number | undefined,
  details?: Record<string, any>,
  affectedAssetCount?: number,
): string => {
  if (value === undefined || value === null || value === 0) return "";

  switch (type) {
    case "asset_importance":
      const sensitivity = details?.asset_sensitivity || details?.data_sensitivity || "未知";
      const criticality = details?.asset_criticality || details?.business_criticality || "未知";
      if (sensitivity === "未知" && criticality === "未知") {
        return `（權重：${value.toFixed(2)}）`;
      }
      return `（資產重要性：${sensitivity} / ${criticality}）`;
    case "asset_count":
      const count = affectedAssetCount || value || 0;
      return `（${count} 個受影響資產）`;
    case "pir_match":
      const pirId = details?.pir_id || details?.matched_pir_id || "未知";
      if (pirId === "未知") {
        return `（符合高優先級 PIR）`;
      }
      return `（符合 PIR-${pirId}）`;
    case "cisa_kev":
      return `（在 CISA KEV 清單中）`;
    default:
      return "";
  }
};

export const RiskAssessmentDetail: React.FC<RiskAssessmentDetailProps> = ({
  riskAssessment,
}) => {
  const {
    final_risk_score,
    risk_level,
    base_cvss_score,
    asset_importance_weight,
    affected_asset_count,
    asset_count_weight,
    pir_match_weight,
    cisa_kev_weight,
    calculation_details,
    calculation_formula,
  } = riskAssessment;

  // 計算各部分的貢獻
  const baseContribution = base_cvss_score * (asset_importance_weight || 1.0);
  const totalWeight = (asset_count_weight || 0) + (pir_match_weight || 0) + (cisa_kev_weight || 0);
  const totalContribution = baseContribution + totalWeight;

  // 計算百分比（用於視覺化）
  const basePercentage = totalContribution > 0 ? (baseContribution / totalContribution) * 100 : 0;
  const assetCountPercentage =
    totalContribution > 0 ? ((asset_count_weight || 0) / totalContribution) * 100 : 0;
  const pirPercentage =
    totalContribution > 0 ? ((pir_match_weight || 0) / totalContribution) * 100 : 0;
  const cisaKevPercentage =
    totalContribution > 0 ? ((cisa_kev_weight || 0) / totalContribution) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* 風險分數總覽 */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-gray-500">最終風險分數</h3>
            <div className="mt-2 flex items-baseline space-x-2">
              <span
                className={`text-5xl font-bold ${getRiskScoreColor(final_risk_score)}`}
              >
                {final_risk_score.toFixed(2)}
              </span>
              <span className="text-2xl text-gray-400">/ 10.0</span>
            </div>
          </div>
          <div className="text-right">
            <h3 className="text-sm font-medium text-gray-500">風險等級</h3>
            <div className="mt-2">
              <span
                className={`inline-flex rounded-full px-4 py-2 text-lg font-semibold ${getRiskLevelColor(risk_level)}`}
              >
                {getRiskLevelLabel(risk_level)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 計算詳情 - 堆疊圖視覺化 */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">風險分數計算詳情</h3>

        {/* 堆疊條形圖 */}
        <div className="mb-6">
          <div className="mb-2 text-sm font-medium text-gray-700">貢獻度視覺化</div>
          <div className="h-8 w-full rounded-md bg-gray-200 overflow-hidden flex">
            {/* 基礎 CVSS 分數（乘以資產重要性） */}
            {basePercentage > 0 && (
              <div
                className="bg-blue-500 flex items-center justify-center text-white text-xs font-semibold"
                style={{ width: `${basePercentage}%` }}
                title={`基礎 CVSS × 資產重要性：${baseContribution.toFixed(2)}`}
              >
                {basePercentage > 5 && `${basePercentage.toFixed(1)}%`}
              </div>
            )}
            {/* 資產數量加權 */}
            {assetCountPercentage > 0 && (
              <div
                className="bg-yellow-500 flex items-center justify-center text-white text-xs font-semibold"
                style={{ width: `${assetCountPercentage}%` }}
                title={`資產數量加權：${asset_count_weight?.toFixed(2)}`}
              >
                {assetCountPercentage > 5 && `${assetCountPercentage.toFixed(1)}%`}
              </div>
            )}
            {/* PIR 符合度加權 */}
            {pirPercentage > 0 && (
              <div
                className="bg-purple-500 flex items-center justify-center text-white text-xs font-semibold"
                style={{ width: `${pirPercentage}%` }}
                title={`PIR 符合度加權：${pir_match_weight?.toFixed(2)}`}
              >
                {pirPercentage > 5 && `${pirPercentage.toFixed(1)}%`}
              </div>
            )}
            {/* CISA KEV 加權 */}
            {cisaKevPercentage > 0 && (
              <div
                className="bg-red-500 flex items-center justify-center text-white text-xs font-semibold"
                style={{ width: `${cisaKevPercentage}%` }}
                title={`CISA KEV 加權：${cisa_kev_weight?.toFixed(2)}`}
              >
                {cisaKevPercentage > 5 && `${cisaKevPercentage.toFixed(1)}%`}
              </div>
            )}
          </div>
          <div className="mt-2 flex flex-wrap gap-4 text-xs text-gray-600">
            {basePercentage > 0 && (
              <div className="flex items-center space-x-2">
                <div className="h-3 w-3 rounded bg-blue-500" />
                <span>基礎 CVSS × 資產重要性</span>
              </div>
            )}
            {assetCountPercentage > 0 && (
              <div className="flex items-center space-x-2">
                <div className="h-3 w-3 rounded bg-yellow-500" />
                <span>資產數量加權</span>
              </div>
            )}
            {pirPercentage > 0 && (
              <div className="flex items-center space-x-2">
                <div className="h-3 w-3 rounded bg-purple-500" />
                <span>PIR 符合度加權</span>
              </div>
            )}
            {cisaKevPercentage > 0 && (
              <div className="flex items-center space-x-2">
                <div className="h-3 w-3 rounded bg-red-500" />
                <span>CISA KEV 加權</span>
              </div>
            )}
          </div>
        </div>

        {/* 詳細計算步驟 */}
        <div className="space-y-4">
          {/* 基礎 CVSS 分數 */}
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-700">基礎 CVSS 分數</div>
              <div className="mt-1 text-xs text-gray-500">威脅的基礎嚴重程度評分</div>
            </div>
            <div className="text-right">
              <div className="text-lg font-semibold text-gray-900">
                {base_cvss_score.toFixed(2)}
              </div>
            </div>
          </div>

          {/* 資產重要性加權 */}
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-700">
                基礎分數 × 資產重要性加權
              </div>
              <div className="mt-1 text-xs text-gray-500">
                {getWeightDescription(
                  "asset_importance",
                  asset_importance_weight,
                  calculation_details,
                ) || "根據資產敏感度和業務關鍵性計算"}
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600">
                {base_cvss_score.toFixed(2)} × {asset_importance_weight?.toFixed(2) || "1.00"} =
              </div>
              <div className="text-lg font-semibold text-blue-600">
                {baseContribution.toFixed(2)}
              </div>
            </div>
          </div>

          {/* 受影響資產數量加權 */}
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-700">受影響資產數量加權</div>
              <div className="mt-1 text-xs text-gray-500">
                {getWeightDescription(
                  "asset_count",
                  asset_count_weight,
                  calculation_details,
                  affected_asset_count,
                )}
              </div>
            </div>
            <div className="text-right">
              <div className="text-lg font-semibold text-green-600">
                {formatWeight(asset_count_weight)}
              </div>
            </div>
          </div>

          {/* PIR 符合度加權 */}
          {pir_match_weight !== undefined && pir_match_weight !== null && (
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-700">PIR 符合度加權</div>
                <div className="mt-1 text-xs text-gray-500">
                  {getWeightDescription("pir_match", pir_match_weight, calculation_details) ||
                    "符合優先情報需求"}
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold text-green-600">
                  {formatWeight(pir_match_weight)}
                </div>
              </div>
            </div>
          )}

          {/* CISA KEV 加權 */}
          {cisa_kev_weight !== undefined && cisa_kev_weight !== null && (
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-700">CISA KEV 加權</div>
                <div className="mt-1 text-xs text-gray-500">
                  {getWeightDescription("cisa_kev", cisa_kev_weight, calculation_details) ||
                    "在 CISA 已知被利用漏洞清單中"}
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold text-green-600">
                  {formatWeight(cisa_kev_weight)}
                </div>
              </div>
            </div>
          )}

          {/* 最終風險分數 */}
          <div className="flex items-center justify-between pt-3">
            <div className="flex-1">
              <div className="text-base font-semibold text-gray-900">最終風險分數</div>
              <div className="mt-1 text-xs text-gray-500">
                基礎分數 × 資產重要性 + 所有加權因子（上限 10.0）
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">
                = {final_risk_score.toFixed(2)}
              </div>
            </div>
          </div>
        </div>

        {/* 計算公式說明 */}
        {calculation_formula && (
          <div className="mt-6 rounded-md bg-gray-50 p-4">
            <h4 className="mb-2 text-sm font-medium text-gray-700">計算公式</h4>
            <p className="text-xs text-gray-600 font-mono whitespace-pre-wrap">
              {calculation_formula}
            </p>
            <div className="mt-3 text-xs text-gray-500">
              <p>公式說明：</p>
              <ul className="mt-1 list-disc list-inside space-y-1">
                <li>基礎 CVSS 分數：威脅的基礎嚴重程度（0.0 - 10.0）</li>
                <li>資產重要性加權：根據資產敏感度和業務關鍵性計算的乘數</li>
                <li>資產數量加權：每增加 10 個受影響資產，風險分數增加 0.1</li>
                <li>PIR 符合度加權：符合高優先級 PIR 時，風險分數增加 0.3</li>
                <li>CISA KEV 加權：在 CISA KEV 清單中時，風險分數增加 0.5</li>
                <li>最終風險分數上限為 10.0</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

