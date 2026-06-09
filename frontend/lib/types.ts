export type FolderStatus =
  | "empty"
  | "has_files"
  | "indexing"
  | "indexed"
  | "needs_reindex"
  | "failed";

export type DocumentStatus = "uploaded" | "indexed" | "failed" | "deleted";
export type EvalProvider = "ollama" | "openai";
export type EvalCaseType = "retrieval" | "answer" | "redteam" | "all";
export type EvalRunType = "full" | "retrieval" | "answer" | "redteam";
export type EvalRunStatus = "pending" | "running" | "completed" | "failed";
export type EvalTriggerType = "manual" | "auto";

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
    chunk_id?: string;
    source_file: string;
    file_type: string;
    content_type: string;
    page_number: number;
    table_index: number;
    row_index: number;
    chunk_index: number;
    citation?: string;
    explanation?: string;
    dense_score?: number;
    keyword_score?: number;
    embedding_model?: string;
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
  vector_candidate_limit: number;
  retrieval_concurrency_limit: number;
  indexing_worker_concurrency: number;
  hybrid_retrieval_enabled: boolean;
  reranker_enabled: boolean;
}

export interface EvalProfile {
  id: string;
  folder_id: string;
  provider: EvalProvider;
  model_name: string;
  auto_run_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface EvalCase {
  id: string;
  folder_id: string;
  name: string;
  question: string;
  reference_answer?: string | null;
  expected_answer_points: string[];
  expected_source_files: string[];
  tags: string[];
  case_type: EvalCaseType;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface EvalRunItem {
  id: string;
  run_id: string;
  case_id?: string | null;
  eval_type: EvalRunType;
  score?: number | null;
  passed: boolean;
  details: Record<string, unknown>;
  created_at: string;
}

export interface EvalRunArtifact {
  id: string;
  run_id: string;
  artifact_type: string;
  name: string;
  content: string;
  created_at: string;
}

export interface EvalRunSummary {
  id: string;
  folder_id: string;
  profile_id?: string | null;
  previous_run_id?: string | null;
  run_type: EvalRunType;
  trigger_type: EvalTriggerType;
  status: EvalRunStatus;
  provider: EvalProvider;
  model_name: string;
  summary_metrics: Record<string, unknown>;
  error_message?: string | null;
  started_at: string;
  completed_at?: string | null;
}

export interface EvalRunDetail extends EvalRunSummary {
  items: EvalRunItem[];
  artifacts: EvalRunArtifact[];
}

export interface OllamaModel {
  name: string;
  size?: number | null;
  modified_at?: string | null;
}
