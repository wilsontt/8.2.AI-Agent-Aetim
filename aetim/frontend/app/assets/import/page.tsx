/**
 * 資產匯入頁面
 */

"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { previewImport, importAssets, type ImportPreviewResponse, type ImportResultResponse } from "@/lib/api/asset";

export default function AssetImportPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [result, setResult] = useState<ImportResultResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<"upload" | "preview" | "result">("upload");

  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // 檢查檔案大小
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError(`檔案大小超過限制（最大 ${MAX_FILE_SIZE / 1024 / 1024}MB）`);
      return;
    }

    // 檢查檔案類型
    if (!selectedFile.name.endsWith(".csv")) {
      setError("檔案必須為 CSV 格式");
      return;
    }

    setFile(selectedFile);
    setError(null);
    setPreview(null);
    setResult(null);
  };

  const handlePreview = async () => {
    if (!file) return;

    try {
      setLoading(true);
      setError(null);
      const previewData = await previewImport(file, 10);
      setPreview(previewData);
      setStep("preview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "預覽失敗");
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    if (!file) return;

    try {
      setLoading(true);
      setError(null);
      const importResult = await importAssets(file);
      setResult(importResult);
      setStep("result");
    } catch (err) {
      setError(err instanceof Error ? err.message : "匯入失敗");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    setStep("upload");
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">匯入資產</h1>
        <Button variant="outline" onClick={() => router.push("/assets")}>
          返回清單
        </Button>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* 步驟 1: 上傳檔案 */}
      {step === "upload" && (
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">步驟 1: 選擇 CSV 檔案</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                CSV 檔案（≤ 10MB）
              </label>
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
              <p className="mt-2 text-sm text-gray-500">
                檔案必須包含以下欄位：主機名稱、作業系統(含版本)、運行的應用程式(含版本)、負責人、資料敏感度、是否對外(Public-facing)、業務關鍵性
              </p>
            </div>
            {file && (
              <div className="rounded-md bg-gray-50 p-4">
                <p className="text-sm text-gray-700">
                  <strong>檔案名稱：</strong> {file.name}
                </p>
                <p className="text-sm text-gray-700">
                  <strong>檔案大小：</strong> {(file.size / 1024).toFixed(2)} KB
                </p>
              </div>
            )}
            <div className="flex justify-end">
              <Button onClick={handlePreview} disabled={!file || loading} isLoading={loading}>
                預覽
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* 步驟 2: 預覽 */}
      {step === "preview" && preview && (
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">步驟 2: 預覽匯入資料</h2>
          <div className="mb-4 space-y-2">
            <p className="text-sm text-gray-700">
              <strong>總筆數：</strong> {preview.total_count}
            </p>
            <p className="text-sm text-gray-700">
              <strong>有效筆數：</strong> {preview.valid_count}
            </p>
            <p className="text-sm text-gray-700">
              <strong>無效筆數：</strong> {preview.invalid_count}
            </p>
          </div>

          {preview.errors.length > 0 && (
            <div className="mb-4 rounded-md bg-red-50 p-4">
              <h3 className="mb-2 text-sm font-medium text-red-800">錯誤清單：</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-red-700">
                {preview.errors.map((error, index) => (
                  <li key={index}>
                    第 {error.row} 行，欄位「{error.field}」：{error.error}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {preview.preview_data.length > 0 && (
            <div className="mb-4 overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      行號
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      主機名稱
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      作業系統
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      負責人
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {preview.preview_data.map((item) => (
                    <tr key={item.row}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.row}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.data["主機名稱"]}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.data["作業系統(含版本)"]}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {item.data["負責人"]}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={handleReset}>
              重新選擇
            </Button>
            <Button onClick={handleImport} disabled={preview.invalid_count > 0} isLoading={loading}>
              確認匯入
            </Button>
          </div>
        </div>
      )}

      {/* 步驟 3: 匯入結果 */}
      {step === "result" && result && (
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">步驟 3: 匯入結果</h2>
          <div className="mb-4 space-y-2">
            <p className="text-sm text-gray-700">
              <strong>總筆數：</strong> {result.total_count}
            </p>
            <p className="text-sm text-green-700">
              <strong>成功筆數：</strong> {result.success_count}
            </p>
            <p className="text-sm text-red-700">
              <strong>失敗筆數：</strong> {result.failure_count}
            </p>
            <p className="text-sm text-gray-700">
              <strong>成功率：</strong>{" "}
              {result.total_count > 0
                ? ((result.success_count / result.total_count) * 100).toFixed(2)
                : 0}
              %
            </p>
          </div>

          {result.results.filter((r) => !r.success).length > 0 && (
            <div className="mb-4 rounded-md bg-red-50 p-4">
              <h3 className="mb-2 text-sm font-medium text-red-800">失敗記錄：</h3>
              <ul className="list-disc list-inside space-y-1 text-sm text-red-700">
                {result.results
                  .filter((r) => !r.success)
                  .map((r, index) => (
                    <li key={index}>
                      第 {r.row} 行：{r.error}
                    </li>
                  ))}
              </ul>
            </div>
          )}

          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={handleReset}>
              繼續匯入
            </Button>
            <Button onClick={() => router.push("/assets")}>返回清單</Button>
          </div>
        </div>
      )}
    </div>
  );
}

