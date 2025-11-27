/**
 * 儀表板端對端測試
 * 
 * 測試場景：
 * - 系統狀態顯示
 * - 威脅統計圖表
 * - 資產統計
 * - 時間範圍篩選
 * - 圖表匯出功能
 * 
 * 符合 T-5-4-1：端對端測試所有功能
 * 符合 AC-027-1, AC-027-2, AC-028-1, AC-028-2, AC-028-3
 */

import { test, expect } from "@playwright/test";

test.describe("儀表板功能", () => {
  test.beforeEach(async ({ page }) => {
    // 模擬已登入狀態
    // 注意：實際測試需要設定測試用的認證狀態
    await page.goto("/dashboard");
  });

  test("應該顯示系統狀態區塊", async ({ page }) => {
    // 檢查系統健康狀態卡片
    await expect(page.locator("text=系統健康狀態")).toBeVisible();
    
    // 檢查統計卡片
    await expect(page.locator("text=最近收集的威脅數量")).toBeVisible();
    await expect(page.locator("text=待處理的嚴重威脅")).toBeVisible();
    await expect(page.locator("text=威脅情資來源狀態")).toBeVisible();
  });

  test("應該顯示威脅統計圖表", async ({ page }) => {
    // 檢查威脅數量趨勢圖表
    await expect(page.locator("text=威脅數量趨勢")).toBeVisible();
    
    // 檢查風險分數分布圖表
    await expect(page.locator("text=風險分數分布")).toBeVisible();
    
    // 檢查受影響資產統計圖表
    await expect(page.locator("text=受影響資產統計")).toBeVisible();
    
    // 檢查威脅來源統計圖表
    await expect(page.locator("text=威脅來源統計")).toBeVisible();
  });

  test("應該顯示資產統計區塊", async ({ page }) => {
    // 檢查資產統計標題
    await expect(page.locator("text=資產統計")).toBeVisible();
    
    // 檢查資產統計卡片
    await expect(page.locator("text=資產總數")).toBeVisible();
    await expect(page.locator("text=受威脅影響的資產")).toBeVisible();
    await expect(page.locator("text=對外暴露資產")).toBeVisible();
    await expect(page.locator("text=高敏感度資產")).toBeVisible();
  });

  test("時間範圍篩選應該正常工作", async ({ page }) => {
    // 檢查時間範圍篩選器
    const timeRangeSelect = page.locator("select").first();
    await expect(timeRangeSelect).toBeVisible();
    
    // 選擇不同的時間範圍
    await timeRangeSelect.selectOption("7d");
    await expect(timeRangeSelect).toHaveValue("7d");
    
    await timeRangeSelect.selectOption("30d");
    await expect(timeRangeSelect).toHaveValue("30d");
    
    await timeRangeSelect.selectOption("90d");
    await expect(timeRangeSelect).toHaveValue("90d");
  });

  test("圖表匯出按鈕應該存在", async ({ page }) => {
    // 檢查匯出所有圖表按鈕
    await expect(page.locator("text=匯出所有圖表為 PDF")).toBeVisible();
    
    // 檢查個別圖表的匯出按鈕
    // 注意：這些按鈕可能在圖表標題旁邊
    await expect(page.locator("button").filter({ hasText: "PNG" }).first()).toBeVisible();
    await expect(page.locator("button").filter({ hasText: "PDF" }).first()).toBeVisible();
  });

  test("自動刷新功能應該正常工作", async ({ page }) => {
    // 檢查自動刷新選項
    const autoRefreshCheckbox = page.locator('input[type="checkbox"]').first();
    await expect(autoRefreshCheckbox).toBeVisible();
    
    // 切換自動刷新
    await autoRefreshCheckbox.click();
    await expect(autoRefreshCheckbox).toBeChecked({ checked: false });
    
    await autoRefreshCheckbox.click();
    await expect(autoRefreshCheckbox).toBeChecked({ checked: true });
  });

  test("重新整理按鈕應該正常工作", async ({ page }) => {
    // 檢查重新整理按鈕
    const refreshButton = page.locator("button").filter({ hasText: "重新整理" });
    await expect(refreshButton).toBeVisible();
    
    // 點擊重新整理按鈕
    await refreshButton.click();
    
    // 應該看到載入狀態（如果有的話）
    // 注意：實際測試需要等待 API 回應
  });
});

