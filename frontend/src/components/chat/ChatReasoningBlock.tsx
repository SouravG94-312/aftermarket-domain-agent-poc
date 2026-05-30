import React from "react";

export function ChatReasoningBlock({ content }: { content: string }) {
  return (
    <div className="rounded-lg border-l-4 pl-4 py-2 bg-gray-50">
      <div className="text-xs font-semibold uppercase mb-1">Insights</div>
      <div className="text-sm whitespace-pre-wrap">{content}</div>
    </div>
  );
}