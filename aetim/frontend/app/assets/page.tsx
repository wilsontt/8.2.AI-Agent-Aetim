/**
 * 資產清單頁面
 */

"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Table } from "@/components/ui/Table";
import { Pagination } from "@/components/ui/Pagination";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { AssetForm } from "@/components/forms/AssetForm";
import {
  getAssets,
  createAsset,
  updateAsset,
  deleteAsset,
  batchDeleteAssets,
  type Asset,
  type AssetSearchParams,
  type CreateAssetRequest,
  type UpdateAssetRequest,
} from "@/lib/api/asset";

export default function AssetsPage() {
  const router = useRouter();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [sortBy, setSortBy] = useState<string | undefined>();
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showBatchDeleteModal, setShowBatchDeleteModal] = useState(false);
  const [currentAsset, setCurrentAsset] = useState<Asset | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 篩選狀態
  const [filters, setFilters] = useState<AssetSearchParams>({});

  useEffect(() => {
    loadAssets();
  }, [page, sortBy, sortOrder, filters]);

  const loadAssets = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: AssetSearchParams = {
        page,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder,
        ...filters,
      };

      const response = await getAssets(params);
      setAssets(response.data);
      setTotalCount(response.total_count);
      setTotalPages(response.total_pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入資產清單失敗");
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (key: string, order: "asc" | "desc") => {
    setSortBy(key);
    setSortOrder(order);
    setPage(1);
  };

  const handleRowClick = (row: Asset) => {
    router.push(`/assets/${row.id}`);
  };

  const handleRowSelect = (id: string, selected: boolean) => {
    const newSelected = new Set(selectedRows);
    if (selected) {
      newSelected.add(id);
    } else {
      newSelected.delete(id);
    }
    setSelectedRows(newSelected);
  };

  const handleCreate = async (data: CreateAssetRequest) => {
    try {
      setIsSubmitting(true);
      await createAsset(data);
      setShowCreateModal(false);
      loadAssets();
    } catch (err) {
      setError(err instanceof Error ? err.message : "建立資產失敗");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = (asset: Asset) => {
    setCurrentAsset(asset);
    setShowEditModal(true);
  };

  const handleUpdate = async (data: UpdateAssetRequest) => {
    if (!currentAsset) return;

    try {
      setIsSubmitting(true);
      await updateAsset(currentAsset.id, data);
      setShowEditModal(false);
      setCurrentAsset(null);
      loadAssets();
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新資產失敗");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!currentAsset) return;

    try {
      setIsSubmitting(true);
      await deleteAsset(currentAsset.id, true);
      setShowDeleteModal(false);
      setCurrentAsset(null);
      loadAssets();
    } catch (err) {
      setError(err instanceof Error ? err.message : "刪除資產失敗");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBatchDelete = async () => {
    if (selectedRows.size === 0) return;

    try {
      setIsSubmitting(true);
      await batchDeleteAssets(Array.from(selectedRows), true);
      setShowBatchDeleteModal(false);
      setSelectedRows(new Set());
      loadAssets();
    } catch (err) {
      setError(err instanceof Error ? err.message : "批次刪除資產失敗");
    } finally {
      setIsSubmitting(false);
    }
  };

  const tableHeaders = [
    { key: "host_name", label: "主機名稱", sortable: true },
    { key: "ip", label: "IP 位址", sortable: false },
    { key: "owner", label: "負責人", sortable: true },
    { key: "data_sensitivity", label: "資料敏感度", sortable: true },
    { key: "business_criticality", label: "業務關鍵性", sortable: true },
    { key: "is_public_facing", label: "對外暴露", sortable: false },
    { key: "actions", label: "操作", sortable: false },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">資產管理</h1>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => router.push("/assets/import")}>
            匯入資產
          </Button>
          <Button onClick={() => setShowCreateModal(true)}>新增資產</Button>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* 篩選區域 */}
      <div className="mb-4 rounded-lg border border-gray-200 bg-white p-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <input
            type="text"
            placeholder="搜尋產品名稱..."
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
            onChange={(e) => setFilters({ ...filters, product_name: e.target.value || undefined })}
          />
          <select
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
            onChange={(e) =>
              setFilters({
                ...filters,
                data_sensitivity: (e.target.value || undefined) as "高" | "中" | "低" | undefined,
              })
            }
          >
            <option value="">所有資料敏感度</option>
            <option value="高">高</option>
            <option value="中">中</option>
            <option value="低">低</option>
          </select>
          <select
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
            onChange={(e) =>
              setFilters({
                ...filters,
                is_public_facing:
                  e.target.value === "" ? undefined : e.target.value === "true",
              })
            }
          >
            <option value="">所有對外狀態</option>
            <option value="true">對外暴露</option>
            <option value="false">非對外暴露</option>
          </select>
          <div className="flex space-x-2">
            {selectedRows.size > 0 && (
              <Button
                variant="danger"
                size="sm"
                onClick={() => setShowBatchDeleteModal(true)}
              >
                批次刪除 ({selectedRows.size})
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* 表格 */}
      <div className="rounded-lg border border-gray-200 bg-white shadow">
        {loading ? (
          <div className="p-8 text-center text-gray-500">載入中...</div>
        ) : (
          <>
            <Table
              headers={tableHeaders}
              data={assets.map((asset) => ({
                id: asset.id,
                host_name: asset.host_name,
                ip: asset.ip || "-",
                owner: asset.owner,
                data_sensitivity: asset.data_sensitivity,
                business_criticality: asset.business_criticality,
                is_public_facing: asset.is_public_facing ? "是" : "否",
                actions: (
                  <div className="flex space-x-2" onClick={(e) => e.stopPropagation()}>
                    <button
                      className="text-blue-600 hover:text-blue-800 text-sm"
                      onClick={() => handleEdit(asset)}
                    >
                      編輯
                    </button>
                    <button
                      className="text-red-600 hover:text-red-800 text-sm"
                      onClick={() => {
                        setCurrentAsset(asset);
                        setShowDeleteModal(true);
                      }}
                    >
                      刪除
                    </button>
                  </div>
                ),
              }))}
              onSort={handleSort}
              sortBy={sortBy}
              sortOrder={sortOrder}
              onRowClick={handleRowClick}
              selectedRows={selectedRows}
              onRowSelect={handleRowSelect}
              selectable={true}
            />
            {totalPages > 0 && (
              <Pagination
                currentPage={page}
                totalPages={totalPages}
                pageSize={pageSize}
                totalCount={totalCount}
                onPageChange={setPage}
              />
            )}
          </>
        )}
      </div>

      {/* 建立資產模態 */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="新增資產"
        footer={
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              取消
            </Button>
          </div>
        }
      >
        <AssetForm
          onSubmit={handleCreate}
          onCancel={() => setShowCreateModal(false)}
          isLoading={isSubmitting}
        />
      </Modal>

      {/* 編輯資產模態 */}
      <Modal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setCurrentAsset(null);
        }}
        title="編輯資產"
        footer={
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setShowEditModal(false)}>
              取消
            </Button>
          </div>
        }
      >
        {currentAsset && (
          <AssetForm
            asset={currentAsset}
            onSubmit={handleUpdate}
            onCancel={() => {
              setShowEditModal(false);
              setCurrentAsset(null);
            }}
            isLoading={isSubmitting}
          />
        )}
      </Modal>

      {/* 刪除確認模態 */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setCurrentAsset(null);
        }}
        title="確認刪除"
        footer={
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setShowDeleteModal(false)}>
              取消
            </Button>
            <Button variant="danger" onClick={handleDelete} isLoading={isSubmitting}>
              確認刪除
            </Button>
          </div>
        }
      >
        <p>確定要刪除資產「{currentAsset?.host_name}」嗎？此操作無法復原。</p>
      </Modal>

      {/* 批次刪除確認模態 */}
      <Modal
        isOpen={showBatchDeleteModal}
        onClose={() => setShowBatchDeleteModal(false)}
        title="確認批次刪除"
        footer={
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setShowBatchDeleteModal(false)}>
              取消
            </Button>
            <Button variant="danger" onClick={handleBatchDelete} isLoading={isSubmitting}>
              確認刪除 ({selectedRows.size} 筆)
            </Button>
          </div>
        }
      >
        <p>確定要刪除選取的 {selectedRows.size} 筆資產嗎？此操作無法復原。</p>
      </Modal>
    </div>
  );
}

