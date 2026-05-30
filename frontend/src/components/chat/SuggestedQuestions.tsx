import React from "react";

type Props = {
  questions: string[];
  onClick: (question: string) => void;
};

const icons = ["↗", "⇄", "🗓", "◉"];

export function SuggestedQuestions({ questions, onClick }: Props) {
  return (
    <div className="suggested-shell production-suggested-shell">
      <div className="suggested-title">Suggested follow-up questions</div>
      <div className="suggested-grid production-suggested-grid">
        {questions.map((question, index) => (
          <button key={question} className="suggested-chip production-suggested-chip" onClick={() => onClick(question)}>
            <span className="chip-icon">{icons[index % icons.length]}</span>
            <span>{question}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
