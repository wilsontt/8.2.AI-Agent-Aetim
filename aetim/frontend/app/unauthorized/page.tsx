/**
 * 未授權頁面
 * 
 * 當使用者沒有權限存取特定資源時顯示。
 */

"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { signOut } from "@/lib/auth/auth";

/**
 * 未授權頁面元件
 */
export default function UnauthorizedPage() {
  const router = useRouter();

  /**
   * 處理登出
   */
  const handleSignOut = async () => {
    await signOut();
    router.push("/login");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 text-center">
        <div className="rounded-lg bg-white px-6 py-8 shadow-md">
          {/* 圖示 */}
          <div className="mb-4 flex justify-center">
            <svg
              className="h-16 w-16 text-yellow-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>

          {/* 標題 */}
          <h1 className="text-2xl font-bold text-gray-900">
            存取被拒絕
          </h1>

          {/* 說明文字 */}
          <p className="mt-4 text-gray-600">
            您沒有權限存取此資源。
          </p>
          <p className="mt-2 text-sm text-gray-500">
            如果您認為這是錯誤，請聯絡系統管理員。
          </p>

          {/* 操作按鈕 */}
          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <Link
              href="/"
              className="inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors duration-200"
            >
              返回首頁
            </Link>
            <button
              onClick={handleSignOut}
              className="inline-block rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors duration-200"
            >
              登出
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

