/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  },
  // 效能優化設定
  // 符合 T-5-4-2：效能優化
  // 符合 NFR-001：Web 界面頁面載入時間 ≤ 2 秒
  experimental: {
    optimizeCss: true,
  },
  // 圖片優化
  images: {
    formats: ['image/avif', 'image/webp'],
  },
  // 壓縮設定
  compress: true,
  // 生產環境優化
  swcMinify: true,
}

module.exports = nextConfig

