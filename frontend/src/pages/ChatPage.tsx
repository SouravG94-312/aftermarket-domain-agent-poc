import React, { useEffect, useMemo, useRef, useState } from "react";
import { sendChatMessage } from "../api/chatApi";
import { normalizeChatResponse } from "../lib/normalizeChatResponse";
import { UiChatMessage } from "../types/chat";
import { ChatResponseRenderer } from "../components/chat/ChatResponseRenderer";

const DEFAULT_ADAPTER = "aftermarket_agent_cluster";
const DEFAULT_USER_ROLE = "aftermarket_user";
const STORAGE_KEY = "aftermarket-agent-session-messages";
const SESSION_ID_KEY = "aftermarket-agent-session-id";

const STARTER_QUESTIONS = [
  "Why was claim WC1001 rejected?",
  "Has VINDEF000123 had the same issue before?",
  "Is part P001 available in Germany?",
  "Give me a 360 summary of dealer DLR003.",
];

export function ChatPage() {
  const [messages, setMessages] = useState<UiChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [sessionId, setSessionId] = useState<string>(() => {
    const existing = sessionStorage.getItem(SESSION_ID_KEY);
    if (existing) return existing;
    const created = crypto.randomUUID();
    sessionStorage.setItem(SESSION_ID_KEY, created);
    return created;
  });

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as UiChatMessage[];
        if (Array.isArray(parsed)) setMessages(parsed);
      }
    } catch {}
  }, []);

  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function submitQuestion(question: string) {
    if (!question.trim() || loading) return;

    const userMessage: UiChatMessage = {
      role: "user",
      blocks: [{ type: "text", content: question.trim() }],
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const backendResponse = await sendChatMessage({
        question: question.trim(),
        adapter: DEFAULT_ADAPTER,
        user_role: DEFAULT_USER_ROLE,
        user_scope: {},
        session_id: sessionId,
      });

      if (backendResponse.session_id && backendResponse.session_id !== sessionId) {
        setSessionId(backendResponse.session_id);
        sessionStorage.setItem(SESSION_ID_KEY, backendResponse.session_id);
      }
      const assistantMessage = normalizeChatResponse(backendResponse);
      setMessages((prev) => [...prev, assistantMessage]);
      setInput("");
    } catch (error) {
      const errorMessage: UiChatMessage = {
        role: "assistant",
        blocks: [
          {
            type: "text",
            content:
              error instanceof Error
                ? `Something went wrong: ${error.message}`
                : "Something went wrong while processing your request.",
          },
        ],
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  }

  function resetConversation() {
    setMessages([]);
    setInput("");
    sessionStorage.removeItem(STORAGE_KEY);
    const created = crypto.randomUUID();
    setSessionId(created);
    sessionStorage.setItem(SESSION_ID_KEY, created);
  }

  const hasMessages = messages.length > 0;
  const content = useMemo(() => (hasMessages ? messages : []), [hasMessages, messages]);

  return (
    <div className="chat-app-shell production-shell">
      <header className="chat-app-header production-header">
        <div className="brand-shell">
          <div className="brand-mark">IQ</div>
          <div>
            <h1>Aftermarket Agent Cluster</h1>
            <p>Warranty, service, parts and dealer-performance agents powered by MCP + A2A</p>
          </div>
        </div>
        <div className="header-actions">
          <button className="reset-button icon-button" onClick={resetConversation}>
            ↻ <span>Reset</span>
          </button>
          <button className="user-menu" type="button">
            <span className="user-menu-avatar">SS</span>
            <span>Sourav</span>
            <span className="caret">⌄</span>
          </button>
        </div>
      </header>

      <div className="connection-status production-status">
        <span className="status-dot" /> Connected
      </div>

      <main className="chat-main-panel production-main-panel" ref={scrollRef}>
        {!hasMessages ? (
          <div className="empty-state">
            <div className="empty-card production-empty-card">
              <div className="assistant-badge">IQ</div>
              <div>
                <h2>Ask an aftermarket question to route it to the right specialist agent</h2>
                <p>Use natural language to analyze trends, compare markets, inspect dealers, and review KPIs.</p>
                <div className="starter-grid">
                  {STARTER_QUESTIONS.map((q) => (
                    <button key={q} className="starter-chip" onClick={() => submitQuestion(q)}>
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="messages-stack production-stack">
            {content.map((message, index) =>
              message.role === "user" ? (
                <div key={index} className="message-row user-row production-user-row">
                  <div className="user-bubble production-user-bubble">
                    {message.blocks.map((block, idx) =>
                      block.type === "text" ? (
                        <div key={idx} className="user-text">
                          {block.content}
                        </div>
                      ) : null
                    )}
                  </div>
                  <div className="avatar-circle user-avatar production-user-avatar">U</div>
                </div>
              ) : (
                <ChatResponseRenderer key={index} message={message} onSuggestedQuestionClick={submitQuestion} />
              )
            )}
            {loading && (
              <div className="message-row assistant-row">
                <div className="avatar-circle assistant-avatar">IQ</div>
                <div className="response-shell loading-shell">Thinking…</div>
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="chat-footer production-footer">
        <div className="composer-shell production-composer-shell">
          <button className="composer-attachment" type="button" aria-label="Attach file" title="Attach">
            ⌘
          </button>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a follow-up question..."
            className="composer-input production-composer-input"
            onKeyDown={(e) => {
              if (e.key === "Enter") submitQuestion(input);
            }}
          />
          <button
            onClick={() => submitQuestion(input)}
            disabled={loading}
            className="send-button production-send-button"
            aria-label="Send message"
            title="Send"
          >
            {loading ? "…" : "➤"}
          </button>
        </div>
      </footer>
    </div>
  );
}
