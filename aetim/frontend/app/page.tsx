import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold">AETIM</h1>
      <p className="mt-4 text-lg">AI 驅動之自動化威脅情資管理系統</p>
      <div className="mt-8 flex space-x-4">
        <Link
          href="/assets"
          className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          資產管理
        </Link>
      </div>
    </main>
  );
}

