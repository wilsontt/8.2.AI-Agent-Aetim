/**
 * 資產詳情頁面
 */

"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { getAsset, deleteAsset } from "@/lib/api/asset";
import type { Asset } from "@/types/asset";

export default function AssetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const assetId = params.id as string;

  const [asset, setAsset] = useState<Asset | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (assetId) {
      loadAsset();
    }
  }, [assetId]);

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

