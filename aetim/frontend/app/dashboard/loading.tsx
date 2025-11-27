/**
 * 儀表板載入中元件
 * 
 * 符合 T-5-4-2：效能優化（前端載入狀態）
 */

export default function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
        <p className="text-gray-600">載入中...</p>
      </div>
    </div>
  );
}

