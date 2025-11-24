/**
 * 風險評估顯示組件
 * 
 * 顯示威脅的風險評估資訊，包括：
 * - 風險分數（大字體、顏色編碼）
 * - 風險等級（嚴重/高/中/低）
 * - 風險分數計算詳情
 * - 視覺化呈現（進度條、圓形圖表等）
 */

"use client";

import React from "react";
import type { RiskAssessmentDetailResponse, RiskLevel } from "@/types/risk_assessment";

interface RiskAssessmentDisplayProps {
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
      // 嘗試從 calculation_details 中取得詳細信息
      const sensitivity = details?.asset_sensitivity || details?.data_sensitivity || "未知";
      const criticality = details?.asset_criticality || details?.business_criticality || "未知";
      // 如果沒有詳細信息，顯示權重值
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

export const RiskAssessmentDisplay: React.FC<RiskAssessmentDisplayProps> = ({
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

  // 計算總加權
  const totalWeight =
    (asset_importance_weight || 0) +
    (asset_count_weight || 0) +
    (pir_match_weight || 0) +
    (cisa_kev_weight || 0);

  // 計算進度條百分比（以 10 為滿分）
  const scorePercentage = (final_risk_score / 10) * 100;

  return (
    <div className="space-y-6">
      {/* 風險分數與等級 */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-medium text-gray-500">風險分數</h3>
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

        {/* 風險分數進度條 */}
        <div className="mt-6">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
            <span>風險分數視覺化</span>
            <span>{scorePercentage.toFixed(1)}%</span>
          </div>
          <div className="h-4 w-full rounded-full bg-gray-200 overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                final_risk_score >= 9.0
                  ? "bg-red-500"
                  : final_risk_score >= 7.0
                    ? "bg-orange-500"
                    : final_risk_score >= 4.0
                      ? "bg-yellow-500"
                      : "bg-green-500"
              }`}
              style={{ width: `${scorePercentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* 風險分數計算詳情 */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">風險分數計算詳情</h3>

        <div className="space-y-4">
          {/* 基礎 CVSS 分數 */}
          <div className="flex items-center justify-between border-b border-gray-100 pb-3">
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-700">基礎 CVSS 分數</div>
              <div className="mt-1 text-xs text-gray-500">
                威脅的基礎嚴重程度評分
              </div>
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
              <div className="text-sm font-medium text-gray-700">資產重要性加權</div>
              <div className="mt-1 text-xs text-gray-500">
                {getWeightDescription(
                  "asset_importance",
                  asset_importance_weight,
                  calculation_details,
                ) || "根據資產敏感度和業務關鍵性計算"}
              </div>
            </div>
            <div className="text-right">
              <div className="text-lg font-semibold text-green-600">
                {formatWeight(asset_importance_weight)}
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
                基礎分數 + 所有加權因子（上限 10.0）
              </div>
            </div>
            <div className="text-right">
              <div className={`text-2xl font-bold ${getRiskScoreColor(final_risk_score)}`}>
                {final_risk_score.toFixed(2)}
              </div>
            </div>
          </div>
        </div>

        {/* 計算公式說明 */}
        {calculation_formula && (
          <div className="mt-6 rounded-md bg-gray-50 p-4">
            <h4 className="mb-2 text-sm font-medium text-gray-700">計算公式</h4>
            <p className="text-xs text-gray-600 font-mono">{calculation_formula}</p>
          </div>
        )}
      </div>

      {/* 視覺化：圓形圖表（加權因子貢獻） */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">加權因子貢獻分析</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {/* 基礎分數 */}
          <div className="flex items-center space-x-3">
            <div className="h-4 w-4 rounded bg-blue-500" />
            <div className="flex-1">
              <div className="text-sm font-medium text-gray-700">基礎 CVSS 分數</div>
              <div className="text-xs text-gray-500">
                {((base_cvss_score / final_risk_score) * 100).toFixed(1)}% 貢獻度
              </div>
            </div>
            <div className="text-sm font-semibold text-gray-900">
              {base_cvss_score.toFixed(2)}
            </div>
          </div>

          {/* 資產重要性 */}
          {asset_importance_weight !== undefined && asset_importance_weight > 0 && (
            <div className="flex items-center space-x-3">
              <div className="h-4 w-4 rounded bg-green-500" />
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-700">資產重要性</div>
                <div className="text-xs text-gray-500">
                  {totalWeight > 0
                    ? ((asset_importance_weight / totalWeight) * 100).toFixed(1)
                    : 0}
                  % 加權貢獻
                </div>
              </div>
              <div className="text-sm font-semibold text-gray-900">
                {formatWeight(asset_importance_weight)}
              </div>
            </div>
          )}

          {/* 資產數量 */}
          {asset_count_weight !== undefined && asset_count_weight > 0 && (
            <div className="flex items-center space-x-3">
              <div className="h-4 w-4 rounded bg-yellow-500" />
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-700">受影響資產數量</div>
                <div className="text-xs text-gray-500">
                  {totalWeight > 0
                    ? ((asset_count_weight / totalWeight) * 100).toFixed(1)
                    : 0}
                  % 加權貢獻
                </div>
              </div>
              <div className="text-sm font-semibold text-gray-900">
                {formatWeight(asset_count_weight)}
              </div>
            </div>
          )}

          {/* PIR 符合度 */}
          {pir_match_weight !== undefined && pir_match_weight > 0 && (
            <div className="flex items-center space-x-3">
              <div className="h-4 w-4 rounded bg-purple-500" />
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-700">PIR 符合度</div>
                <div className="text-xs text-gray-500">
                  {totalWeight > 0
                    ? ((pir_match_weight / totalWeight) * 100).toFixed(1)
                    : 0}
                  % 加權貢獻
                </div>
              </div>
              <div className="text-sm font-semibold text-gray-900">
                {formatWeight(pir_match_weight)}
              </div>
            </div>
          )}

          {/* CISA KEV */}
          {cisa_kev_weight !== undefined && cisa_kev_weight > 0 && (
            <div className="flex items-center space-x-3">
              <div className="h-4 w-4 rounded bg-red-500" />
              <div className="flex-1">
                <div className="text-sm font-medium text-gray-700">CISA KEV</div>
                <div className="text-xs text-gray-500">
                  {totalWeight > 0
                    ? ((cisa_kev_weight / totalWeight) * 100).toFixed(1)
                    : 0}
                  % 加權貢獻
                </div>
              </div>
              <div className="text-sm font-semibold text-gray-900">
                {formatWeight(cisa_kev_weight)}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

