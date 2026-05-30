import React from "react";

type Props = { content: string };

export function ChatSqlBlock({ content }: Props) {
  return (
    <pre className="sql-block">
      <code>{content}</code>
    </pre>
  );
}
