interface HistoryItem {
  id: string;
  question: string;
  answer: string;
  createdAt: string;
}

interface AnswerPanelProps {
  latestAnswer: string | null;
  history: HistoryItem[];
}

export const AnswerPanel = ({ latestAnswer, history }: AnswerPanelProps) => {
  return (
    <section className="card">
      <span className="badge">Respostas</span>
      <h2>Insights recentes</h2>

      {latestAnswer ? (
        <article className="answer" style={{ marginTop: "1.5rem" }}>
          {latestAnswer}
        </article>
      ) : (
        <p style={{ marginTop: "1.5rem", color: "#cbd5f5" }}>
          Faça uma pergunta para receber a primeira resposta automatizada.
        </p>
      )}

      {history.length > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h3 style={{ marginBottom: "1rem" }}>Histórico</h3>
          <div className="grid">
            {history.map((item) => (
              <details key={item.id} className="card" style={{ margin: 0 }}>
                <summary style={{ cursor: "pointer" }}>
                  {new Date(item.createdAt).toLocaleString("pt-BR", {
                    dateStyle: "short",
                    timeStyle: "short"
                  })}
                  : {item.question}
                </summary>
                <div className="answer" style={{ marginTop: "1rem" }}>
                  {item.answer}
                </div>
              </details>
            ))}
          </div>
        </div>
      )}
    </section>
  );
};
