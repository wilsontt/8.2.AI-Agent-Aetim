/**
 * 風險趨勢分析組件
 * 
 * 顯示風險分數的趨勢分析，包含：
 * - 時間序列圖（風險分數隨時間變化）
 * - 風險等級分布圖（嚴重/高/中/低數量）
 * - 加權因子貢獻圖（各加權因子的平均貢獻）
 * - 統計資訊
 */

"use client";

import React, { useMemo } from "react";
import type { RiskAssessmentHistoryResponse, RiskLevel } from "@/types/risk_assessment";

interface RiskTrendAnalysisProps {
  histories: RiskAssessmentHistoryResponse[];
}

const getRiskLevelColor = (level: RiskLevel): string => {
  switch (level) {
    case "Critical":
      return "#ef4444"; // red-500
    case "High":
      return "#f97316"; // orange-500
    case "Medium":
      return "#f59e0b"; // yellow-500
    case "Low":
      return "#22c55e"; // green-500
    default:
      return "#6b7280"; // gray-500
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

export const RiskTrendAnalysis: React.FC<RiskTrendAnalysisProps> = ({ histories }) => {
  // 按時間排序（最舊的在前）
  const sortedHistories = useMemo(() => {
    return [...histories].sort((a, b) => {
      return new Date(a.calculated_at).getTime() - new Date(b.calculated_at).getTime();
    });
  }, [histories]);

  // 統計資訊
  const stats = useMemo(() => {
    if (sortedHistories.length === 0) {
      return {
        averageScore: 0,
        maxScore: 0,
        minScore: 0,
        trend: "持平" as "上升" | "下降" | "持平",
        levelDistribution: {
          Critical: 0,
          High: 0,
          Medium: 0,
          Low: 0,
        },
        averageWeights: {
          asset_importance: 0,
          asset_count: 0,
          pir_match: 0,
          cisa_kev: 0,
        },
      };
    }

    const scores = sortedHistories.map((h) => h.final_risk_score);
    const averageScore =
      scores.reduce((sum, score) => sum + score, 0) / scores.length;
    const maxScore = Math.max(...scores);
    const minScore = Math.min(...scores);

    // 計算趨勢
    let trend: "上升" | "下降" | "持平" = "持平";
    if (sortedHistories.length >= 2) {
      const firstScore = sortedHistories[0].final_risk_score;
      const lastScore = sortedHistories[sortedHistories.length - 1].final_risk_score;
      const diff = lastScore - firstScore;
      if (diff > 0.1) trend = "上升";
      else if (diff < -0.1) trend = "下降";
    }

    // 風險等級分布
    const levelDistribution = sortedHistories.reduce(
      (acc, h) => {
        acc[h.risk_level] = (acc[h.risk_level] || 0) + 1;
        return acc;
      },
      {} as Record<RiskLevel, number>,
    );

    // 平均加權因子
    const totalWeights = sortedHistories.reduce(
      (acc, h) => {
        acc.asset_importance += h.asset_importance_weight;
        acc.asset_count += h.asset_count_weight || 0;
        acc.pir_match += h.pir_match_weight || 0;
        acc.cisa_kev += h.cisa_kev_weight || 0;
        return acc;
      },
      {
        asset_importance: 0,
        asset_count: 0,
        pir_match: 0,
        cisa_kev: 0,
      },
    );

    const count = sortedHistories.length;
    const averageWeights = {
      asset_importance: totalWeights.asset_importance / count,
      asset_count: totalWeights.asset_count / count,
      pir_match: totalWeights.pir_match / count,
      cisa_kev: totalWeights.cisa_kev / count,
    };

    return {
      averageScore,
      maxScore,
      minScore,
      trend,
      levelDistribution: {
        Critical: levelDistribution.Critical || 0,
        High: levelDistribution.High || 0,
        Medium: levelDistribution.Medium || 0,
        Low: levelDistribution.Low || 0,
      },
      averageWeights,
    };
  }, [sortedHistories]);

  // 時間序列圖表數據
  const timeSeriesData = useMemo(() => {
    return sortedHistories.map((h) => ({
      date: new Date(h.calculated_at),
      score: h.final_risk_score,
      level: h.risk_level,
    }));
  }, [sortedHistories]);

  // 繪製時間序列圖表
  const renderTimeSeriesChart = () => {
    if (timeSeriesData.length === 0) {
      return (
        <div className="flex h-64 items-center justify-center text-gray-500">
          沒有足夠的數據繪製圖表
        </div>
      );
    }

    const width = 800;
    const height = 300;
    const padding = { top: 20, right: 20, bottom: 40, left: 60 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    const minScore = Math.min(...timeSeriesData.map((d) => d.score));
    const maxScore = Math.max(...timeSeriesData.map((d) => d.score));
    const scoreRange = maxScore - minScore || 10;
    const minY = Math.max(0, minScore - scoreRange * 0.1);
    const maxY = Math.min(10, maxScore + scoreRange * 0.1);

    const xScale = (index: number) =>
      padding.left + (index / (timeSeriesData.length - 1 || 1)) * chartWidth;
    const yScale = (score: number) =>
      padding.top +
      chartHeight -
      ((score - minY) / (maxY - minY || 1)) * chartHeight;

    // 繪製網格線
    const gridLines = [];
    for (let i = 0; i <= 5; i++) {
      const y = padding.top + (chartHeight / 5) * i;
      const value = maxY - (maxY - minY) * (i / 5);
      gridLines.push(
        <g key={`grid-${i}`}>
          <line
            x1={padding.left}
            y1={y}
            x2={padding.left + chartWidth}
            y2={y}
            stroke="#e5e7eb"
            strokeWidth={1}
          />
          <text
            x={padding.left - 10}
            y={y + 4}
            textAnchor="end"
            fontSize="12"
            fill="#6b7280"
          >
            {value.toFixed(1)}
          </text>
        </g>,
      );
    }

    // 繪製數據點和線
    const points = timeSeriesData.map((d, i) => ({
      x: xScale(i),
      y: yScale(d.score),
      score: d.score,
      level: d.level,
      date: d.date,
    }));

    const pathData = points
      .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`)
      .join(" ");

    return (
      <div className="overflow-x-auto">
        <svg width={width} height={height} className="border border-gray-200 rounded-lg">
          {gridLines}
          {/* 繪製線 */}
          <path
            d={pathData}
            fill="none"
            stroke="#3b82f6"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* 繪製數據點 */}
          {points.map((p, i) => (
            <g key={i}>
              <circle
                cx={p.x}
                cy={p.y}
                r={4}
                fill={getRiskLevelColor(p.level)}
                stroke="white"
                strokeWidth={2}
              />
              <title>
                {p.date.toLocaleString("zh-TW")}: {p.score.toFixed(2)} ({getRiskLevelLabel(p.level)})
              </title>
            </g>
          ))}
          {/* X 軸標籤 */}
          {timeSeriesData.map((d, i) => {
            if (i % Math.ceil(timeSeriesData.length / 5) !== 0 && i !== timeSeriesData.length - 1)
              return null;
            return (
              <text
                key={i}
                x={xScale(i)}
                y={height - padding.bottom + 20}
                textAnchor="middle"
                fontSize="10"
                fill="#6b7280"
              >
                {d.date.toLocaleDateString("zh-TW", { month: "short", day: "numeric" })}
              </text>
            );
          })}
          {/* Y 軸標籤 */}
          <text
            x={padding.left - 30}
            y={height / 2}
            textAnchor="middle"
            fontSize="12"
            fill="#6b7280"
            transform={`rotate(-90, ${padding.left - 30}, ${height / 2})`}
          >
            風險分數
          </text>
        </svg>
      </div>
    );
  };

  // 繪製風險等級分布圖
  const renderLevelDistributionChart = () => {
    const levels: RiskLevel[] = ["Critical", "High", "Medium", "Low"];
    const maxCount = Math.max(...levels.map((l) => stats.levelDistribution[l] || 0), 1);

    return (
      <div className="space-y-3">
        {levels.map((level) => {
          const count = stats.levelDistribution[level] || 0;
          const percentage = maxCount > 0 ? (count / maxCount) * 100 : 0;
          return (
            <div key={level} className="flex items-center space-x-3">
              <div className="w-20 text-sm font-medium text-gray-700">
                {getRiskLevelLabel(level)}
              </div>
              <div className="flex-1">
                <div className="h-6 rounded-md bg-gray-200 overflow-hidden">
                  <div
                    className="h-full flex items-center justify-end pr-2 text-xs font-semibold text-white"
                    style={{
                      width: `${percentage}%`,
                      backgroundColor: getRiskLevelColor(level),
                    }}
                  >
                    {count > 0 && count}
                  </div>
                </div>
              </div>
              <div className="w-16 text-right text-sm text-gray-600">{count} 次</div>
            </div>
          );
        })}
      </div>
    );
  };

  // 繪製加權因子貢獻圖
  const renderWeightContributionChart = () => {
    const weights = [
      { name: "資產重要性", value: stats.averageWeights.asset_importance, color: "#3b82f6" },
      { name: "資產數量", value: stats.averageWeights.asset_count, color: "#f59e0b" },
      { name: "PIR 符合度", value: stats.averageWeights.pir_match, color: "#a855f7" },
      { name: "CISA KEV", value: stats.averageWeights.cisa_kev, color: "#ef4444" },
    ];

    const totalWeight = weights.reduce((sum, w) => sum + w.value, 0);
    const maxWeight = Math.max(...weights.map((w) => w.value), 1);

    return (
      <div className="space-y-3">
        {weights.map((weight) => {
          const percentage = maxWeight > 0 ? (weight.value / maxWeight) * 100 : 0;
          const contribution = totalWeight > 0 ? (weight.value / totalWeight) * 100 : 0;
          return (
            <div key={weight.name} className="flex items-center space-x-3">
              <div className="w-24 text-sm font-medium text-gray-700">{weight.name}</div>
              <div className="flex-1">
                <div className="h-6 rounded-md bg-gray-200 overflow-hidden">
                  <div
                    className="h-full flex items-center justify-end pr-2 text-xs font-semibold text-white"
                    style={{
                      width: `${percentage}%`,
                      backgroundColor: weight.color,
                    }}
                  >
                    {weight.value > 0 && weight.value.toFixed(2)}
                  </div>
                </div>
              </div>
              <div className="w-20 text-right text-sm text-gray-600">
                {contribution > 0 ? `${contribution.toFixed(1)}%` : "-"}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  if (sortedHistories.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-gray-500">沒有足夠的歷史記錄進行趨勢分析</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 統計資訊 */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="text-sm font-medium text-gray-500">平均風險分數</div>
          <div className="mt-2 text-2xl font-bold text-gray-900">
            {stats.averageScore.toFixed(2)}
          </div>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="text-sm font-medium text-gray-500">最高風險分數</div>
          <div className="mt-2 text-2xl font-bold text-red-600">{stats.maxScore.toFixed(2)}</div>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="text-sm font-medium text-gray-500">最低風險分數</div>
          <div className="mt-2 text-2xl font-bold text-green-600">{stats.minScore.toFixed(2)}</div>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="text-sm font-medium text-gray-500">趨勢</div>
          <div className="mt-2">
            <span
              className={`inline-flex rounded-full px-3 py-1 text-sm font-semibold ${
                stats.trend === "上升"
                  ? "bg-red-100 text-red-800"
                  : stats.trend === "下降"
                    ? "bg-green-100 text-green-800"
                    : "bg-gray-100 text-gray-800"
              }`}
            >
              {stats.trend === "上升" && "↑"} {stats.trend === "下降" && "↓"}{" "}
              {stats.trend === "持平" && "→"} {stats.trend}
            </span>
          </div>
        </div>
      </div>

      {/* 時間序列圖表 */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">風險分數時間序列</h3>
        {renderTimeSeriesChart()}
      </div>

      {/* 風險等級分布 */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">風險等級分布</h3>
        {renderLevelDistributionChart()}
      </div>

      {/* 加權因子貢獻 */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">平均加權因子貢獻</h3>
        {renderWeightContributionChart()}
      </div>
    </div>
  );
};

