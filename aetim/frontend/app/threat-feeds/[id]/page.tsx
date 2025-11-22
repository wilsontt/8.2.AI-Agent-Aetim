/**
 * 威脅情資來源詳情頁面
 */

"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { getThreatFeed, getCollectionStatus } from "@/lib/api/threat_feed";
import type { ThreatFeed, CollectionStatusResponse } from "@/types/threat_feed";

export default function ThreatFeedDetailPage() {
  const params = useParams();
  const router = useRouter();
  const threatFeedId = params.id as string;

  const [threatFeed, setThreatFeed] = useState<ThreatFeed | null>(null);
  const [collectionStatus, setCollectionStatus] = useState<CollectionStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (threatFeedId) {
      loadThreatFeed();
      loadCollectionStatus();
    }
  }, [threatFeedId]);

  const loadThreatFeed = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getThreatFeed(threatFeedId);
      setThreatFeed(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入威脅情資來源詳情失敗");
    } finally {
      setLoading(false);
    }
  };

  const loadCollectionStatus = async () => {
    try {
      const statuses = await getCollectionStatus(threatFeedId);
      if (statuses.length > 0) {
        setCollectionStatus(statuses[0]);
      }
    } catch (err) {
      console.error("載入收集狀態失敗:", err);
    }
  };

  const getStatusBadge = (status?: string) => {
    if (!status) return <span className="text-gray-500">-</span>;
    const statusMap: Record<string, { label: string; color: string }> = {
      success: { label: "成功", color: "bg-green-100 text-green-800" },
      failed: { label: "失敗", color: "bg-red-100 text-red-800" },
      in_progress: { label: "進行中", color: "bg-blue-100 text-blue-800" },
    };
    const statusInfo = statusMap[status] || { label: status, color: "bg-gray-100 text-gray-800" };
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.color}`}>
        {statusInfo.label}
      </span>
    );
  };

  const formatDateTime = (dateTime?: string) => {
    if (!dateTime) return "-";
    return new Date(dateTime).toLocaleString("zh-TW");
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-gray-500">載入中...</div>
      </div>
    );
  }

  if (error || !threatFeed) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error || "威脅情資來源不存在"}</p>
        </div>
        <Button variant="outline" onClick={() => router.push("/threat-feeds")} className="mt-4">
          返回清單
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">威脅情資來源詳情</h1>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => router.push("/threat-feeds")}>
            返回清單
          </Button>
          <Button variant="outline" onClick={() => router.push(`/threat-feeds/${threatFeed.id}/edit`)}>
            編輯
          </Button>
        </div>
      </div>

      <div className="space-y-6">
        {/* 基本資訊 */}
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">基本資訊</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">來源名稱</dt>
                <dd className="mt-1 text-sm text-gray-900">{threatFeed.name}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">優先級</dt>
                <dd className="mt-1 text-sm text-gray-900">{threatFeed.priority}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">啟用狀態</dt>
                <dd className="mt-1 text-sm text-gray-900">{threatFeed.is_enabled ? "啟用" : "停用"}</dd>
              </div>
            </dl>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">收集頻率</dt>
                <dd className="mt-1 text-sm text-gray-900">{threatFeed.collection_frequency || "-"}</dd>
              </div>
              {threatFeed.description && (
                <div>
                  <dt className="text-sm font-medium text-gray-500">描述</dt>
                  <dd className="mt-1 text-sm text-gray-900">{threatFeed.description}</dd>
                </div>
              )}
            </dl>
          </div>
        </div>

        {/* 收集狀態 */}
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">收集狀態</h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-gray-500">最後收集時間</dt>
              <dd className="mt-1 text-sm text-gray-900">
                {formatDateTime(collectionStatus?.last_collection_time || threatFeed.last_collection_time)}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">收集狀態</dt>
              <dd className="mt-1">
                {getStatusBadge(collectionStatus?.last_collection_status || threatFeed.last_collection_status)}
              </dd>
            </div>
            {(collectionStatus?.last_collection_error || threatFeed.last_collection_error) && (
              <div>
                <dt className="text-sm font-medium text-gray-500">錯誤訊息</dt>
                <dd className="mt-1 text-sm text-red-600">
                  {collectionStatus?.last_collection_error || threatFeed.last_collection_error}
                </dd>
              </div>
            )}
          </dl>
        </div>

        {/* 收集策略 */}
        {threatFeed.collection_strategy && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">收集策略</h2>
            <p className="text-sm text-gray-900 whitespace-pre-wrap">{threatFeed.collection_strategy}</p>
          </div>
        )}
      </div>
    </div>
  );
}

