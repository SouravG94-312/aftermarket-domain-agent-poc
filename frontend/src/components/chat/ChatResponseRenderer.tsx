import React, { useMemo } from "react";
import { UiChatMessage } from "../../types/chat";
import { ChatTextBlock } from "./ChatTextBlock";
import { ChatTableBlock } from "./ChatTableBlock";
import { ChatChartBlock } from "./ChatChartBlock";
import { SuggestedQuestions } from "./SuggestedQuestions";
import { ChatSqlBlock } from "./ChatSqlBlock";

type Props = {
  message: UiChatMessage;
  onSuggestedQuestionClick: (question: string) => void;
};

type FlowStep = {
  step?: number;
  from?: string;
  to?: string;
  action?: string;
  detail?: string;
};

function getAgentFlow(trace?: Record<string, unknown> | null): FlowStep[] {
  if (!trace) return [];
  const flow = trace.agent_flow;
  return Array.isArray(flow) ? (flow as FlowStep[]) : [];
}

function AgentFlowPanel({ trace }: { trace?: Record<string, unknown> | null }) {
  const flow = getAgentFlow(trace);
  if (!trace && flow.length === 0) return null;

  return (
    <details className="agent-flow-panel">
      <summary>Agent communication flow</summary>
      {flow.length > 0 ? (
        <div className="agent-flow-steps">
          {flow.map((step, index) => (
            <div className="agent-flow-step" key={`${step.step ?? index}-${step.action ?? "step"}`}>
              <div className="agent-flow-step-number">{step.step ?? index + 1}</div>
              <div className="agent-flow-step-body">
                <div className="agent-flow-route">
                  <strong>{step.from ?? "source"}</strong>
                  <span>→</span>
                  <strong>{step.to ?? "target"}</strong>
                </div>
                <div className="agent-flow-action">{step.action ?? "action"}</div>
                {step.detail && <div className="agent-flow-detail">{step.detail}</div>}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <pre className="agent-flow-json">{JSON.stringify(trace, null, 2)}</pre>
      )}
    </details>
  );
}


function SectionIcon({ children }: { children: React.ReactNode }) {
  return <span className="single-output-section-icon">{children}</span>;
}

function InsightIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="single-output-svg-icon">
      <path d="M9 18h6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M10 21h4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M12 3a5.5 5.5 0 0 0-3.7 9.58c.9.82 1.45 1.58 1.67 2.42h4.06c.22-.84.78-1.6 1.67-2.42A5.5 5.5 0 0 0 12 3Z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
    </svg>
  );
}

function ChartIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="single-output-svg-icon">
      <path d="M4 19h16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M6 16 10 11l3 2 5-6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M6 19V8" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function TableIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="single-output-svg-icon">
      <rect x="4" y="5" width="16" height="14" rx="2" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path d="M4 10h16M9 5v14M15 5v14" fill="none" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}

export function ChatResponseRenderer({ message, onSuggestedQuestionClick }: Props) {
  const insightBlocks = useMemo(() => message.blocks.filter((b) => b.type === "text"), [message.blocks]);
  const chartBlocks = useMemo(() => message.blocks.filter((b) => b.type === "chart"), [message.blocks]);
  const tableBlocks = useMemo(() => message.blocks.filter((b) => b.type === "table"), [message.blocks]);
  const sqlBlocks = useMemo(() => message.blocks.filter((b) => b.type === "sql"), [message.blocks]);

  const hasInsights = insightBlocks.length > 0;
  const hasCharts = chartBlocks.length > 0;
  const hasTables = tableBlocks.length > 0;
  const hasSql = sqlBlocks.length > 0;

  return (
    <div className="message-row assistant-row production-assistant-row single-output-row">
      <div className="avatar-circle assistant-avatar production-assistant-avatar">IQ</div>
      <div className="assistant-content-column production-assistant-column single-output-column">
        <article className="workspace-card single-output-card" aria-label="Assistant response">
          <div className="single-output-header">
            <div className="single-output-title-wrap">
              <div className="single-output-avatar">IQ</div>
              <div>
                <div className="single-output-eyebrow">Agent answer</div>
                <h2 className="single-output-title">Insights, evidence and data in one response</h2>
              </div>
            </div>
            <div className="single-output-meta">MCP + A2A</div>
          </div>

          {hasInsights && (
            <section className="single-output-section single-output-insight-section">
              <div className="single-output-section-heading">
                <SectionIcon><InsightIcon /></SectionIcon>
                <span>Insight</span>
              </div>
              <div className="single-output-section-body single-output-insight-body">
                {insightBlocks.map((block, index) =>
                  block.type === "text" ? <ChatTextBlock key={index} content={block.content} /> : null
                )}
              </div>
            </section>
          )}

          {hasCharts && (
            <section className="single-output-section single-output-chart-section">
              <div className="single-output-section-heading">
                <SectionIcon><ChartIcon /></SectionIcon>
                <span>Chart</span>
              </div>
              <div className="single-output-section-body single-output-chart-body">
                {chartBlocks.map((block, index) =>
                  block.type === "chart" ? (
                    <ChatChartBlock
                      key={index}
                      chartType={block.chartType}
                      title={block.title}
                      x={block.x}
                      y={block.y}
                      series={block.series}
                      data={block.data}
                      notes={block.notes}
                    />
                  ) : null
                )}
              </div>
            </section>
          )}

          {hasTables && (
            <section className="single-output-section single-output-table-section">
              <div className="single-output-section-heading">
                <SectionIcon><TableIcon /></SectionIcon>
                <span>Table</span>
              </div>
              <div className="single-output-section-body single-output-table-body">
                {tableBlocks.map((block, index) =>
                  block.type === "table" ? <ChatTableBlock key={index} rows={block.rows} columns={block.columns} /> : null
                )}
              </div>
            </section>
          )}

          {hasSql && (
            <details className="sql-details single-output-sql-details">
              <summary>View SQL</summary>
              {sqlBlocks.map((block, index) =>
                block.type === "sql" ? <ChatSqlBlock key={index} content={block.content} /> : null
              )}
            </details>
          )}

          {!hasInsights && !hasCharts && !hasTables && (
            <div className="empty-tab-state">No response content was returned.</div>
          )}

          <AgentFlowPanel trace={message.trace} />
        </article>

        {message.suggestedQuestions && message.suggestedQuestions.length > 0 && (
          <SuggestedQuestions questions={message.suggestedQuestions} onClick={onSuggestedQuestionClick} />
        )}
      </div>
    </div>
  );
}
