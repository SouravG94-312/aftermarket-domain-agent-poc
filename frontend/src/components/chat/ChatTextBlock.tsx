import React from "react";

type Props = {
  content: string;
};

function renderInline(text: string, keyPrefix: string) {
  const cleaned = text.replace(/\\\*\\\*/g, "**");
  const parts = cleaned.split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
  return parts.map((part, idx) => {
    if (/^\*\*[^*]+\*\*$/.test(part)) {
      return <strong key={`${keyPrefix}-${idx}`}>{part.slice(2, -2)}</strong>;
    }
    return <React.Fragment key={`${keyPrefix}-${idx}`}>{part}</React.Fragment>;
  });
}

export function ChatTextBlock({ content }: Props) {
  const normalized = String(content ?? "").replace(/\r\n/g, "\n").trim();
  const sections = normalized.split(/\n{2,}/).filter(Boolean);

  return (
    <div className="insight-panel">
      {sections.map((section, index) => {
        const trimmed = section.trim();
        const lines = trimmed.split(/\n/).filter(Boolean);

        if (/^#{1,6}\s/.test(trimmed)) {
          return (
            <h3 key={index} className="insight-heading">
              {trimmed.replace(/^#{1,6}\s/, "")}
            </h3>
          );
        }

        if (
          lines.length > 1 &&
          lines.every(
            (line) => /^[-*•]\s/.test(line.trim()) || /^\d+\.\s/.test(line.trim())
          )
        ) {
          return (
            <ul key={index} className="insight-list">
              {lines.map((line, liIndex) => (
                <li key={liIndex}>
                  {renderInline(line.replace(/^([-*•]|\d+\.)\s/, ""), `${index}-${liIndex}`)}
                </li>
              ))}
            </ul>
          );
        }

        return (
          <p key={index} className="insight-paragraph">
            {renderInline(trimmed, `${index}`)}
          </p>
        );
      })}
    </div>
  );
}
