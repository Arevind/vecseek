export type FolderStatus =
  | "empty"
  | "has_files"
  | "indexing"
  | "indexed"
  | "needs_reindex"
  | "failed";

export type DocumentStatus = "uploaded" | "indexed" | "failed" | "deleted";

export interface Folder {
  id: string;
  display_name: string;
  slug: string;
  collection_name: string;
  status: FolderStatus;
  document_count: number;
  indexed_chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentItem {
  id: string;
  file_name: string;
  stored_file_name: string;
  file_type: string;
  file_hash: string;
  status: DocumentStatus;
  uploaded_at: string;
  indexed_at: string | null;
}

export interface FolderDetail extends Folder {
  documents: DocumentItem[];
}

export interface UploadResult {
  status: string;
  message: string;
  file_name: string;
  document_id?: string | null;
}

export interface UploadResponse {
  folder_name: string;
  results: UploadResult[];
}

export interface IndexJob {
  id: string;
  status: "pending" | "running" | "completed" | "failed";
  total_files: number;
  processed_files: number;
  total_chunks: number;
  error_message?: string | null;
  started_at: string;
  completed_at?: string | null;
  phase?: string | null;
  progress_percent?: number | null;
  status_message?: string | null;
}

export interface IndexStartResponse {
  message: string;
  folder_name: string;
  collection_name: string;
  total_files: number;
  total_chunks: number;
  status: string;
  job_id?: string | null;
}

export interface IndexStatusResponse {
  folder_name: string;
  status: FolderStatus;
  latest_job?: IndexJob | null;
}

export interface RetrievalItem {
  content: string;
  score: number;
  metadata: {
    source_file: string;
    file_type: string;
    content_type: string;
    page_number: number;
    table_index: number;
    row_index: number;
    chunk_index: number;
  } & Record<string, string | number>;
}

export interface RetrievalResponse {
  folder_name: string;
  query: string;
  top_k: number;
  results: RetrievalItem[];
}

export interface SettingsResponse {
  default_top_k: number;
  max_top_k: number;
  chunk_size: number;
  chunk_overlap: number;
}
