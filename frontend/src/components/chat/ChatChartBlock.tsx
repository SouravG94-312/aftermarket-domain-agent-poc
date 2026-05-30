import React from "react";
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from "recharts";

type Props = {
  chartType: string;
  title?: string | null;
  x?: string | null;
  y?: string[] | null;
  series?: string | null;
  data: Record<string, unknown>[];
  notes?: string | null;
};

const PALETTE = ["#0F4C5C", "#2C7DA0", "#3A86FF", "#5B8E7D", "#8A5CF6", "#F59E0B"];
const GRID = "#E5E7EB";
const AXIS = "#6B7280";
const CARD = "#FFFFFF";

function toNumber(value: unknown): number | null {
  if (typeof value === "number") return Number.isFinite(value) ? value : null;
  if (typeof value === "string") {
    const cleaned = value.trim().replace(/,/g, "").replace(/%$/, "");
    const num = Number(cleaned);
    return Number.isFinite(num) ? num : null;
  }
  return null;
}

function inferXKey(data: Record<string, unknown>[], requested?: string | null) {
  if (!data.length) return requested ?? undefined;
  const keys = Object.keys(data[0]);
  if (requested && keys.includes(requested)) return requested;
  const preferred = keys.find((k) => /(month|quarter|year|date|period)/i.test(k));
  return preferred ?? keys[0];
}

function inferYKeys(data: Record<string, unknown>[], requested?: string[] | null, xKey?: string, seriesKey?: string) {
  if (!data.length) return requested ?? [];
  const keys = Object.keys(data[0]).filter((k) => k !== xKey && k !== seriesKey);
  const validRequested = (requested ?? []).filter((k) => keys.includes(k));
  if (validRequested.length > 0) return validRequested;

  const numeric = keys.filter((key) => data.some((row) => toNumber(row[key]) !== null));
  const preferred = numeric.filter((k) => /(revenue|sales|profit|margin|order|quantity|volume|change|growth|yoy|mom|qoq)/i.test(k));
  return (preferred.length > 0 ? preferred : numeric).slice(0, 2);
}

function pivotSeriesData(
  data: Record<string, unknown>[],
  xKey: string,
  seriesKey: string,
  valueKey: string
) {
  const grouped: Record<string, Record<string, unknown>> = {};

  for (const row of data) {
    const xVal = String(row[xKey] ?? "");
    const sVal = String(row[seriesKey] ?? "");
    const rawValue = row[valueKey];
    const vVal = toNumber(rawValue);

    if (!grouped[xVal]) {
      grouped[xVal] = { [xKey]: xVal };
    }

    grouped[xVal][sVal] = vVal ?? rawValue;
  }

  return Object.values(grouped);
}

function getSeriesNames(data: Record<string, unknown>[], seriesKey: string): string[] {
  return Array.from(new Set(data.map((row) => String(row[seriesKey] ?? "")).filter(Boolean)));
}

function coerceNumbers(data: Record<string, unknown>[], keys: string[]) {
  return data.map((row) => {
    const clone: Record<string, unknown> = { ...row };
    keys.forEach((key) => {
      const num = toNumber(clone[key]);
      if (num !== null) clone[key] = num;
    });
    return clone;
  });
}

function maybeSortByX(data: Record<string, unknown>[], xKey: string) {
  const values = data.map((row) => String(row[xKey] ?? ""));
  const looksDateLike = values.every(
    (v) => /^\d{4}([-/]\d{2}){0,2}$/.test(v) || !Number.isNaN(Date.parse(v)) || /^Q[1-4]\s?\d{4}$/i.test(v)
  );
  if (!looksDateLike) return data;

  const quarterToDate = (value: string) => {
    const match = value.match(/^Q([1-4])\s?(\d{4})$/i);
    if (match) {
      const q = Number(match[1]);
      const year = Number(match[2]);
      return new Date(year, (q - 1) * 3, 1).getTime();
    }
    return new Date(value).getTime();
  };

  return [...data].sort((a, b) => quarterToDate(String(a[xKey] ?? "")) - quarterToDate(String(b[xKey] ?? "")));
}

const valueFormatter = (value: unknown) => {
  if (typeof value === "number") {
    if (Math.abs(value) >= 1000) return value.toLocaleString();
    return Number(value.toFixed(2)).toString();
  }
  return String(value ?? "");
};

export function ChatChartBlock({ chartType, title, x, y, series, data, notes }: Props) {
  if (!data || data.length === 0) return null;

  const xKey = inferXKey(data, x);
  let normalizedSeries = series && data.length > 0 && Object.keys(data[0]).includes(series) ? series : undefined;
  const yKeys = inferYKeys(data, y, xKey, normalizedSeries);
  if (!xKey || yKeys.length === 0) {
    return <div className="empty-tab-state">Chart rendering is not available for this result set.</div>;
  }

  let chartData = coerceNumbers(data, yKeys);
  chartData = maybeSortByX(chartData, xKey);

  let seriesNames: string[] = [];

  if (normalizedSeries && yKeys.length === 1) {
    seriesNames = getSeriesNames(chartData, normalizedSeries);
    chartData = pivotSeriesData(chartData, xKey, normalizedSeries, yKeys[0]);
    chartData = maybeSortByX(chartData, xKey);
    if (seriesNames.length === 0) normalizedSeries = undefined;
  }

  const normalizedType = chartType === "grouped_bar" ? "bar" : chartType;
  const titleText = title || "Visualization";

  const effectiveSeries = normalizedSeries && seriesNames.length > 0 ? normalizedSeries : undefined;

  return (
    <div className="chart-card-shell" style={{ background: CARD, border: "1px solid #E5E7EB", borderRadius: 16, padding: 18, overflowX: "auto" }}>
      <div style={{ fontSize: 24, fontWeight: 700, color: "#111827", marginBottom: 14, lineHeight: 1.3 }}>{titleText}</div>

      <div style={{ border: "1px solid #E5E7EB", borderRadius: 14, padding: 16, background: "#FFFFFF" }}>
        <div style={{ width: "100%", height: 360 }}>
          <ResponsiveContainer>
            {normalizedType === "bar" ? (
              <BarChart data={chartData} margin={{ top: 8, right: 16, left: 8, bottom: 28 }}>
                <CartesianGrid stroke={GRID} strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey={xKey} tick={{ fill: AXIS, fontSize: 12 }} angle={-45} textAnchor="end" height={70} interval={0} />
                <YAxis tick={{ fill: AXIS, fontSize: 12 }} tickFormatter={valueFormatter} />
                <Tooltip formatter={(value) => valueFormatter(value)} />
                <Legend wrapperStyle={{ paddingTop: 8 }} />
                {effectiveSeries ? (
                  seriesNames.map((seriesName, index) => (
                    <Bar key={seriesName} dataKey={seriesName} radius={[4, 4, 0, 0]} fill={PALETTE[index % PALETTE.length]} />
                  ))
                ) : yKeys.length > 1 ? (
                  yKeys.map((key, index) => <Bar key={key} dataKey={key} radius={[4, 4, 0, 0]} fill={PALETTE[index % PALETTE.length]} />)
                ) : (
                  <Bar dataKey={yKeys[0]} radius={[4, 4, 0, 0]}>
                    {chartData.map((_, index) => (
                      <Cell key={index} fill={PALETTE[index % PALETTE.length]} />
                    ))}
                  </Bar>
                )}
              </BarChart>
            ) : (
              <LineChart data={chartData} margin={{ top: 8, right: 16, left: 8, bottom: 18 }}>
                <CartesianGrid stroke={GRID} strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey={xKey} tick={{ fill: AXIS, fontSize: 12 }} />
                <YAxis tick={{ fill: AXIS, fontSize: 12 }} tickFormatter={valueFormatter} />
                <Tooltip formatter={(value) => valueFormatter(value)} />
                <Legend wrapperStyle={{ paddingTop: 8 }} />
                {effectiveSeries ? (
                  seriesNames.map((seriesName, index) => (
                    <Line
                      key={seriesName}
                      type="monotone"
                      dataKey={seriesName}
                      dot={false}
                      activeDot={{ r: 4 }}
                      stroke={PALETTE[index % PALETTE.length]}
                      strokeWidth={3}
                      connectNulls
                    />
                  ))
                ) : (
                  yKeys.map((key, index) => (
                    <Line
                      key={key}
                      type="monotone"
                      dataKey={key}
                      name={key.replace(/_/g, " ")}
                      dot={false}
                      activeDot={{ r: 4 }}
                      stroke={PALETTE[index % PALETTE.length]}
                      strokeWidth={3}
                      connectNulls
                    />
                  ))
                )}
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>
      </div>

      {notes && <div style={{ marginTop: 10, fontSize: 12, color: "#6B7280" }}>{notes}</div>}
    </div>
  );
}
