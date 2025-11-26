/**
 * 編輯通知規則頁面
 */

"use client";

import React, { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import {
  getNotificationRuleById,
  updateNotificationRule,
  type UpdateNotificationRuleRequest,
} from "@/lib/api/notification_rule";

export default function EditNotificationRulePage() {
  const router = useRouter();
  const params = useParams();
  const ruleId = params.id as string;

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 表單狀態
  const [formData, setFormData] = useState<UpdateNotificationRuleRequest>({
    recipients: [],
    risk_score_threshold: undefined,
    send_time: undefined,
    is_enabled: undefined,
  });

  // 通知類型（不可變更）
  const [notificationType, setNotificationType] = useState<string>("");

  // 載入通知規則
  useEffect(() => {
    const loadRule = async () => {
      try {
        setLoading(true);
        setError(null);

        const rule = await getNotificationRuleById(ruleId);
        setNotificationType(rule.notification_type);
        setFormData({
          recipients: rule.recipients,
          risk_score_threshold: rule.risk_score_threshold,
          send_time: rule.send_time,
          is_enabled: rule.is_enabled,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "載入通知規則失敗");
      } finally {
        setLoading(false);
      }
    };

    if (ruleId) {
      loadRule();
    }
  }, [ruleId]);

  // 處理表單變更
  const handleChange = (
    field: keyof UpdateNotificationRuleRequest,
    value: any,
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: "" }));
    setError(null);
  };

  // 處理收件人變更
  const handleRecipientsChange = (index: number, value: string) => {
    const newRecipients = [...(formData.recipients || [])];
    newRecipients[index] = value;
    setFormData((prev) => ({ ...prev, recipients: newRecipients }));
    setErrors((prev) => ({ ...prev, recipients: "" }));
  };

  // 新增收件人欄位
  const handleAddRecipient = () => {
    setFormData((prev) => ({
      ...prev,
      recipients: [...(prev.recipients || []), ""],
    }));
  };

  // 移除收件人欄位
  const handleRemoveRecipient = (index: number) => {
    if (formData.recipients && formData.recipients.length > 1) {
      const newRecipients = formData.recipients.filter((_, i) => i !== index);
      setFormData((prev) => ({ ...prev, recipients: newRecipients }));
    }
  };

  // 表單驗證
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    // 驗證收件人（AC-021-2）
    if (formData.recipients) {
      const validRecipients = formData.recipients.filter((r) => r.trim() !== "");
      if (validRecipients.length === 0) {
        newErrors.recipients = "至少需要一個收件人";
      } else {
        // 驗證 Email 格式
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        for (const recipient of validRecipients) {
          if (!emailRegex.test(recipient)) {
            newErrors.recipients = `無效的 Email 地址：${recipient}`;
            break;
          }
        }
      }
    }

    // 驗證風險分數閾值
    if (formData.risk_score_threshold !== undefined) {
      if (
        formData.risk_score_threshold < 0 ||
        formData.risk_score_threshold > 10
      ) {
        newErrors.risk_score_threshold =
          "風險分數閾值必須在 0.0 到 10.0 之間";
      }
    }

    // 驗證發送時間格式
    if (formData.send_time) {
      const timeRegex = /^([0-1][0-9]|2[0-3]):[0-5][0-9]$/;
      if (!timeRegex.test(formData.send_time)) {
        newErrors.send_time = "發送時間格式錯誤，應為 HH:MM";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 處理提交
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setSaving(true);
    setError(null);

    try {
      // 過濾空收件人（如果提供）
      const updateData: UpdateNotificationRuleRequest = { ...formData };
      if (updateData.recipients) {
        updateData.recipients = updateData.recipients.filter(
          (r) => r.trim() !== "",
        );
      }

      await updateNotificationRule(ruleId, updateData);
      router.push("/notification-rules");
    } catch (err) {
      setError(err instanceof Error ? err.message : "更新通知規則失敗");
    } finally {
      setSaving(false);
    }
  };

  // 格式化通知類型
  const formatNotificationType = (type: string): string => {
    const types: Record<string, string> = {
      Critical: "嚴重威脅通知",
      HighRiskDaily: "高風險每日摘要",
      Weekly: "週報通知",
    };
    return types[type] || type;
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600">載入中...</p>
        </div>
      </div>
    );
  }

  if (error && !formData.recipients) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="rounded-lg bg-red-50 p-4 text-red-800">{error}</div>
        <div className="mt-4">
          <Button onClick={() => router.push("/notification-rules")}>
            返回通知規則清單
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">編輯通知規則</h1>
        <p className="mt-2 text-gray-600">
          通知類型：{formatNotificationType(notificationType)}
        </p>
      </div>

      <div className="mx-auto max-w-2xl rounded-lg bg-white p-6 shadow">
        <form onSubmit={handleSubmit}>
          {/* 收件人（AC-021-2） */}
          <div className="mb-4">
            <label className="mb-2 block text-sm font-medium text-gray-700">
              收件人 <span className="text-red-500">*</span>
            </label>
            {formData.recipients?.map((recipient, index) => (
              <div key={index} className="mb-2 flex gap-2">
                <Input
                  type="email"
                  value={recipient}
                  onChange={(e) => handleRecipientsChange(index, e.target.value)}
                  placeholder="email@example.com"
                  className="flex-1"
                />
                {formData.recipients && formData.recipients.length > 1 && (
                  <Button
                    type="button"
                    onClick={() => handleRemoveRecipient(index)}
                    className="bg-red-600 text-white hover:bg-red-700"
                  >
                    移除
                  </Button>
                )}
              </div>
            ))}
            <Button
              type="button"
              onClick={handleAddRecipient}
              className="mt-2 bg-gray-600 text-white hover:bg-gray-700"
            >
              新增收件人
            </Button>
            {errors.recipients && (
              <p className="mt-1 text-sm text-red-600">{errors.recipients}</p>
            )}
          </div>

          {/* 風險分數閾值（僅適用於嚴重威脅通知和高風險每日摘要） */}
          {(notificationType === "Critical" ||
            notificationType === "HighRiskDaily") && (
            <div className="mb-4">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                風險分數閾值
              </label>
              <Input
                type="number"
                step="0.1"
                min="0"
                max="10"
                value={formData.risk_score_threshold || ""}
                onChange={(e) =>
                  handleChange(
                    "risk_score_threshold",
                    e.target.value ? parseFloat(e.target.value) : undefined,
                  )
                }
                placeholder="8.0"
              />
              {errors.risk_score_threshold && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.risk_score_threshold}
                </p>
              )}
            </div>
          )}

          {/* 發送時間（適用於高風險每日摘要和週報通知） */}
          {(notificationType === "HighRiskDaily" ||
            notificationType === "Weekly") && (
            <div className="mb-4">
              <label className="mb-2 block text-sm font-medium text-gray-700">
                發送時間
              </label>
              <Input
                type="time"
                value={formData.send_time || ""}
                onChange={(e) => handleChange("send_time", e.target.value || undefined)}
              />
              {errors.send_time && (
                <p className="mt-1 text-sm text-red-600">{errors.send_time}</p>
              )}
            </div>
          )}

          {/* 啟用狀態（AC-021-3） */}
          <div className="mb-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_enabled ?? false}
                onChange={(e) => handleChange("is_enabled", e.target.checked)}
                className="mr-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">啟用此通知規則</span>
            </label>
          </div>

          {/* 錯誤訊息 */}
          {error && (
            <div className="mb-4 rounded-lg bg-red-50 p-4 text-red-800">
              {error}
            </div>
          )}

          {/* 按鈕 */}
          <div className="flex gap-2">
            <Button
              type="submit"
              disabled={saving}
              className="bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? "儲存中..." : "儲存變更"}
            </Button>
            <Button
              type="button"
              onClick={() => router.push("/notification-rules")}
              className="bg-gray-600 text-white hover:bg-gray-700"
            >
              取消
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

