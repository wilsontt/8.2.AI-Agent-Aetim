/**
 * 登入頁面
 * 
 * 提供 OIDC/OAuth 2.0 登入功能。
 * 符合 AC-022-1, AC-022-2, AC-022-3。
 */

"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { signIn, isAuthenticated } from "@/lib/auth/auth";

/**
 * 登入頁面元件
 */
export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 檢查是否已登入
  useEffect(() => {
    if (isAuthenticated()) {
      // 如果已登入，重定向至首頁或指定的重定向 URL
      const redirectTo = searchParams.get("redirect") || "/";
      router.push(redirectTo);
    }
  }, [router, searchParams]);

  // 處理登入錯誤（從 URL 參數取得）
  useEffect(() => {
    const errorParam = searchParams.get("error");
    if (errorParam) {
      setError(decodeURIComponent(errorParam));
    }
  }, [searchParams]);

  /**
   * 處理登入按鈕點擊
   */
  const handleLogin = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // 觸發 OIDC/OAuth 2.0 登入流程
      // 符合 AC-022-1：整合 OIDC/OAuth 2.0 身份驗證提供者 (IdP)
      // 符合 AC-022-2：支援單一登入 (SSO) 功能
      await signIn();
    } catch (err) {
      // 符合 AC-022-3：登入失敗時顯示明確的錯誤訊息
      const errorMessage = err instanceof Error ? err.message : "登入失敗，請稍後再試";
      setError(errorMessage);
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        {/* 標題區域 */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900">AETIM</h1>
          <p className="mt-2 text-lg text-gray-600">
            AI 驅動之自動化威脅情資管理系統
          </p>
          <p className="mt-4 text-sm text-gray-500">
            請使用您的企業帳號登入
          </p>
        </div>

        {/* 登入表單 */}
        <div className="rounded-lg bg-white px-6 py-8 shadow-md">
          {/* 錯誤訊息 */}
          {error && (
            <div
              className="mb-4 rounded-md bg-red-50 p-4"
              role="alert"
            >
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-red-400"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    登入失敗
                  </h3>
                  <div className="mt-2 text-sm text-red-700">
                    <p>{error}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 登入按鈕 */}
          <button
            type="button"
            onClick={handleLogin}
            disabled={loading}
            className="w-full rounded-md bg-blue-600 px-4 py-3 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-colors duration-200"
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg
                  className="mr-2 h-5 w-5 animate-spin text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                登入中...
              </span>
            ) : (
              "登入"
            )}
          </button>

          {/* 說明文字 */}
          <p className="mt-4 text-center text-xs text-gray-500">
            點擊登入按鈕後，您將被重定向至企業身份驗證系統
          </p>
        </div>

        {/* 頁尾 */}
        <div className="text-center text-xs text-gray-500">
          <p>© 2025 AETIM. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}

