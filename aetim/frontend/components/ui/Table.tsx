/**
 * 表格組件
 */

import React from "react";

interface TableProps {
  headers: Array<{ key: string; label: string; sortable?: boolean }>;
  data: Array<Record<string, any>>;
  onSort?: (key: string, order: "asc" | "desc") => void;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
  onRowClick?: (row: Record<string, any>) => void;
  selectedRows?: Set<string>;
  onRowSelect?: (id: string, selected: boolean) => void;
  selectable?: boolean;
}

export const Table: React.FC<TableProps> = ({
  headers,
  data,
  onSort,
  sortBy,
  sortOrder,
  onRowClick,
  selectedRows,
  onRowSelect,
  selectable = false,
}) => {
  const handleSort = (key: string) => {
    if (!onSort) return;
    const newOrder = sortBy === key && sortOrder === "asc" ? "desc" : "asc";
    onSort(key, newOrder);
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {selectable && (
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  checked={selectedRows?.size === data.length && data.length > 0}
                  onChange={(e) => {
                    if (onRowSelect) {
                      data.forEach((row) => {
                        onRowSelect(row.id, e.target.checked);
                      });
                    }
                  }}
                />
              </th>
            )}
            {headers.map((header) => (
              <th
                key={header.key}
                className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                  header.sortable ? "cursor-pointer hover:bg-gray-100" : ""
                }`}
                onClick={() => header.sortable && handleSort(header.key)}
              >
                <div className="flex items-center space-x-1">
                  <span>{header.label}</span>
                  {header.sortable && sortBy === header.key && (
                    <span className="text-blue-600">
                      {sortOrder === "asc" ? "↑" : "↓"}
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={headers.length + (selectable ? 1 : 0)}
                className="px-6 py-4 text-center text-gray-500"
              >
                沒有資料
              </td>
            </tr>
          ) : (
            data.map((row, index) => (
              <tr
                key={row.id || index}
                className={`hover:bg-gray-50 ${onRowClick ? "cursor-pointer" : ""}`}
                onClick={() => onRowClick && onRowClick(row)}
              >
                {selectable && (
                  <td className="px-6 py-4 whitespace-nowrap">
                    <input
                      type="checkbox"
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      checked={selectedRows?.has(row.id) || false}
                      onChange={(e) => {
                        e.stopPropagation();
                        if (onRowSelect) {
                          onRowSelect(row.id, e.target.checked);
                        }
                      }}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </td>
                )}
                {headers.map((header) => (
                  <td key={header.key} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {typeof row[header.key] === "object" && React.isValidElement(row[header.key])
                      ? row[header.key]
                      : String(row[header.key] ?? "")}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

