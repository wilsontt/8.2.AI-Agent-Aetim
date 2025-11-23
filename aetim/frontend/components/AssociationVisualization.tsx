/**
 * 關聯分析視覺化組件
 * 
 * 使用簡單的 SVG 和 Canvas 實作威脅-資產關係圖（AC-011-4）
 */

"use client";

import React, { useEffect, useRef, useState } from "react";
import type { ThreatAssetAssociation } from "@/types/association";

interface AssociationVisualizationProps {
  associations: ThreatAssetAssociation[];
  threatId: string;
  threatTitle?: string;
}

interface Node {
  id: string;
  type: "threat" | "asset";
  label: string;
  x: number;
  y: number;
  size: number;
  color: string;
}

interface Edge {
  from: string;
  to: string;
  confidence: number;
  matchType: string;
}

export const AssociationVisualization: React.FC<AssociationVisualizationProps> = ({
  associations,
  threatId,
  threatTitle,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // 建立節點和邊
  const nodes: Node[] = [
    {
      id: threatId,
      type: "threat",
      label: threatTitle || threatId,
      x: 400,
      y: 300,
      size: 60,
      color: "#ef4444", // red-500
    },
    ...associations.map((assoc, index) => {
      const angle = (index / associations.length) * 2 * Math.PI;
      const radius = 200;
      return {
        id: assoc.asset_id,
        type: "asset" as const,
        label: assoc.asset_id.substring(0, 8) + "...",
        x: 400 + radius * Math.cos(angle),
        y: 300 + radius * Math.sin(angle),
        size: 40 + assoc.match_confidence * 20,
        color:
          assoc.match_confidence >= 0.9
            ? "#22c55e" // green-500
            : assoc.match_confidence >= 0.7
              ? "#eab308" // yellow-500
              : "#f97316", // orange-500
      };
    }),
  ];

  const edges: Edge[] = associations.map((assoc) => ({
    from: threatId,
    to: assoc.asset_id,
    confidence: assoc.match_confidence,
    matchType: assoc.match_type,
  }));

  // 繪製圖形
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // 設定畫布大小
    canvas.width = 800;
    canvas.height = 600;

    // 清除畫布
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 應用縮放和平移
    ctx.save();
    ctx.translate(pan.x, pan.y);
    ctx.scale(zoom, zoom);

    // 繪製邊
    edges.forEach((edge) => {
      const fromNode = nodes.find((n) => n.id === edge.from);
      const toNode = nodes.find((n) => n.id === edge.to);

      if (!fromNode || !toNode) return;

      // 邊的顏色根據信心分數
      const alpha = edge.confidence;
      ctx.strokeStyle = `rgba(59, 130, 246, ${alpha})`; // blue-500 with alpha
      ctx.lineWidth = 2 + edge.confidence * 3;
      ctx.beginPath();
      ctx.moveTo(fromNode.x, fromNode.y);
      ctx.lineTo(toNode.x, toNode.y);
      ctx.stroke();
    });

    // 繪製節點
    nodes.forEach((node) => {
      // 節點圓圈
      ctx.fillStyle = node.color;
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.size / 2, 0, 2 * Math.PI);
      ctx.fill();

      // 節點邊框
      ctx.strokeStyle = selectedNode?.id === node.id ? "#000" : "#fff";
      ctx.lineWidth = selectedNode?.id === node.id ? 3 : 2;
      ctx.stroke();

      // 節點標籤
      ctx.fillStyle = "#fff";
      ctx.font = "12px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(node.label, node.x, node.y);
    });

    ctx.restore();
  }, [nodes, edges, zoom, pan, selectedNode]);

  // 處理滑鼠點擊
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - pan.x) / zoom;
    const y = (e.clientY - rect.top - pan.y) / zoom;

    // 檢查是否點擊到節點
    const clickedNode = nodes.find((node) => {
      const distance = Math.sqrt(
        Math.pow(x - node.x, 2) + Math.pow(y - node.y, 2),
      );
      return distance <= node.size / 2;
    });

    setSelectedNode(clickedNode || null);
  };

  // 處理滑鼠拖曳
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // 處理縮放
  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom(Math.max(0.5, Math.min(2, zoom * delta)));
  };

  if (associations.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
        <p className="text-sm text-gray-500">目前沒有關聯的資產，無法顯示視覺化圖表</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">關聯分析視覺化</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setZoom(Math.max(0.5, zoom - 0.1))}
            className="rounded-md border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50"
          >
            縮小
          </button>
          <button
            onClick={() => setZoom(1)}
            className="rounded-md border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50"
          >
            重置
          </button>
          <button
            onClick={() => setZoom(Math.min(2, zoom + 0.1))}
            className="rounded-md border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50"
          >
            放大
          </button>
        </div>
      </div>

      <div className="relative">
        <canvas
          ref={canvasRef}
          onClick={handleCanvasClick}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
          className="cursor-move border border-gray-200 rounded-md"
          style={{ width: "100%", height: "600px" }}
        />

        {/* 圖例 */}
        <div className="mt-4 flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 rounded-full bg-red-500"></div>
            <span>威脅</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 rounded-full bg-green-500"></div>
            <span>資產（信心分數 ≥ 90%）</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 rounded-full bg-yellow-500"></div>
            <span>資產（信心分數 70-89%）</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 rounded-full bg-orange-500"></div>
            <span>資產（信心分數 &lt; 70%）</span>
          </div>
        </div>

        {/* 選中節點詳情 */}
        {selectedNode && (
          <div className="mt-4 rounded-md border border-gray-200 bg-gray-50 p-4">
            <h4 className="mb-2 font-semibold text-gray-900">節點詳情</h4>
            <dl className="space-y-1 text-sm">
              <div>
                <dt className="font-medium text-gray-700">ID：</dt>
                <dd className="text-gray-900">{selectedNode.id}</dd>
              </div>
              <div>
                <dt className="font-medium text-gray-700">類型：</dt>
                <dd className="text-gray-900">{selectedNode.type === "threat" ? "威脅" : "資產"}</dd>
              </div>
              <div>
                <dt className="font-medium text-gray-700">標籤：</dt>
                <dd className="text-gray-900">{selectedNode.label}</dd>
              </div>
              {selectedNode.type === "asset" && (
                <div>
                  <dt className="font-medium text-gray-700">關聯資訊：</dt>
                  <dd className="text-gray-900">
                    {associations
                      .find((a) => a.asset_id === selectedNode.id)
                      ?.match_confidence.toFixed(2)}
                    % 信心分數
                  </dd>
                </div>
              )}
            </dl>
          </div>
        )}
      </div>
    </div>
  );
};

