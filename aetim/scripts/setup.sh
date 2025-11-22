#!/bin/bash

# AETIM 開發環境設定腳本

set -e

echo "🚀 開始設定 AETIM 開發環境..."

# 檢查必要工具
echo "📋 檢查必要工具..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker 未安裝，請先安裝 Docker"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose 未安裝，請先安裝 Docker Compose"; exit 1; }

# 建立必要的目錄
echo "📁 建立必要的目錄..."
mkdir -p data
mkdir -p reports
mkdir -p backend/.venv 2>/dev/null || true

# 複製環境變數檔案
if [ ! -f .env ]; then
    echo "📝 複製環境變數檔案..."
    cp .env.example .env
    echo "✅ 已建立 .env 檔案，請根據需要修改"
else
    echo "ℹ️  .env 檔案已存在，跳過複製"
fi

# 建立 Python 虛擬環境（可選）
if [ ! -d "backend/.venv" ]; then
    echo "🐍 建立 Python 虛擬環境..."
    cd backend
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    cd ..
    echo "✅ Python 虛擬環境已建立"
else
    echo "ℹ️  Python 虛擬環境已存在，跳過建立"
fi

# 檢查 Node.js 版本（如果使用 nvm）
if command -v nvm >/dev/null 2>&1; then
    echo "📦 設定 Node.js 版本..."
    nvm use
fi

echo "✅ 開發環境設定完成！"
echo ""
echo "📖 下一步："
echo "  1. 檢查並修改 .env 檔案"
echo "  2. 執行 'docker-compose up -d' 啟動服務"
echo "  3. 執行 'docker-compose logs -f' 查看日誌"

