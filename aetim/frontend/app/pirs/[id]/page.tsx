/**
 * PIR 詳情頁面
 */

"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { getPIR } from "@/lib/api/pir";
import type { PIR } from "@/types/pir";

export default function PIRDetailPage() {
  const params = useParams();
  const router = useRouter();
  const pirId = params.id as string;

  const [pir, setPIR] = useState<PIR | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (pirId) {
      loadPIR();
    }
  }, [pirId]);

  const loadPIR = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getPIR(pirId);
      setPIR(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入 PIR 詳情失敗");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-gray-500">載入中...</div>
      </div>
    );
  }

  if (error || !pir) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error || "PIR 不存在"}</p>
        </div>
        <Button variant="outline" onClick={() => router.push("/pirs")} className="mt-4">
          返回清單
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">PIR 詳情</h1>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => router.push("/pirs")}>
            返回清單
          </Button>
          <Button variant="outline" onClick={() => router.push(`/pirs/${pir.id}/edit`)}>
            編輯
          </Button>
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div>
            <h2 className="mb-4 text-lg font-semibold text-gray-900">基本資訊</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">PIR 名稱</dt>
                <dd className="mt-1 text-sm text-gray-900">{pir.name}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">優先級</dt>
                <dd className="mt-1 text-sm text-gray-900">{pir.priority}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">啟用狀態</dt>
                <dd className="mt-1 text-sm text-gray-900">{pir.is_enabled ? "啟用" : "停用"}</dd>
              </div>
            </dl>
          </div>

          <div>
            <h2 className="mb-4 text-lg font-semibold text-gray-900">條件設定</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">條件類型</dt>
                <dd className="mt-1 text-sm text-gray-900">{pir.condition_type}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">條件值</dt>
                <dd className="mt-1 text-sm text-gray-900">{pir.condition_value}</dd>
              </div>
            </dl>
          </div>
        </div>

        <div className="mt-6">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">描述</h2>
          <p className="text-sm text-gray-900 whitespace-pre-wrap">{pir.description}</p>
        </div>
      </div>
    </div>
  );
}

