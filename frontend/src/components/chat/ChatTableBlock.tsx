import React from "react";

type Props = {
  rows: Record<string, unknown>[];
  columns: string[];
};

function toTitle(label: string): string {
  return label
    .replace(/_/g, " ")
    .replace(/\b\w/g, (m) => m.toUpperCase())
    .replace(/\bEur\b/g, "EUR")
    .replace(/\bAov\b/g, "AOV");
}

function isCurrencyColumn(column: string) {
  return /(revenue|sales|amount|value|price|aov|avg_order_value)/i.test(column);
}

function isPercentColumn(column: string) {
  return /(pct|percent|percentage|change|growth|yoy|mom|qoq)/i.test(column);
}

function numericValue(value: unknown): number | null {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value === "string" && value.trim() !== "" && !Number.isNaN(Number(value))) return Number(value);
  return null;
}

function formatCell(value: unknown, column: string): string {
  if (value === null || value === undefined) return "";
  const num = numericValue(value);
  if (num !== null) {
    if (isCurrencyColumn(column)) {
      return new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(num);
    }
    if (isPercentColumn(column)) {
      return `${num.toFixed(1)}%`;
    }
    return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(num);
  }
  return String(value);
}

function isNumericColumn(rows: Record<string, unknown>[], column: string) {
  return rows.every((row) => row[column] === null || row[column] === undefined || row[column] === "" || numericValue(row[column]) !== null);
}

export function ChatTableBlock({ rows, columns }: Props) {
  const limitedRows = rows.slice(0, 50);
  const numericColumns = new Set(columns.filter((col) => isNumericColumn(rows, col)));

  return (
    <div className="table-panel refined-table-panel">
      <div className="table-meta">Showing {limitedRows.length} of {rows.length} rows</div>
      <div className="table-wrapper">
        <table className="result-table refined-result-table">
          <colgroup>
            {columns.map((col) => (
              <col key={col} style={{ width: numericColumns.has(col) ? '14%' : 'auto' }} />
            ))}
          </colgroup>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col} className={numericColumns.has(col) ? 'numeric-cell' : undefined}>{toTitle(col)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {limitedRows.map((row, idx) => (
              <tr key={idx}>
                {columns.map((col) => (
                  <td key={col} className={numericColumns.has(col) ? "numeric-cell" : undefined} title={formatCell(row[col], col)}>
                    {formatCell(row[col], col)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
