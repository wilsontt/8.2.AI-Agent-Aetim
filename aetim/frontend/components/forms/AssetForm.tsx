/**
 * 資產表單組件
 */

"use client";

import React, { useState, useEffect } from "react";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import type { CreateAssetRequest, UpdateAssetRequest, Asset } from "@/types/asset";

interface AssetFormProps {
  asset?: Asset;
  onSubmit: (data: CreateAssetRequest | UpdateAssetRequest) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export const AssetForm: React.FC<AssetFormProps> = ({
  asset,
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<CreateAssetRequest>({
    host_name: "",
    ip: "",
    operating_system: "",
    running_applications: "",
    owner: "",
    data_sensitivity: "中",
    is_public_facing: false,
    business_criticality: "中",
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (asset) {
      setFormData({
        host_name: asset.host_name,
        ip: asset.ip || "",
        operating_system: asset.operating_system,
        running_applications: asset.running_applications,
        owner: asset.owner,
        data_sensitivity: asset.data_sensitivity,
        is_public_facing: asset.is_public_facing,
        business_criticality: asset.business_criticality,
      });
    }
  }, [asset]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.host_name.trim()) {
      newErrors.host_name = "主機名稱不能為空";
    }

    if (!formData.operating_system.trim()) {
      newErrors.operating_system = "作業系統不能為空";
    }

    if (!formData.running_applications.trim()) {
      newErrors.running_applications = "運行的應用程式不能為空";
    }

    if (!formData.owner.trim()) {
      newErrors.owner = "負責人不能為空";
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
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input
          label="主機名稱 *"
          value={formData.host_name}
          onChange={(e) => setFormData({ ...formData, host_name: e.target.value })}
          error={errors.host_name}
          required
        />

        <Input
          label="IP 位址"
          value={formData.ip}
          onChange={(e) => setFormData({ ...formData, ip: e.target.value })}
          error={errors.ip}
        />

        <Input
          label="作業系統（含版本） *"
          value={formData.operating_system}
          onChange={(e) => setFormData({ ...formData, operating_system: e.target.value })}
          error={errors.operating_system}
          required
        />

        <Input
          label="負責人 *"
          value={formData.owner}
          onChange={(e) => setFormData({ ...formData, owner: e.target.value })}
          error={errors.owner}
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          運行的應用程式（含版本） *
        </label>
        <textarea
          className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            errors.running_applications ? "border-red-500" : "border-gray-300"
          }`}
          value={formData.running_applications}
          onChange={(e) => setFormData({ ...formData, running_applications: e.target.value })}
          rows={3}
          required
        />
        {errors.running_applications && (
          <p className="mt-1 text-sm text-red-600">{errors.running_applications}</p>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Select
          label="資料敏感度 *"
          value={formData.data_sensitivity}
          onChange={(e) =>
            setFormData({ ...formData, data_sensitivity: e.target.value as "高" | "中" | "低" })
          }
          options={[
            { value: "高", label: "高" },
            { value: "中", label: "中" },
            { value: "低", label: "低" },
          ]}
          error={errors.data_sensitivity}
          required
        />

        <Select
          label="業務關鍵性 *"
          value={formData.business_criticality}
          onChange={(e) =>
            setFormData({
              ...formData,
              business_criticality: e.target.value as "高" | "中" | "低",
            })
          }
          options={[
            { value: "高", label: "高" },
            { value: "中", label: "中" },
            { value: "低", label: "低" },
          ]}
          error={errors.business_criticality}
          required
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            是否對外暴露 *
          </label>
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={formData.is_public_facing ? "true" : "false"}
            onChange={(e) => setFormData({ ...formData, is_public_facing: e.target.value === "true" })}
            required
          >
            <option value="false">否 (N)</option>
            <option value="true">是 (Y)</option>
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

