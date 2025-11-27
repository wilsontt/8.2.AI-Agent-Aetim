/**
 * 權限閘道元件
 * 
 * 用於根據權限條件顯示或隱藏 UI 元件。
 * 符合 AC-023-3：在 UI 中隱藏使用者無權存取的功能
 */

"use client";

import { usePermission, UserRole, PermissionName } from "@/hooks/usePermission";

interface PermissionGateProps {
  children: React.ReactNode;
  roles?: UserRole[];
  permissions?: PermissionName[];
  fallback?: React.ReactNode;
}

/**
 * 權限閘道元件
 * 
 * 如果使用者有指定的角色或權限，則顯示子元件，否則顯示 fallback（如果提供）或不顯示任何內容。
 * 
 * @param props 元件屬性
 * @returns 子元件或 fallback
 */
export function PermissionGate({
  children,
  roles,
  permissions,
  fallback = null,
}: PermissionGateProps) {
  const { hasAnyRole, hasAnyPermission } = usePermission();

  // 檢查角色
  if (roles && roles.length > 0) {
    if (!hasAnyRole(roles)) {
      return <>{fallback}</>;
    }
  }

  // 檢查權限
  if (permissions && permissions.length > 0) {
    if (!hasAnyPermission(permissions)) {
      return <>{fallback}</>;
    }
  }

  return <>{children}</>;
}

