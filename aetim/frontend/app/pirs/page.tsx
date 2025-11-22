/**
 * PIR 清單頁面
 */

"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Table } from "@/components/ui/Table";
import { Pagination } from "@/components/ui/Pagination";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { PIRForm } from "@/components/forms/PIRForm";
import {
  getPIRs,
  createPIR,
  updatePIR,
  deletePIR,
  togglePIR,
  type PIR,
  type CreatePIRRequest,
  type UpdatePIRRequest,
} from "@/lib/api/pir";

export default function PIRsPage() {
  const router = useRouter();
  const [pirs, setPIRs] = useState<PIR[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [sortBy, setSortBy] = useState<string | undefined>();
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [currentPIR, setCurrentPIR] = useState<PIR | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadPIRs();
  }, [page, sortBy, sortOrder]);

  const loadPIRs = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await getPIRs(page, pageSize, sortBy, sortOrder);
      setPIRs(response.data);
      setTotalCount(response.total_count);
      setTotalPages(response.total_pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入 PIR 清單失敗");
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (key: string, order: "asc" | "desc") => {
    setSortBy(key);
    setSortOrder(order);
    setPage(1);
  };

  const handleRowClick = (row: PIR) => {
    router.push(`/pirs/${row.id}`);
  };

  const handleCreate = async (data: CreatePIRRequest) => {
    try {
      setIsSubmitting(true);
      await createPIR(data);
      setShowCreateModal(false);
      loadPIRs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "建立 PIR 失敗");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = (pir: PIR) => {
    setCurrentPIR(pir);
    setShowEditModal(true);
  };

  const handleUpdate = async (data: UpdatePIRRequest) => {
    if (!currentPIR) return;

    try {
      setIsSubmitting(true);
      await updatePIR(currentPIR.id, data);
      setShowEditModal(false);
      setCurrentPIR(null);
      loadPIRs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新 PIR 失敗");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!currentPIR) return;

    try {
      setIsSubmitting(true);
      await deletePIR(currentPIR.id);
      setShowDeleteModal(false);
      setCurrentPIR(null);
      loadPIRs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "刪除 PIR 失敗");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggle = async (pir: PIR) => {
    try {
      await togglePIR(pir.id);
      loadPIRs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "切換 PIR 啟用狀態失敗");
    }
  };

  const tableHeaders = [
    { key: "name", label: "PIR 名稱", sortable: true },
    { key: "priority", label: "優先級", sortable: true },
    { key: "condition_type", label: "條件類型", sortable: false },
    { key: "condition_value", label: "條件值", sortable: false },
    { key: "is_enabled", label: "啟用狀態", sortable: false },
    { key: "actions", label: "操作", sortable: false },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">優先情資需求 (PIR) 管理</h1>
        <Button onClick={() => setShowCreateModal(true)}>新增 PIR</Button>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* 表格 */}
      <div className="rounded-lg border border-gray-200 bg-white shadow">
        {loading ? (
          <div className="p-8 text-center text-gray-500">載入中...</div>
        ) : (
          <>
            <Table
              headers={tableHeaders}
              data={pirs.map((pir) => ({
                id: pir.id,
                name: pir.name,
                priority: pir.priority,
                condition_type: pir.condition_type,
                condition_value: pir.condition_value,
                is_enabled: pir.is_enabled ? "啟用" : "停用",
                actions: (
                  <div className="flex space-x-2" onClick={(e) => e.stopPropagation()}>
                    <button
                      className="text-blue-600 hover:text-blue-800 text-sm"
                      onClick={() => handleEdit(pir)}
                    >
                      編輯
                    </button>
                    <button
                      className={`text-sm ${
                        pir.is_enabled ? "text-orange-600 hover:text-orange-800" : "text-green-600 hover:text-green-800"
                      }`}
                      onClick={() => handleToggle(pir)}
                    >
                      {pir.is_enabled ? "停用" : "啟用"}
                    </button>
                    <button
                      className="text-red-600 hover:text-red-800 text-sm"
                      onClick={() => {
                        setCurrentPIR(pir);
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

      {/* 建立 PIR 模態 */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="新增 PIR"
        footer={
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              取消
            </Button>
          </div>
        }
      >
        <PIRForm
          onSubmit={handleCreate}
          onCancel={() => setShowCreateModal(false)}
          isLoading={isSubmitting}
        />
      </Modal>

      {/* 編輯 PIR 模態 */}
      <Modal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setCurrentPIR(null);
        }}
        title="編輯 PIR"
        footer={
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setShowEditModal(false)}>
              取消
            </Button>
          </div>
        }
      >
        {currentPIR && (
          <PIRForm
            pir={currentPIR}
            onSubmit={handleUpdate}
            onCancel={() => {
              setShowEditModal(false);
              setCurrentPIR(null);
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
          setCurrentPIR(null);
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
        <p>確定要刪除 PIR「{currentPIR?.name}」嗎？此操作無法復原。</p>
      </Modal>
    </div>
  );
}

