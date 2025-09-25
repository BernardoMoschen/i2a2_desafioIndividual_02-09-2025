import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  askQuestion,
  listDatasets,
  uploadDataset,
  type DatasetInfo,
  type AskResponse,
  type UploadResponse
} from "./api/client";
import { FileUploadCard } from "./components/FileUploadCard";
import { QuestionCard } from "./components/QuestionCard";
import { AnswerPanel } from "./components/AnswerPanel";

interface AskVariables {
  datasetId: string;
  question: string;
}

interface HistoryItem {
  id: string;
  question: string;
  answer: string;
  createdAt: string;
}

const makeHistoryId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

const mapDatasets = (datasets: Record<string, DatasetInfo> | undefined) =>
  Object.entries(datasets ?? {}).map(([id, info]) => ({ id, info }));

const App = () => {
  const queryClient = useQueryClient();
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
  const [latestAnswer, setLatestAnswer] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const datasetsQuery = useQuery({ queryKey: ["datasets"], queryFn: listDatasets });

  const uploadMutation = useMutation<UploadResponse, unknown, File>({
    mutationFn: uploadDataset,
    onSuccess: (data: UploadResponse) => {
      void queryClient.invalidateQueries({ queryKey: ["datasets"] });
      setSelectedDatasetId(data.dataset_id);
      setErrorMessage(null);
    },
    onError: (error: unknown) => {
      setErrorMessage(error instanceof Error ? error.message : "Falha ao enviar o dataset.");
    }
  });

  const askMutation = useMutation<AskResponse, unknown, AskVariables>({
    mutationFn: ({ datasetId, question }: AskVariables) => askQuestion(datasetId, question),
    onSuccess: (data: AskResponse, variables: AskVariables) => {
      setLatestAnswer(data.answer);
      setHistory((prev: HistoryItem[]) => [
        {
          id: makeHistoryId(),
          question: variables.question,
          answer: data.answer,
          createdAt: new Date().toISOString()
        },
        ...prev
      ]);
      setErrorMessage(null);
    },
    onError: (error: unknown) => {
      setErrorMessage(error instanceof Error ? error.message : "Erro ao consultar o agente.");
    }
  });

  const datasetOptions = useMemo(() => mapDatasets(datasetsQuery.data), [datasetsQuery.data]);

  const handleAsk = (question: string) => {
    if (!selectedDatasetId) {
      setErrorMessage("Selecione ou envie um dataset antes de fazer perguntas.");
      return;
    }
    askMutation.mutate({ datasetId: selectedDatasetId, question });
  };

  return (
    <main>
      <header className="card" style={{ textAlign: "center", padding: "2.5rem 2rem" }}>
        <div className="badge">I2A2 • Agente Autônomo</div>
        <h1>Central de Insights para CSVs</h1>
        <p>
          Faça upload de um arquivo, realize perguntas em linguagem natural e receba análises inteligentes,
          gráficos e conclusões geradas pelo agente LangChain.
        </p>
      </header>

      {errorMessage && (
        <div className="card" style={{ borderColor: "rgba(248, 113, 113, 0.35)", color: "#fecaca" }}>
          <strong>Algo deu errado:</strong>
          <p>{errorMessage}</p>
        </div>
      )}

      <FileUploadCard
        datasets={datasetOptions}
        selectedDatasetId={selectedDatasetId}
        onSelectDataset={(id) => setSelectedDatasetId(id)}
        onUploadFile={(file) => uploadMutation.mutate(file)}
        isUploading={uploadMutation.isPending}
      />

      <QuestionCard
        disabled={!selectedDatasetId || uploadMutation.isPending}
        onSubmit={handleAsk}
        isLoading={askMutation.isPending}
      />

      <AnswerPanel latestAnswer={latestAnswer} history={history} />
    </main>
  );
};

export default App;
