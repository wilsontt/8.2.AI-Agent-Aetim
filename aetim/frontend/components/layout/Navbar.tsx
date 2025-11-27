/**
 * 導航列元件
 * 
 * 提供主要導航功能和登出功能。
 */

"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { signOut, getUserInfo, isAuthenticated, type UserInfo } from "@/lib/auth/auth";

/**
 * 導航列元件
 */
export function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<UserInfo | null>(null);
  const [showMenu, setShowMenu] = useState(false);

  useEffect(() => {
    // 載入使用者資訊
    if (isAuthenticated()) {
      const userInfo = getUserInfo();
      setUser(userInfo);
    }
  }, []);

  // 點擊外部關閉選單
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (showMenu && !target.closest(".relative")) {
        setShowMenu(false);
      }
    };

    if (showMenu) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showMenu]);

  /**
   * 處理登出
   */
  const handleSignOut = async () => {
    try {
      await signOut();
      router.push("/login");
    } catch (error) {
      console.error("登出失敗:", error);
    }
  };

  // 如果不在登入頁面或回調頁面，顯示導航列
  if (pathname === "/login" || pathname === "/callback") {
    return null;
  }

  return (
    <nav className="bg-white shadow-md">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo 和標題 */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">AETIM</h1>
            </Link>
          </div>

          {/* 導航連結 */}
          <div className="hidden md:flex md:items-center md:space-x-4">
            <Link
              href="/"
              className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                pathname === "/"
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-700 hover:bg-gray-100"
              }`}
            >
              首頁
            </Link>
            <Link
              href="/assets"
              className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                pathname.startsWith("/assets")
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-700 hover:bg-gray-100"
              }`}
            >
              資產管理
            </Link>
            <Link
              href="/threats"
              className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                pathname.startsWith("/threats")
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-700 hover:bg-gray-100"
              }`}
            >
              威脅管理
            </Link>
            <Link
              href="/reports"
              className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                pathname.startsWith("/reports")
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-700 hover:bg-gray-100"
              }`}
            >
              報告
            </Link>
          </div>

          {/* 使用者選單 */}
          <div className="relative">
            {user ? (
              <div className="flex items-center space-x-4">
                <div className="hidden md:block text-sm text-gray-700">
                  {user.display_name || user.email}
                </div>
                <div className="relative">
                  <button
                    onClick={() => setShowMenu(!showMenu)}
                    className="flex items-center rounded-full bg-gray-100 p-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <svg
                      className="h-5 w-5 text-gray-600"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                      />
                    </svg>
                  </button>

                  {/* 下拉選單 */}
                  {showMenu && (
                    <div className="absolute right-0 mt-2 w-48 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5">
                      <div className="py-1">
                        <div className="px-4 py-2 text-sm text-gray-700 border-b">
                          <div className="font-medium">{user.display_name}</div>
                          <div className="text-xs text-gray-500">{user.email}</div>
                        </div>
                        <button
                          onClick={handleSignOut}
                          className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
                        >
                          登出
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <Link
                href="/login"
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                登入
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

