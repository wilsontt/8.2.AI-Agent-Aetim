/**
 * 系統設定頁面
 * 
 * 提供系統設定的集中管理介面。
 * 符合 AC-024-1, AC-024-2, AC-024-3, AC-024-4。
 */

"use client";

import React, { useState, useEffect } from "react";
import { usePermission } from "@/hooks/usePermission";
import { PermissionGate } from "@/components/auth/PermissionGate";
import {
  getSystemConfigurations,
  updateSystemConfigurationsBatch,
  type SystemConfiguration,
  type SystemConfigurationUpdateRequest,
} from "@/lib/api/system_configuration";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";

// 設定類別（符合 AC-024-2）
const CATEGORIES = [
  { id: "threat_feed", name: "威脅情資來源訂閱", description: "管理威脅情資來源的訂閱設定" },
  { id: "notification_rule", name: "通知規則", description: "管理通知規則的設定" },
  { id: "report_schedule", name: "報告排程", description: "管理報告生成的排程設定" },
  { id: "data_retention", name: "資料保留政策", description: "管理資料保留政策的設定" },
];

export default function SettingsPage() {
  const { hasPermission } = usePermission();
  const [configurations, setConfigurations] = useState<SystemConfiguration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [editedConfigs, setEditedConfigs] = useState<Map<string, SystemConfigurationUpdateRequest>>(
    new Map(),
  );
  const [hasChanges, setHasChanges] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadConfigurations();
  }, [selectedCategory]);

  /**
   * 載入系統設定
   */
  const loadConfigurations = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await getSystemConfigurations(selectedCategory || undefined);
      setConfigurations(response.configurations);
      setEditedConfigs(new Map());
      setHasChanges(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入系統設定失敗");
    } finally {
      setLoading(false);
    }
  };

  /**
   * 處理設定值變更
   */
  const handleConfigChange = (key: string, value: string, description?: string, category?: string) => {
    const config = configurations.find((c) => c.key === key);
    if (!config) {
      return;
    }

    const editedConfig: SystemConfigurationUpdateRequest = {
      key,
      value,
      description: description || config.description,
      category: category || config.category,
    };

    const newEditedConfigs = new Map(editedConfigs);
    newEditedConfigs.set(key, editedConfig);
    setEditedConfigs(newEditedConfigs);
    setHasChanges(true);
  };

  /**
   * 處理儲存（符合 AC-024-3：在儲存設定前要求使用者確認）
   */
  const handleSave = () => {
    if (editedConfigs.size === 0) {
      return;
    }
    setShowConfirmModal(true);
  };

  /**
   * 確認儲存
   */
  const handleConfirmSave = async () => {
    try {
      setIsSubmitting(true);
      setError(null);

      const configsArray = Array.from(editedConfigs.values());
      await updateSystemConfigurationsBatch({
        configurations: configsArray,
      });

      setShowConfirmModal(false);
      setEditedConfigs(new Map());
      setHasChanges(false);
      await loadConfigurations();
    } catch (err) {
      setError(err instanceof Error ? err.message : "儲存系統設定失敗");
    } finally {
      setIsSubmitting(false);
    }
  };

  /**
   * 處理取消（符合 AC-024-4：提供「取消」按鈕，允許使用者放棄變更）
   */
  const handleCancel = () => {
    setEditedConfigs(new Map());
    setHasChanges(false);
    loadConfigurations();
  };

  /**
   * 取得類別的設定
   */
  const getCategoryConfigs = (categoryId: string) => {
    return configurations.filter((c) => c.category === categoryId);
  };

  return (
    <PermissionGate permissions={["system_config:view"]}>
      <div className="container mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">系統設定</h1>
          <p className="mt-2 text-gray-600">
            管理系統的各項設定（符合 AC-024-1：提供系統設定的集中管理介面）
          </p>
        </div>

        {/* 錯誤訊息 */}
        {error && (
          <div className="mb-4 rounded-md bg-red-50 p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">錯誤</h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 設定類別分頁（符合 AC-024-2：支援所有設定類別） */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setSelectedCategory(null)}
              className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                selectedCategory === null
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
              }`}
            >
              全部
            </button>
            {CATEGORIES.map((category) => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium ${
                  selectedCategory === category.id
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
                }`}
              >
                {category.name}
              </button>
            ))}
          </nav>
        </div>

        {/* 設定內容 */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
              <p className="mt-4 text-gray-600">載入中...</p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* 顯示選定類別或所有類別的設定 */}
            {selectedCategory ? (
              <CategorySettings
                category={CATEGORIES.find((c) => c.id === selectedCategory)!}
                configs={getCategoryConfigs(selectedCategory)}
                editedConfigs={editedConfigs}
                onConfigChange={handleConfigChange}
              />
            ) : (
              CATEGORIES.map((category) => (
                <CategorySettings
                  key={category.id}
                  category={category}
                  configs={getCategoryConfigs(category.id)}
                  editedConfigs={editedConfigs}
                  onConfigChange={handleConfigChange}
                />
              ))
            )}

            {/* 操作按鈕（符合 AC-024-3, AC-024-4） */}
            {hasChanges && (
              <div className="flex justify-end space-x-4 border-t border-gray-200 pt-6">
                <Button
                  onClick={handleCancel}
                  variant="secondary"
                  disabled={isSubmitting}
                >
                  取消
                </Button>
                <PermissionGate permissions={["system_config:update"]}>
                  <Button
                    onClick={handleSave}
                    disabled={isSubmitting}
                  >
                    儲存變更
                  </Button>
                </PermissionGate>
              </div>
            )}
          </div>
        )}

        {/* 確認儲存對話框（符合 AC-024-3：在儲存設定前要求使用者確認） */}
        <Modal
          isOpen={showConfirmModal}
          onClose={() => setShowConfirmModal(false)}
          title="確認儲存"
        >
          <div className="space-y-4">
            <p className="text-gray-700">
              您確定要儲存這些變更嗎？此操作將更新 {editedConfigs.size} 個系統設定。
            </p>
            <div className="flex justify-end space-x-4">
              <Button
                onClick={() => setShowConfirmModal(false)}
                variant="secondary"
                disabled={isSubmitting}
              >
                取消
              </Button>
              <Button
                onClick={handleConfirmSave}
                disabled={isSubmitting}
              >
                {isSubmitting ? "儲存中..." : "確認儲存"}
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    </PermissionGate>
  );
}

/**
 * 類別設定元件
 */
function CategorySettings({
  category,
  configs,
  editedConfigs,
  onConfigChange,
}: {
  category: { id: string; name: string; description: string };
  configs: SystemConfiguration[];
  editedConfigs: Map<string, SystemConfigurationUpdateRequest>;
  onConfigChange: (key: string, value: string, description?: string, category?: string) => void;
}) {
  if (configs.length === 0) {
    return null;
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6">
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-gray-900">{category.name}</h2>
        <p className="mt-1 text-sm text-gray-600">{category.description}</p>
      </div>

      <div className="space-y-4">
        {configs.map((config) => {
          const editedConfig = editedConfigs.get(config.key);
          const currentValue = editedConfig?.value ?? config.value;
          const currentDescription = editedConfig?.description ?? config.description;

          return (
            <div key={config.key} className="border-b border-gray-100 pb-4 last:border-b-0">
              <div className="mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  {config.key}
                </label>
                {currentDescription && (
                  <p className="mt-1 text-xs text-gray-500">{currentDescription}</p>
                )}
              </div>
              <Input
                type="text"
                value={currentValue}
                onChange={(e) =>
                  onConfigChange(config.key, e.target.value, currentDescription, config.category)
                }
                className="w-full"
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

