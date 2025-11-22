/**
 * 威脅情資來源清單頁面
 */

"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Table } from "@/components/ui/Table";
import { Pagination } from "@/components/ui/Pagination";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { ThreatFeedForm } from "@/components/forms/ThreatFeedForm";
import {
  getThreatFeeds,
  createThreatFeed,
  updateThreatFeed,
  deleteThreatFeed,
  toggleThreatFeed,
  getCollectionStatus,
  type ThreatFeed,
  type CreateThreatFeedRequest,
  type UpdateThreatFeedRequest,
  type CollectionStatusResponse,
} from "@/lib/api/threat_feed";

export default function ThreatFeedsPage() {
  const router = useRouter();
  const [threatFeeds, setThreatFeeds] = useState<ThreatFeed[]>([]);
  const [collectionStatuses, setCollectionStatuses] = useState<Record<string, CollectionStatusResponse>>({});
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
  const [currentThreatFeed, setCurrentThreatFeed] = useState<ThreatFeed | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadThreatFeeds();
    loadCollectionStatuses();
  }, [page, sortBy, sortOrder]);

  const loadThreatFeeds = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await getThreatFeeds(page, pageSize, sortBy, sortOrder);
      setThreatFeeds(response.data);
      setTotalCount(response.total_count);
      setTotalPages(response.total_pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入威脅情資來源清單失敗");
    } finally {
      setLoading(false);
    }
  };

  const loadCollectionStatuses = async () => {
    try {
      const statuses = await getCollectionStatus();
      const statusMap: Record<string, CollectionStatusResponse> = {};
      statuses.forEach((status) => {
        statusMap[status.threat_feed_id] = status;
      });
      setCollectionStatuses(statusMap);
    } catch (err) {
      console.error("載入收集狀態失敗:", err);
    }
  };

  const handleSort = (key: string, order: "asc" | "desc") => {
    setSortBy(key);
    setSortOrder(order);
    setPage(1);
  };

  const handleRowClick = (row: ThreatFeed) => {
    router.push(`/threat-feeds/${row.id}`);
  };

  const handleCreate = async (data: CreateThreatFeedRequest) => {
    try {
      setIsSubmitting(true);
      await createThreatFeed(data);
      setShowCreateModal(false);
      loadThreatFeeds();
      loadCollectionStatuses();
    } catch (err) {
      setError(err instanceof Error ? err.message : "建立威脅情資來源失敗");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = (threatFeed: ThreatFeed) => {
    setCurrentThreatFeed(threatFeed);
    setShowEditModal(true);
  };

  const handleUpdate = async (data: UpdateThreatFeedRequest) => {
    if (!currentThreatFeed) return;

    try {
      setIsSubmitting(true);
      await updateThreatFeed(currentThreatFeed.id, data);
      setShowEditModal(false);
      setCurrentThreatFeed(null);
      loadThreatFeeds();
      loadCollectionStatuses();
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新威脅情資來源失敗");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!currentThreatFeed) return;

    try {
      setIsSubmitting(true);
      await deleteThreatFeed(currentThreatFeed.id);
      setShowDeleteModal(false);
      setCurrentThreatFeed(null);
      loadThreatFeeds();
      loadCollectionStatuses();
    } catch (err) {
      setError(err instanceof Error ? err.message : "刪除威脅情資來源失敗");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggle = async (threatFeed: ThreatFeed) => {
    try {
      await toggleThreatFeed(threatFeed.id);
      loadThreatFeeds();
      loadCollectionStatuses();
    } catch (err) {
      setError(err instanceof Error ? err.message : "切換威脅情資來源啟用狀態失敗");
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

  const tableHeaders = [
    { key: "name", label: "來源名稱", sortable: true },
    { key: "priority", label: "優先級", sortable: true },
    { key: "collection_frequency", label: "收集頻率", sortable: false },
    { key: "last_collection_time", label: "最後收集時間", sortable: false },
    { key: "last_collection_status", label: "收集狀態", sortable: false },
    { key: "is_enabled", label: "啟用狀態", sortable: false },
    { key: "actions", label: "操作", sortable: false },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">威脅情資來源管理</h1>
        <Button onClick={() => setShowCreateModal(true)}>新增威脅來源</Button>
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
              data={threatFeeds.map((feed) => {
                const status = collectionStatuses[feed.id];
                return {
                  id: feed.id,
                  name: feed.name,
                  priority: feed.priority,
                  collection_frequency: feed.collection_frequency || "-",
                  last_collection_time: formatDateTime(status?.last_collection_time || feed.last_collection_time),
                  last_collection_status: getStatusBadge(status?.last_collection_status || feed.last_collection_status),
                  is_enabled: feed.is_enabled ? "啟用" : "停用",
                  actions: (
                    <div className="flex space-x-2" onClick={(e) => e.stopPropagation()}>
                      <button
                        className="text-blue-600 hover:text-blue-800 text-sm"
                        onClick={() => handleEdit(feed)}
                      >
                        編輯
                      </button>
                      <button
                        className={`text-sm ${
                          feed.is_enabled ? "text-orange-600 hover:text-orange-800" : "text-green-600 hover:text-green-800"
                        }`}
                        onClick={() => handleToggle(feed)}
                      >
                        {feed.is_enabled ? "停用" : "啟用"}
                      </button>
                      <button
                        className="text-red-600 hover:text-red-800 text-sm"
                        onClick={() => {
                          setCurrentThreatFeed(feed);
                          setShowDeleteModal(true);
                        }}
                      >
                        刪除
                      </button>
                    </div>
                  ),
                };
              })}
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

      {/* 建立威脅來源模態 */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="新增威脅情資來源"
        footer={
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              取消
            </Button>
          </div>
        }
      >
        <ThreatFeedForm
          onSubmit={handleCreate}
          onCancel={() => setShowCreateModal(false)}
          isLoading={isSubmitting}
        />
      </Modal>

      {/* 編輯威脅來源模態 */}
      <Modal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setCurrentThreatFeed(null);
        }}
        title="編輯威脅情資來源"
        footer={
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setShowEditModal(false)}>
              取消
            </Button>
          </div>
        }
      >
        {currentThreatFeed && (
          <ThreatFeedForm
            threatFeed={currentThreatFeed}
            onSubmit={handleUpdate}
            onCancel={() => {
              setShowEditModal(false);
              setCurrentThreatFeed(null);
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
          setCurrentThreatFeed(null);
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
        <p>確定要刪除威脅情資來源「{currentThreatFeed?.name}」嗎？此操作無法復原。</p>
      </Modal>
    </div>
  );
}

