import React, { useMemo, useState } from "react";
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

type RightTabKey = "chart" | "table";

function InsightIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="tab-svg-icon">
      <path d="M9 18h6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M10 21h4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M12 3a5.5 5.5 0 0 0-3.7 9.58c.9.82 1.45 1.58 1.67 2.42h4.06c.22-.84.78-1.6 1.67-2.42A5.5 5.5 0 0 0 12 3Z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/>
    </svg>
  );
}

function ChartIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="tab-svg-icon">
      <path d="M4 19h16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M6 16 10 11l3 2 5-6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M6 19V8" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function TableIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="tab-svg-icon">
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

  const defaultTab: RightTabKey = chartBlocks.length > 0 ? "chart" : "table";
  const [activeRightTab, setActiveRightTab] = useState<RightTabKey>(defaultTab);

  return (
    <div className="message-row assistant-row production-assistant-row">
      <div className="avatar-circle assistant-avatar production-assistant-avatar">IQ</div>
      <div className="assistant-content-column production-assistant-column">
        <div className="workspace-card">
          <div className="split-response-layout production-split-layout">
            <section className="production-panel production-panel-left">
              <div className="panel-toolbar panel-toolbar-left">
                <div className="panel-brand-badge">IQ</div>
                <div className="toolbar-pill toolbar-pill-active toolbar-pill-static">
                  <InsightIcon />
                  <span>INSIGHT</span>
                </div>
              </div>
              <div className="panel-card insight-card-scroll equal-panel-card">
                <div className="response-section-stack">
                  {insightBlocks.length > 0 ? (
                    insightBlocks.map((block, index) =>
                      block.type === "text" ? <ChatTextBlock key={index} content={block.content} /> : null
                    )
                  ) : (
                    <div className="empty-tab-state">No insight was returned for this response.</div>
                  )}
                </div>
              </div>
            </section>

            <section className="production-panel production-panel-right">
              <div className="panel-toolbar panel-toolbar-right">
                <button
                  className={`toolbar-pill ${activeRightTab === "chart" ? "toolbar-pill-active" : ""}`}
                  onClick={() => setActiveRightTab("chart")}
                  type="button"
                >
                  <ChartIcon />
                  <span>CHART</span>
                </button>
                <button
                  className={`toolbar-pill ${activeRightTab === "table" ? "toolbar-pill-active" : ""}`}
                  onClick={() => setActiveRightTab("table")}
                  type="button"
                >
                  <TableIcon />
                  <span>TABLE</span>
                </button>
              </div>

              <div className="panel-card analytics-card equal-panel-card">
                {activeRightTab === "chart" && (
                  <div className="response-section-stack analytics-scroll-region">
                    {chartBlocks.length > 0 ? (
                      chartBlocks.map((block, index) =>
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
                      )
                    ) : (
                      <div className="empty-tab-state">No chart was returned for this response.</div>
                    )}
                  </div>
                )}

                {activeRightTab === "table" && (
                  <div className="response-section-stack analytics-scroll-region">
                    {tableBlocks.length > 0 ? (
                      tableBlocks.map((block, index) =>
                        block.type === "table" ? <ChatTableBlock key={index} rows={block.rows} columns={block.columns} /> : null
                      )
                    ) : (
                      <div className="empty-tab-state">No table was returned for this response.</div>
                    )}

                    {sqlBlocks.length > 0 && (
                      <details className="sql-details">
                        <summary>View SQL</summary>
                        {sqlBlocks.map((block, index) =>
                          block.type === "sql" ? <ChatSqlBlock key={index} content={block.content} /> : null
                        )}
                      </details>
                    )}
                  </div>
                )}
              </div>
            </section>
          </div>

          {message.suggestedQuestions && message.suggestedQuestions.length > 0 && (
            <SuggestedQuestions questions={message.suggestedQuestions} onClick={onSuggestedQuestionClick} />
          )}
        </div>
      </div>
    </div>
  );
}
