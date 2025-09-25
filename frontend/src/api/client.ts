import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8080";

export const http = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json"
  }
});

export interface UploadResponse {
  dataset_id: string;
  rows: string;
}

export interface AskResponse {
  answer: string;
}

export interface DatasetInfo {
  path: string;
  rows: string;
  columns: string;
}

export const uploadDataset = async (file: File): Promise<UploadResponse> => {
  const form = new FormData();
  form.append("file", file);
  const response = await http.post<UploadResponse>("/upload", form, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
};

export const askQuestion = async (datasetId: string, question: string): Promise<AskResponse> => {
  const response = await http.post<AskResponse>("/ask", { dataset_id: datasetId, question });
  return response.data;
};

export const listDatasets = async (): Promise<Record<string, DatasetInfo>> => {
  const response = await http.get<Record<string, DatasetInfo>>("/datasets");
  return response.data;
};
