import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AETIM - AI 驅動之自動化威脅情資管理系統',
  description: 'AI 驅動之自動化威脅情資管理系統',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-TW">
      <body>{children}</body>
    </html>
  )
}

