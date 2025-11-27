/**
 * 保護路由元件
 * 
 * 用於保護需要特定角色或權限才能存取的頁面。
 * 符合 AC-023-3：在 UI 中隱藏使用者無權存取的功能
 */

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { usePermission, UserRole, PermissionName } from "@/hooks/usePermission";
import { isAuthenticated } from "@/lib/auth/auth";

interface ProtectedRouteProps {
  children: React.ReactNode;
  roles?: UserRole[];
  permissions?: PermissionName[];
  redirectTo?: string;
}

/**
 * 保護路由元件
 * 
 * @param props 元件屬性
 * @returns 保護的路由內容或重定向
 */
export function ProtectedRoute({
  children,
  roles,
  permissions,
  redirectTo = "/login",
}: ProtectedRouteProps) {
  const router = useRouter();
  const { permissions: userPermissions, loading, hasAnyRole, hasAnyPermission } = usePermission();

  useEffect(() => {
    // 檢查是否已登入
    if (!isAuthenticated()) {
      router.push(redirectTo);
      return;
    }

    // 如果還在載入權限，等待
    if (loading) {
      return;
    }

    // 檢查角色
    if (roles && roles.length > 0) {
      if (!hasAnyRole(roles)) {
        router.push("/unauthorized");
        return;
      }
    }

    // 檢查權限
    if (permissions && permissions.length > 0) {
      if (!hasAnyPermission(permissions)) {
        router.push("/unauthorized");
        return;
      }
    }
  }, [loading, userPermissions, roles, permissions, router, redirectTo, hasAnyRole, hasAnyPermission]);

  // 如果還在載入，顯示載入中
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600">載入中...</p>
        </div>
      </div>
    );
  }

  // 如果未登入，不顯示內容（會重定向）
  if (!isAuthenticated()) {
    return null;
  }

  // 檢查角色
  if (roles && roles.length > 0) {
    if (!hasAnyRole(roles)) {
      return null; // 會重定向到未授權頁面
    }
  }

  // 檢查權限
  if (permissions && permissions.length > 0) {
    if (!hasAnyPermission(permissions)) {
      return null; // 會重定向到未授權頁面
    }
  }

  return <>{children}</>;
}

