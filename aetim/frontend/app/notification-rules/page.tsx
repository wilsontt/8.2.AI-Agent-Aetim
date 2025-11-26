/**
 * 通知規則清單頁面
 */

"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Table } from "@/components/ui/Table";
import {
  getNotificationRules,
  updateNotificationRule,
  deleteNotificationRule,
  type NotificationRule,
} from "@/lib/api/notification_rule";

export default function NotificationRulesPage() {
  const router = useRouter();
  const [rules, setRules] = useState<NotificationRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 載入通知規則清單
  const loadRules = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await getNotificationRules();
      setRules(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "載入通知規則失敗");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRules();
  }, []);

  // 處理啟用/停用切換（AC-021-3）
  const handleToggleEnabled = async (rule: NotificationRule) => {
    try {
      await updateNotificationRule(rule.id, {
        is_enabled: !rule.is_enabled,
      });
      await loadRules();
    } catch (err) {
      alert(err instanceof Error ? err.message : "更新通知規則失敗");
    }
  };

  // 處理刪除
  const handleDelete = async (ruleId: string) => {
    if (!confirm("確定要刪除此通知規則嗎？")) {
      return;
    }

    try {
      await deleteNotificationRule(ruleId);
      await loadRules();
    } catch (err) {
      alert(err instanceof Error ? err.message : "刪除通知規則失敗");
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

  // 格式化日期
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleString("zh-TW", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // 表格標題
  const tableHeaders = [
    { key: "notification_type", label: "通知類型", sortable: true },
    { key: "is_enabled", label: "啟用狀態", sortable: true },
    { key: "recipients", label: "收件人", sortable: false },
    { key: "risk_score_threshold", label: "風險分數閾值", sortable: true },
    { key: "send_time", label: "發送時間", sortable: true },
    { key: "actions", label: "操作", sortable: false },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">通知規則管理</h1>
        <Button
          onClick={() => router.push("/notification-rules/create")}
          className="bg-blue-600 text-white hover:bg-blue-700"
        >
          建立通知規則
        </Button>
      </div>

      {/* 錯誤訊息 */}
      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-4 text-red-800">{error}</div>
      )}

      {/* 通知規則表格 */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600">載入中...</p>
        </div>
      ) : (
        <div className="rounded-lg bg-white shadow">
          <Table
            headers={tableHeaders}
            data={rules.map((rule) => ({
              id: rule.id,
              notification_type: formatNotificationType(rule.notification_type),
              is_enabled: (
                <span
                  className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                    rule.is_enabled
                      ? "bg-green-100 text-green-800"
                      : "bg-gray-100 text-gray-800"
                  }`}
                >
                  {rule.is_enabled ? "啟用" : "停用"}
                </span>
              ),
              recipients: rule.recipients.join(", "),
              risk_score_threshold: rule.risk_score_threshold
                ? rule.risk_score_threshold.toFixed(1)
                : "-",
              send_time: rule.send_time || "-",
              actions: (
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleToggleEnabled(rule)}
                    className={`text-sm px-3 py-1 ${
                      rule.is_enabled
                        ? "bg-yellow-600 text-white hover:bg-yellow-700"
                        : "bg-green-600 text-white hover:bg-green-700"
                    }`}
                  >
                    {rule.is_enabled ? "停用" : "啟用"}
                  </Button>
                  <Button
                    onClick={() => router.push(`/notification-rules/${rule.id}/edit`)}
                    className="bg-blue-600 text-white hover:bg-blue-700 text-sm px-3 py-1"
                  >
                    編輯
                  </Button>
                  <Button
                    onClick={() => handleDelete(rule.id)}
                    className="bg-red-600 text-white hover:bg-red-700 text-sm px-3 py-1"
                  >
                    刪除
                  </Button>
                </div>
              ),
            }))}
          />
        </div>
      )}
    </div>
  );
}

