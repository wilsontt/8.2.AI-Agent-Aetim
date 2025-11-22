/**
 * 威脅情資來源表單組件
 */

"use client";

import React, { useState, useEffect } from "react";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import type {
  CreateThreatFeedRequest,
  UpdateThreatFeedRequest,
  ThreatFeed,
} from "@/types/threat_feed";

interface ThreatFeedFormProps {
  threatFeed?: ThreatFeed;
  onSubmit: (data: CreateThreatFeedRequest | UpdateThreatFeedRequest) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export const ThreatFeedForm: React.FC<ThreatFeedFormProps> = ({
  threatFeed,
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<CreateThreatFeedRequest>({
    name: "",
    description: "",
    priority: "P1",
    collection_frequency: "每日",
    collection_strategy: "",
    api_key: "",
    is_enabled: true,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (threatFeed) {
      setFormData({
        name: threatFeed.name,
        description: threatFeed.description || "",
        priority: threatFeed.priority,
        collection_frequency: threatFeed.collection_frequency || "每日",
        collection_strategy: threatFeed.collection_strategy || "",
        api_key: "",
        is_enabled: threatFeed.is_enabled,
      });
    }
  }, [threatFeed]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "威脅情資來源名稱不能為空";
    }

    if (!formData.collection_frequency) {
      newErrors.collection_frequency = "收集頻率不能為空";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    try {
      await onSubmit(formData);
    } catch (error) {
      console.error("提交表單失敗:", error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 gap-4">
        <Input
          label="來源名稱 *"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          error={errors.name}
          placeholder="例如：CISA KEV、NVD、VMware VMSA"
          required
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">來源描述</label>
          <textarea
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            rows={2}
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Select
            label="優先級 *"
            value={formData.priority}
            onChange={(e) =>
              setFormData({ ...formData, priority: e.target.value as "P0" | "P1" | "P2" | "P3" })
            }
            options={[
              { value: "P0", label: "P0 (緊急)" },
              { value: "P1", label: "P1 (高)" },
              { value: "P2", label: "P2 (中)" },
              { value: "P3", label: "P3 (低)" },
            ]}
            error={errors.priority}
            required
          />

          <Select
            label="收集頻率 *"
            value={formData.collection_frequency}
            onChange={(e) => setFormData({ ...formData, collection_frequency: e.target.value })}
            options={[
              { value: "每小時", label: "每小時" },
              { value: "每日", label: "每日" },
              { value: "每週", label: "每週" },
              { value: "每月", label: "每月" },
            ]}
            error={errors.collection_frequency}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">收集策略</label>
          <textarea
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={formData.collection_strategy}
            onChange={(e) => setFormData({ ...formData, collection_strategy: e.target.value })}
            rows={3}
            placeholder="例如：API / JSON Feed - 最高優先級，任何匹配資產的 CVE 將觸發即時緊急警報"
          />
        </div>

        <Input
          label="API 金鑰（可選）"
          type="password"
          value={formData.api_key}
          onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
          error={errors.api_key}
          placeholder="如來源需要 API 金鑰或認證資訊"
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">啟用狀態 *</label>
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={formData.is_enabled ? "true" : "false"}
            onChange={(e) => setFormData({ ...formData, is_enabled: e.target.value === "true" })}
            required
          >
            <option value="true">啟用</option>
            <option value="false">停用</option>
          </select>
        </div>
      </div>

      <div className="flex justify-end space-x-3 pt-4">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          取消
        </Button>
        <Button type="submit" isLoading={isLoading}>
          儲存
        </Button>
      </div>
    </form>
  );
};

