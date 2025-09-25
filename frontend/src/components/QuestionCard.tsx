import { FormEvent, useState } from "react";
import type { ChangeEvent } from "react";

interface QuestionCardProps {
  disabled: boolean;
  onSubmit: (question: string) => void;
  isLoading: boolean;
}

export const QuestionCard = ({ disabled, onSubmit, isLoading }: QuestionCardProps) => {
  const [question, setQuestion] = useState<string>("");

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!question.trim()) {
      return;
    }
    onSubmit(question);
    setQuestion("");
  };

  return (
    <section className="card">
      <span className="badge">Perguntas</span>
      <h2>Converse com o agente</h2>
      <p>Faça perguntas em português. O agente utilizará ferramentas de estatística, gráficos e anomalias.</p>

      <form className="grid" style={{ marginTop: "1.5rem" }} onSubmit={handleSubmit}>
        <label>
          <span style={{ display: "block", marginBottom: "0.5rem", fontWeight: 600 }}>
            Sua pergunta
          </span>
          <textarea
            rows={3}
            placeholder="Ex.: Quais colunas têm maior correlação com a variável 'Class'?"
            value={question}
            onChange={(event: ChangeEvent<HTMLTextAreaElement>) => setQuestion(event.target.value)}
            disabled={disabled || isLoading}
          />
        </label>
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <button type="submit" disabled={disabled || isLoading}>
            {isLoading ? "Consultando..." : "Perguntar"}
          </button>
        </div>
      </form>
    </section>
  );
};
