/**
 * 通知規則類型定義
 */

export type NotificationType = "Critical" | "HighRiskDaily" | "Weekly";

export interface NotificationRule {
  id: string;
  notification_type: NotificationType;
  is_enabled: boolean;
  recipients: string[];
  risk_score_threshold?: number;
  send_time?: string; // HH:MM 格式
  created_at: string;
  updated_at: string;
  created_by: string;
  updated_by: string;
}

export interface CreateNotificationRuleRequest {
  notification_type: NotificationType;
  recipients: string[];
  risk_score_threshold?: number;
  send_time?: string;
  is_enabled?: boolean;
}

export interface UpdateNotificationRuleRequest {
  recipients?: string[];
  risk_score_threshold?: number;
  send_time?: string;
  is_enabled?: boolean;
}

export interface NotificationRuleListResponse {
  items: NotificationRule[];
  total: number;
}

