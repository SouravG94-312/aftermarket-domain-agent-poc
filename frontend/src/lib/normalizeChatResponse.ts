import { BackendChatResponse, UiBlock, UiChatMessage } from "../types/chat";

function extractSuggestedQuestionsFromRaw(response: BackendChatResponse): string[] {
  const attachments = response.table?.raw_response?.attachments ?? [];
  for (const attachment of attachments) {
    if (attachment?.suggested_questions?.questions) {
      return attachment.suggested_questions.questions;
    }
  }
  return [];
}

function buildInsightText(response: BackendChatResponse): string | null {
  const parts: string[] = [];

  if (response.summary && response.summary.trim()) {
    parts.push(response.summary.trim());
  }

  if (
    response.reasoning &&
    response.reasoning.trim() &&
    response.reasoning.trim() !== response.summary?.trim()
  ) {
    parts.push(response.reasoning.trim());
  }

  const combined = parts.join("\n\n");
  return combined.length > 0 ? combined : null;
}

type ParsedMarkdownTable = {
  cleanedText: string;
  rows: Record<string, unknown>[];
  columns: string[];
};

function normalizeHeaderCell(cell: string): string {
  return cell
    .trim()
    .replace(/[*`]/g, "")
    .replace(/\s+/g, " ")
    .replace(/^\W+|\W+$/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function parseValue(raw: string): unknown {
  const value = raw.trim().replace(/[*`]/g, "");
  if (!value) return "";
  const numericCandidate = value.replace(/,/g, "").replace(/[€$£]/g, "").replace(/%$/, "");
  const num = Number(numericCandidate);
  if (!Number.isNaN(num) && numericCandidate !== "") return num;
  return value;
}

function parseMarkdownTable(text: string | null): ParsedMarkdownTable | null {
  if (!text) return null;
  const lines = text.split(/\r?\n/);
  let start = -1;

  for (let i = 0; i < lines.length - 1; i += 1) {
    const line = lines[i].trim();
    const next = lines[i + 1].trim();
    if (line.includes("|") && /^\|?\s*[:-]+[-| :]*\|?\s*$/.test(next)) {
      start = i;
      break;
    }
  }

  if (start === -1) return null;

  const tableLines: string[] = [];
  let end = start;
  for (let i = start; i < lines.length; i += 1) {
    const line = lines[i].trim();
    if (!line.includes("|")) break;
    tableLines.push(lines[i]);
    end = i;
  }

  if (tableLines.length < 2) return null;

  const splitCells = (line: string) =>
    line
      .trim()
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => cell.trim());

  const rawHeaders = splitCells(tableLines[0]);
  const headers = rawHeaders.map((cell, idx) => normalizeHeaderCell(cell) || `column_${idx + 1}`);
  const dataLines = tableLines.slice(2);

  const rows = dataLines
    .map((line) => splitCells(line))
    .filter((cells) => cells.some((cell) => cell !== ""))
    .map((cells) => {
      const row: Record<string, unknown> = {};
      headers.forEach((header, idx) => {
        row[header] = parseValue(cells[idx] ?? "");
      });
      return row;
    });

  const cleanedLines = [...lines.slice(0, start), ...lines.slice(end + 1)];
  const cleanedText = cleanedLines.join("\n").replace(/\n{3,}/g, "\n\n").trim();

  if (!rows.length) return null;
  return { cleanedText, rows, columns: headers };
}

function isNumericValue(value: unknown): boolean {
  return typeof value === "number" && Number.isFinite(value);
}

function inferGroupedSeriesKey(columns: string[], rows: Record<string, unknown>[], xKey: string, metricKeys: string[]) {
  return columns.find((col) =>
    col !== xKey &&
    !metricKeys.includes(col) &&
    rows.some((row) => typeof row[col] === "string" && String(row[col]).trim() !== "") &&
    /(country|market|region|dealer|segment|group|name)/i.test(col)
  ) ?? null;
}

function inferChartFromRows(rows: Record<string, unknown>[]) {
  if (!rows.length) return null;
  const columns = Object.keys(rows[0]);
  if (!columns.length) return null;

  const timeKey = columns.find((col) => /(month|quarter|year|date|period)/i.test(col));
  const numericCols = columns.filter((col) => rows.some((row) => isNumericValue(row[col])));
  const metricCols = numericCols.filter((col) => !/(id|code)$/i.test(col));

  if (!timeKey || metricCols.length === 0) return null;

  const primaryMetric =
    metricCols.find((col) => /(revenue|sales|turnover|amount|value)/i.test(col)) ?? metricCols[0];
  const secondaryMetric = metricCols.find((col) => col !== primaryMetric && /(yoy|mom|qoq|change|growth)/i.test(col)) ?? null;

  const groupKey = inferGroupedSeriesKey(columns, rows, timeKey, metricCols);

  if (groupKey) {
    return {
      chart_type: "line",
      title: "Auto-generated visualization",
      x: timeKey,
      y: [primaryMetric],
      series: groupKey,
      data: rows,
      notes: "Auto-derived multi-series trend chart from tabular result.",
    };
  }

  return {
    chart_type: /month|quarter|year|date|period/i.test(timeKey) ? "line" : "bar",
    title: "Auto-generated visualization",
    x: timeKey,
    y: secondaryMetric ? [primaryMetric, secondaryMetric] : [primaryMetric],
    series: null,
    data: rows,
    notes: "Auto-derived from tabular result in the insight text.",
  };
}

function enrichChart(chart: NonNullable<BackendChatResponse["chart"]>, rows: Record<string, unknown>[]) {
  const data = chart.data && chart.data.length > 0 ? chart.data : rows;
  if (!data.length) return chart;

  const columns = Object.keys(data[0]);
  const xKey = chart.x && columns.includes(chart.x) ? chart.x : columns.find((col) => /(month|quarter|year|date|period)/i.test(col)) ?? chart.x ?? null;
  const yKeys = (chart.y ?? []).filter((col) => columns.includes(col));
  const numericCols = columns.filter((col) => data.some((row) => isNumericValue(row[col])));
  const metricCols = (yKeys.length > 0 ? yKeys : numericCols).filter((col) => !/(id|code)$/i.test(col));
  const primaryMetric = metricCols.find((col) => /(revenue|sales|turnover|amount|value)/i.test(col)) ?? metricCols[0] ?? null;
  const groupKey = xKey ? inferGroupedSeriesKey(columns, data, xKey, metricCols) : null;

  const enrichedY = chart.y && chart.y.length > 0 ? chart.y : (primaryMetric ? [primaryMetric] : []);
  const inferredType = chart.chart_type || (xKey ? "line" : "bar");

  return {
    ...chart,
    chart_type: xKey && groupKey ? "line" : inferredType,
    x: xKey ?? chart.x,
    y: enrichedY,
    series: chart.series && columns.includes(chart.series) ? chart.series : (groupKey ?? chart.series ?? null),
    data,
  };
}

export function normalizeChatResponse(response: BackendChatResponse): UiChatMessage {
  const blocks: UiBlock[] = [];

  const rawInsightText = buildInsightText(response);
  const parsedMarkdownTable = parseMarkdownTable(rawInsightText);
  const insightText = parsedMarkdownTable ? parsedMarkdownTable.cleanedText : rawInsightText;

  if (insightText) {
    blocks.push({
      type: "text",
      content: insightText,
    });
  }

  const backendTableRows = response.table?.rows ?? [];
  const derivedTableRows = backendTableRows.length > 0 ? backendTableRows : parsedMarkdownTable?.rows ?? [];
  const derivedColumns = backendTableRows.length > 0
    ? Object.keys(backendTableRows[0])
    : parsedMarkdownTable?.columns ?? [];

  const backendChartData = response.chart?.data ?? [];
  const effectiveChart = response.chart && (backendChartData.length > 0 || derivedTableRows.length > 0)
    ? enrichChart(
        {
          ...response.chart,
          data: backendChartData.length > 0 ? backendChartData : derivedTableRows,
        },
        derivedTableRows,
      )
    : inferChartFromRows(derivedTableRows);

  if (effectiveChart && (effectiveChart.data?.length ?? 0) > 0) {
    blocks.push({
      type: "chart",
      chartType: effectiveChart.chart_type ?? "bar",
      title: effectiveChart.title ?? undefined,
      x: effectiveChart.x ?? undefined,
      y: effectiveChart.y ?? undefined,
      series: effectiveChart.series ?? undefined,
      data: effectiveChart.data ?? [],
      notes: effectiveChart.notes ?? undefined,
    });
  }

  if (derivedTableRows.length > 0) {
    blocks.push({
      type: "table",
      rows: derivedTableRows,
      columns: derivedColumns,
      sql: response.table?.sql ?? undefined,
    });
  }

  if (response.table?.sql && response.table.sql.trim()) {
    blocks.push({
      type: "sql",
      content: response.table.sql.trim(),
    });
  }

  const suggestedQuestions =
    response.suggested_questions && response.suggested_questions.length > 0
      ? response.suggested_questions
      : extractSuggestedQuestionsFromRaw(response);

  return {
    role: "assistant",
    blocks,
    suggestedQuestions,
    trace: response.trace ?? null,
  };
}
