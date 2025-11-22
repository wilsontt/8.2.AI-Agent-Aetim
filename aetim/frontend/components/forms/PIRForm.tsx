/**
 * PIR 表單組件
 */

"use client";

import React, { useState, useEffect } from "react";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Button } from "@/components/ui/Button";
import type { CreatePIRRequest, UpdatePIRRequest, PIR } from "@/types/pir";

interface PIRFormProps {
  pir?: PIR;
  onSubmit: (data: CreatePIRRequest | UpdatePIRRequest) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export const PIRForm: React.FC<PIRFormProps> = ({ pir, onSubmit, onCancel, isLoading = false }) => {
  const [formData, setFormData] = useState<CreatePIRRequest>({
    name: "",
    description: "",
    priority: "中",
    condition_type: "產品名稱",
    condition_value: "",
    is_enabled: true,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (pir) {
      setFormData({
        name: pir.name,
        description: pir.description,
        priority: pir.priority,
        condition_type: pir.condition_type,
        condition_value: pir.condition_value,
        is_enabled: pir.is_enabled,
      });
    }
  }, [pir]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = "PIR 名稱不能為空";
    }

    if (!formData.description.trim()) {
      newErrors.description = "PIR 描述不能為空";
    }

    if (!formData.condition_value.trim()) {
      newErrors.condition_value = "條件值不能為空";
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
          label="PIR 名稱 *"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          error={errors.name}
          required
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">PIR 描述 *</label>
          <textarea
            className={`w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.description ? "border-red-500" : "border-gray-300"
            }`}
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            rows={3}
            required
          />
          {errors.description && <p className="mt-1 text-sm text-red-600">{errors.description}</p>}
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Select
            label="優先級 *"
            value={formData.priority}
            onChange={(e) =>
              setFormData({ ...formData, priority: e.target.value as "高" | "中" | "低" })
            }
            options={[
              { value: "高", label: "高" },
              { value: "中", label: "中" },
              { value: "低", label: "低" },
            ]}
            error={errors.priority}
            required
          />

          <Select
            label="條件類型 *"
            value={formData.condition_type}
            onChange={(e) => setFormData({ ...formData, condition_type: e.target.value })}
            options={[
              { value: "產品名稱", label: "產品名稱" },
              { value: "CVE 編號", label: "CVE 編號" },
              { value: "威脅類型", label: "威脅類型" },
              { value: "CVSS 分數", label: "CVSS 分數" },
            ]}
            error={errors.condition_type}
            required
          />
        </div>

        <Input
          label="條件值 *"
          value={formData.condition_value}
          onChange={(e) => setFormData({ ...formData, condition_value: e.target.value })}
          error={errors.condition_value}
          placeholder={
            formData.condition_type === "CVE 編號"
              ? "例如：CVE-2024-"
              : formData.condition_type === "CVSS 分數"
              ? "例如：> 7.0"
              : "例如：VMware"
          }
          required
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

