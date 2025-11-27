import type { Metadata } from 'next'
import './globals.css'
import { Navbar } from '@/components/layout/Navbar'

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
      <body>
        <Navbar />
        {children}
      </body>
    </html>
  )
}

