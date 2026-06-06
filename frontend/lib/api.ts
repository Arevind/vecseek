"use client";

import axios, { AxiosError } from "axios";

import type {
  Folder,
  FolderDetail,
  IndexStartResponse,
  IndexStatusResponse,
  RetrievalResponse,
  SettingsResponse,
  UploadResponse,
} from "@/lib/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8080",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const apiKey = process.env.NEXT_PUBLIC_KB_API_KEY;
  if (apiKey) {
    config.headers["x-api-key"] = apiKey;
  }
  return config;
});

export async function getFolders() {
  const { data } = await api.get<Folder[]>("/folders");
  return data;
}

export async function createFolder(folder_name: string) {
  const { data } = await api.post<Folder>("/folders", { folder_name });
  return data;
}

export async function getFolder(folderName: string) {
  const { data } = await api.get<FolderDetail>(`/folders/${encodeURIComponent(folderName)}`);
  return data;
}

export async function deleteFolder(folderName: string) {
  const { data } = await api.delete(`/folders/${encodeURIComponent(folderName)}`);
  return data;
}

export async function uploadFiles(
  folderName: string,
  files: File[],
  onProgress?: (percent: number) => void,
) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const { data } = await api.post<UploadResponse>(`/folders/${encodeURIComponent(folderName)}/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (event) => {
      if (!event.total) {
        return;
      }
      const percent = Math.round((event.loaded * 100) / event.total);
      onProgress?.(percent);
    },
  });
  return data;
}

export async function getDocuments(folderName: string) {
  const { data } = await api.get<FolderDetail["documents"]>(`/folders/${encodeURIComponent(folderName)}/documents`);
  return data;
}

export async function deleteDocument(folderName: string, documentId: string) {
  const { data } = await api.delete(`/folders/${encodeURIComponent(folderName)}/documents/${documentId}`);
  return data;
}

export async function indexFolder(folderName: string) {
  const { data } = await api.post<IndexStartResponse>(`/folders/${encodeURIComponent(folderName)}/index`);
  return data;
}

export async function getIndexStatus(folderName: string) {
  const { data } = await api.get<IndexStatusResponse>(`/folders/${encodeURIComponent(folderName)}/index/status`);
  return data;
}

export async function retrieveChunks(payload: { folder_name: string; query: string; top_k?: number }) {
  const { data } = await api.post<RetrievalResponse>("/retrieve", payload);
  return data;
}

export async function getSettings() {
  const { data } = await api.get<SettingsResponse>("/settings");
  return data;
}

export async function updateSettings(payload: {
  default_top_k: number;
  chunk_size: number;
  chunk_overlap: number;
}) {
  const { data } = await api.patch<SettingsResponse>("/settings", payload);
  return data;
}

export function getApiErrorMessage(error: unknown) {
  if (error instanceof AxiosError) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong.";
}
