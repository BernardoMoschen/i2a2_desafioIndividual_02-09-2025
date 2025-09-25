import { ChangeEvent, useRef } from "react";
import { clsx } from "clsx";

import type { DatasetInfo } from "../api/client";

interface DatasetOption {
  id: string;
  info: DatasetInfo;
}

interface FileUploadCardProps {
  datasets: DatasetOption[];
  selectedDatasetId: string | null;
  onSelectDataset: (datasetId: string) => void;
  onUploadFile: (file: File) => void;
  isUploading: boolean;
}

export const FileUploadCard = ({
  datasets,
  selectedDatasetId,
  onSelectDataset,
  onUploadFile,
  isUploading
}: FileUploadCardProps) => {
  const fileRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onUploadFile(file);
      event.target.value = "";
    }
  };

  const handleSelect = (event: ChangeEvent<HTMLSelectElement>) => {
    onSelectDataset(event.target.value);
  };

  const currentDataset = datasets.find((item) => item.id === selectedDatasetId);

  return (
    <section className="card">
      <header className="grid two-columns" style={{ alignItems: "center" }}>
        <div>
          <span className="badge">Dataset</span>
          <h2>Gerencie os arquivos CSV</h2>
          <p>Envie um novo arquivo ou selecione um dataset já carregado para realizar perguntas.</p>
        </div>
        <div style={{ textAlign: "right" }}>
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            disabled={isUploading}
            className={clsx({ uploading: isUploading })}
          >
            {isUploading ? "Carregando..." : "Enviar novo CSV"}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="text/csv"
            style={{ display: "none" }}
            onChange={handleFileChange}
          />
        </div>
      </header>

      <div className="grid" style={{ marginTop: "1.5rem" }}>
        <label>
          <span style={{ display: "block", marginBottom: "0.5rem", fontWeight: 600 }}>
            Datasets disponíveis
          </span>
          <select value={selectedDatasetId ?? ""} onChange={handleSelect}>
            <option value="" disabled>
              Selecione um dataset carregado
            </option>
            {datasets.map((dataset) => (
              <option key={dataset.id} value={dataset.id}>
                {dataset.id} — {dataset.info.rows} linhas
              </option>
            ))}
          </select>
        </label>
      </div>

      {currentDataset ? (
        <dl className="grid two-columns" style={{ marginTop: "1.5rem" }}>
          <div>
            <dt>Caminho</dt>
            <dd>{currentDataset.info.path}</dd>
          </div>
          <div>
            <dt>Linhas</dt>
            <dd>{currentDataset.info.rows}</dd>
          </div>
          <div>
            <dt>Colunas</dt>
            <dd>{currentDataset.info.columns}</dd>
          </div>
        </dl>
      ) : (
        <p style={{ marginTop: "1.5rem", color: "#cbd5f5" }}>
          Nenhum dataset selecionado. Faça upload de um CSV ou escolha na lista acima.
        </p>
      )}
    </section>
  );
};
