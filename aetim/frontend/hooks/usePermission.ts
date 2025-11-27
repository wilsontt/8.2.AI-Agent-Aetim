/**
 * 權限檢查 Hook
 * 
 * 提供權限檢查功能。
 * 符合 AC-023-3：在 UI 中隱藏使用者無權存取的功能
 */

import { useState, useEffect } from "react";
import { getUserInfo, getToken } from "@/lib/auth/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

/**
 * 使用者角色
 */
export type UserRole = "CISO" | "IT_Admin" | "Analyst" | "Viewer";

/**
 * 權限名稱
 */
export type PermissionName =
  | "asset:view"
  | "asset:create"
  | "asset:update"
  | "asset:delete"
  | "asset:import"
  | "pir:view"
  | "pir:create"
  | "pir:update"
  | "pir:delete"
  | "pir:toggle"
  | "threat_feed:view"
  | "threat_feed:create"
  | "threat_feed:update"
  | "threat_feed:delete"
  | "threat_feed:toggle"
  | "threat:view"
  | "association:view"
  | "risk_assessment:view"
  | "report:view"
  | "report:create"
  | "report:download"
  | "ticket:view"
  | "ticket:export"
  | "ticket:update_status"
  | "notification_rule:view"
  | "notification_rule:create"
  | "notification_rule:update"
  | "notification_rule:delete"
  | "system_config:view"
  | "system_config:update"
  | "schedule:view"
  | "schedule:create"
  | "schedule:update"
  | "schedule:delete"
  | "schedule:trigger"
  | "audit_log:view";

/**
 * 使用者權限資訊
 */
interface UserPermissions {
  roles: UserRole[];
  permissions: PermissionName[];
}

/**
 * 權限檢查 Hook
 * 
 * @returns 權限檢查函數和使用者權限資訊
 */
export function usePermission() {
  const [permissions, setPermissions] = useState<UserPermissions | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPermissions();
  }, []);

  /**
   * 載入使用者權限
   */
  const loadPermissions = async () => {
    try {
      const token = getToken();
      if (!token) {
        setPermissions(null);
        setLoading(false);
        return;
      }

      // 從後端取得使用者權限
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/permissions`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data: UserPermissions = await response.json();
        setPermissions(data);
      } else {
        setPermissions(null);
      }
    } catch (error) {
      console.error("載入權限失敗:", error);
      setPermissions(null);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 檢查是否有特定角色
   * 
   * @param role 角色名稱
   * @returns 是否有該角色
   */
  const hasRole = (role: UserRole): boolean => {
    if (!permissions) {
      return false;
    }
    return permissions.roles.includes(role);
  };

  /**
   * 檢查是否有特定權限
   * 
   * @param permission 權限名稱
   * @returns 是否有該權限
   */
  const hasPermission = (permission: PermissionName): boolean => {
    if (!permissions) {
      return false;
    }
    return permissions.permissions.includes(permission);
  };

  /**
   * 檢查是否有任一角色
   * 
   * @param roles 角色名稱清單
   * @returns 是否有任一角色
   */
  const hasAnyRole = (roles: UserRole[]): boolean => {
    return roles.some((role) => hasRole(role));
  };

  /**
   * 檢查是否有任一權限
   * 
   * @param permissions 權限名稱清單
   * @returns 是否有任一權限
   */
  const hasAnyPermission = (permissions: PermissionName[]): boolean => {
    return permissions.some((permission) => hasPermission(permission));
  };

  return {
    permissions,
    loading,
    hasRole,
    hasPermission,
    hasAnyRole,
    hasAnyPermission,
    refresh: loadPermissions,
  };
}

