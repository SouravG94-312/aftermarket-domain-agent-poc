export type BackendChatRequest = {
  question: string;
  adapter?: string;
  user_role?: string;
  user_scope?: Record<string, unknown>;
  session_id?: string | null;
};

export type BackendTable = {
  type?: string;
  sql?: string | null;
  rows?: Record<string, unknown>[];
  raw_response?: any;
  conversation_id?: string | null;
};

export type BackendChart = {
  chart_type?: string | null;
  title?: string | null;
  x?: string | null;
  y?: string[] | null;
  series?: string | null;
  notes?: string | null;
  data?: Record<string, unknown>[] | null;
};

export type BackendChatResponse = {
  summary?: string | null;
  table?: BackendTable | null;
  chart?: BackendChart | null;
  reasoning?: string | null;
  suggested_questions?: string[] | null;
  trace?: Record<string, unknown> | null;
  workflow?: string | null;
  session_id?: string | null;
};

export type UiBlock =
  | { type: "text"; content: string }
  | { type: "chart"; chartType: string; title?: string | null; x?: string | null; y?: string[] | null; series?: string | null; data: Record<string, unknown>[]; notes?: string | null }
  | { type: "table"; rows: Record<string, unknown>[]; columns: string[]; sql?: string | null }
  | { type: "sql"; content: string };

export type UiChatMessage = {
  role: "user" | "assistant";
  blocks: UiBlock[];
  suggestedQuestions?: string[];
  trace?: Record<string, unknown> | null;
};
