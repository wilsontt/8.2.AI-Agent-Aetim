#!/bin/bash

# 健康檢查測試腳本

set -e

echo "🏥 開始測試服務健康狀態..."

# 測試後端健康檢查
echo "📡 測試後端 API..."
BACKEND_HEALTH=$(curl -s http://localhost:8000/api/v1/health || echo "failed")
if echo "$BACKEND_HEALTH" | grep -q "healthy"; then
    echo "✅ 後端服務正常"
    echo "$BACKEND_HEALTH" | jq '.' 2>/dev/null || echo "$BACKEND_HEALTH"
else
    echo "❌ 後端服務異常"
    echo "$BACKEND_HEALTH"
    exit 1
fi

# 測試 AI 服務健康檢查
echo ""
echo "🤖 測試 AI 服務..."
AI_HEALTH=$(curl -s http://localhost:8001/health || echo "failed")
if echo "$AI_HEALTH" | grep -q "healthy"; then
    echo "✅ AI 服務正常"
    echo "$AI_HEALTH" | jq '.' 2>/dev/null || echo "$AI_HEALTH"
else
    echo "❌ AI 服務異常"
    echo "$AI_HEALTH"
    exit 1
fi

# 測試 Redis 連線
echo ""
echo "💾 測試 Redis 連線..."
REDIS_TEST=$(docker exec aetim-redis redis-cli ping 2>/dev/null || echo "failed")
if [ "$REDIS_TEST" = "PONG" ]; then
    echo "✅ Redis 連線正常"
else
    echo "❌ Redis 連線異常"
    exit 1
fi

# 測試資料庫連線（透過後端 API）
echo ""
echo "🗄️  測試資料庫連線（透過後端健康檢查）..."
DB_STATUS=$(echo "$BACKEND_HEALTH" | jq -r '.checks.database' 2>/dev/null || echo "unknown")
if [ "$DB_STATUS" = "healthy" ]; then
    echo "✅ 資料庫連線正常"
else
    echo "❌ 資料庫連線異常"
    exit 1
fi

echo ""
echo "✅ 所有服務健康檢查通過！"

