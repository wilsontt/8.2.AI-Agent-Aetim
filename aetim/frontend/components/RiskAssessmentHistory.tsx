/**
 * 風險評估歷史記錄組件
 * 
 * 顯示風險分數的歷史記錄，包含時間軸視覺化（AC-013-3）
 */

"use client";

import React from "react";
import type { RiskAssessmentHistoryResponse, RiskLevel } from "@/types/risk_assessment";

interface RiskAssessmentHistoryProps {
  histories: RiskAssessmentHistoryResponse[];
  threatId: string;
}

const getRiskLevelColor = (level: RiskLevel): string => {
  switch (level) {
    case "Critical":
      return "bg-red-500";
    case "High":
      return "bg-orange-500";
    case "Medium":
      return "bg-yellow-500";
    case "Low":
      return "bg-green-500";
    default:
      return "bg-gray-500";
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

const formatWeight = (weight: number | undefined): string => {
  if (weight === undefined || weight === null) return "-";
  return weight > 0 ? `+${weight.toFixed(2)}` : weight.toFixed(2);
};

const getChangeReason = (
  current: RiskAssessmentHistoryResponse,
  previous: RiskAssessmentHistoryResponse | null,
): string => {
  if (!previous) {
    return "初始計算";
  }

  const reasons: string[] = [];

  // 檢查 CVSS 分數變更
  if (current.base_cvss_score !== previous.base_cvss_score) {
    reasons.push("CVSS 分數更新");
  }

  // 檢查資產重要性變更
  if (current.asset_importance_weight !== previous.asset_importance_weight) {
    reasons.push("資產重要性變更");
  }

  // 檢查受影響資產數量變更
  if (current.affected_asset_count !== previous.affected_asset_count) {
    reasons.push(`受影響資產數量變更（${previous.affected_asset_count} → ${current.affected_asset_count}）`);
  }

  // 檢查 PIR 符合度變更
  if (current.pir_match_weight !== previous.pir_match_weight) {
    if (current.pir_match_weight && !previous.pir_match_weight) {
      reasons.push("新增 PIR 符合");
    } else if (!current.pir_match_weight && previous.pir_match_weight) {
      reasons.push("移除 PIR 符合");
    } else {
      reasons.push("PIR 符合度變更");
    }
  }

  // 檢查 CISA KEV 狀態變更
  if (current.cisa_kev_weight !== previous.cisa_kev_weight) {
    if (current.cisa_kev_weight && !previous.cisa_kev_weight) {
      reasons.push("新增至 CISA KEV 清單");
    } else if (!current.cisa_kev_weight && previous.cisa_kev_weight) {
      reasons.push("從 CISA KEV 清單移除");
    }
  }

  return reasons.length > 0 ? reasons.join("、") : "重新計算";
};

export const RiskAssessmentHistory: React.FC<RiskAssessmentHistoryProps> = ({
  histories,
  threatId,
}) => {
  if (histories.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-gray-500">目前沒有歷史記錄</p>
      </div>
    );
  }

  // 按時間排序（最新的在前）
  const sortedHistories = [...histories].sort((a, b) => {
    return new Date(b.calculated_at).getTime() - new Date(a.calculated_at).getTime();
  });

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
      <h3 className="mb-6 text-lg font-semibold text-gray-900">風險分數歷史記錄</h3>

      {/* 時間軸視覺化 */}
      <div className="relative">
        {/* 時間軸線 */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-300" />

        <div className="space-y-8">
          {sortedHistories.map((history, index) => {
            const previous = index < sortedHistories.length - 1 ? sortedHistories[index + 1] : null;
            const changeReason = getChangeReason(history, previous);
            const isLatest = index === 0;

            return (
              <div key={history.id} className="relative flex items-start space-x-4">
                {/* 時間軸節點 */}
                <div className="relative z-10 flex-shrink-0">
                  <div
                    className={`h-8 w-8 rounded-full border-4 border-white ${
                      isLatest ? getRiskLevelColor(history.risk_level) : "bg-gray-400"
                    } shadow-md`}
                  />
                  {isLatest && (
                    <div className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-green-500 border-2 border-white" />
                  )}
                </div>

                {/* 內容 */}
                <div className="flex-1 min-w-0">
                  <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                    {/* 標題行 */}
                    <div className="mb-3 flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <span
                          className={`inline-flex rounded-full px-3 py-1 text-sm font-semibold ${
                            isLatest
                              ? getRiskLevelColor(history.risk_level) + " text-white"
                              : "bg-gray-200 text-gray-700"
                          }`}
                        >
                          {getRiskLevelLabel(history.risk_level)}
                        </span>
                        <span className="text-lg font-bold text-gray-900">
                          {history.final_risk_score.toFixed(2)}
                        </span>
                        <span className="text-sm text-gray-500">/ 10.0</span>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900">
                          {new Date(history.calculated_at).toLocaleDateString("zh-TW", {
                            year: "numeric",
                            month: "long",
                            day: "numeric",
                          })}
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(history.calculated_at).toLocaleTimeString("zh-TW", {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </div>
                      </div>
                    </div>

                    {/* 變更原因 */}
                    {changeReason && (
                      <div className="mb-3 rounded-md bg-blue-50 px-3 py-2">
                        <div className="text-xs font-medium text-blue-800">變更原因</div>
                        <div className="text-sm text-blue-700">{changeReason}</div>
                      </div>
                    )}

                    {/* 計算詳情 */}
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <div className="text-xs text-gray-500">基礎 CVSS 分數</div>
                        <div className="font-semibold text-gray-900">
                          {history.base_cvss_score.toFixed(2)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500">資產重要性加權</div>
                        <div className="font-semibold text-green-600">
                          {formatWeight(history.asset_importance_weight)}
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500">受影響資產數量</div>
                        <div className="font-semibold text-gray-900">
                          {history.affected_asset_count} 個
                        </div>
                      </div>
                      <div>
                        <div className="text-xs text-gray-500">資產數量加權</div>
                        <div className="font-semibold text-green-600">
                          {formatWeight(history.asset_count_weight)}
                        </div>
                      </div>
                      {history.pir_match_weight !== undefined && history.pir_match_weight !== null && (
                        <div>
                          <div className="text-xs text-gray-500">PIR 符合度加權</div>
                          <div className="font-semibold text-green-600">
                            {formatWeight(history.pir_match_weight)}
                          </div>
                        </div>
                      )}
                      {history.cisa_kev_weight !== undefined && history.cisa_kev_weight !== null && (
                        <div>
                          <div className="text-xs text-gray-500">CISA KEV 加權</div>
                          <div className="font-semibold text-green-600">
                            {formatWeight(history.cisa_kev_weight)}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* 風險分數變化指示 */}
                    {previous && (
                      <div className="mt-3 flex items-center space-x-2 text-xs">
                        {history.final_risk_score > previous.final_risk_score ? (
                          <>
                            <span className="text-red-600">↑</span>
                            <span className="text-red-600">
                              增加{" "}
                              {(history.final_risk_score - previous.final_risk_score).toFixed(2)}
                            </span>
                          </>
                        ) : history.final_risk_score < previous.final_risk_score ? (
                          <>
                            <span className="text-green-600">↓</span>
                            <span className="text-green-600">
                              減少{" "}
                              {(previous.final_risk_score - history.final_risk_score).toFixed(2)}
                            </span>
                          </>
                        ) : (
                          <span className="text-gray-500">無變化</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

