/**
 * 登入回調頁面
 * 
 * 處理 OIDC/OAuth 2.0 授權回調。
 * 符合 AC-022-1, AC-022-3。
 */

"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { handleCallback } from "@/lib/auth/auth";

/**
 * 登入回調頁面元件
 */
export default function CallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    /**
     * 處理授權回調
     */
    const processCallback = async () => {
      try {
        // 從 URL 參數取得授權碼和狀態
        const code = searchParams.get("code");
        const state = searchParams.get("state");
        const errorParam = searchParams.get("error");
        const errorDescription = searchParams.get("error_description");

        // 檢查是否有錯誤
        if (errorParam) {
          // 符合 AC-022-3：登入失敗時顯示明確的錯誤訊息
          const errorMessage = errorDescription
            ? decodeURIComponent(errorDescription)
            : errorParam === "access_denied"
            ? "使用者拒絕授權"
            : "登入失敗";
          setError(errorMessage);
          setStatus("error");
          return;
        }

        // 檢查是否有授權碼
        if (!code) {
          setError("未收到授權碼");
          setStatus("error");
          return;
        }

        // 處理授權回調
        // 符合 AC-022-1：整合 OIDC/OAuth 2.0 身份驗證提供者 (IdP)
        await handleCallback(code, state || undefined);

        // 登入成功，重定向至首頁或指定的重定向 URL
        setStatus("success");
        const redirectTo = searchParams.get("redirect") || "/";
        
        // 延遲一下再重定向，讓使用者看到成功訊息
        setTimeout(() => {
          router.push(redirectTo);
        }, 1000);
      } catch (err) {
        // 符合 AC-022-3：登入失敗時顯示明確的錯誤訊息
        const errorMessage = err instanceof Error ? err.message : "處理授權回調失敗";
        setError(errorMessage);
        setStatus("error");
      }
    };

    processCallback();
  }, [router, searchParams]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <div className="rounded-lg bg-white px-6 py-8 shadow-md text-center">
          {status === "loading" && (
            <div>
              <div className="mb-4 flex justify-center">
                <svg
                  className="h-12 w-12 animate-spin text-blue-600"
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
              </div>
              <h2 className="text-xl font-semibold text-gray-900">
                正在處理登入...
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                請稍候，我們正在驗證您的身份
              </p>
            </div>
          )}

          {status === "success" && (
            <div>
              <div className="mb-4 flex justify-center">
                <svg
                  className="h-12 w-12 text-green-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900">
                登入成功！
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                正在為您重定向...
              </p>
            </div>
          )}

          {status === "error" && (
            <div>
              <div className="mb-4 flex justify-center">
                <svg
                  className="h-12 w-12 text-red-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900">
                登入失敗
              </h2>
              <p className="mt-2 text-sm text-red-600">{error}</p>
              <div className="mt-6">
                <a
                  href="/login"
                  className="inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  返回登入頁面
                </a>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

