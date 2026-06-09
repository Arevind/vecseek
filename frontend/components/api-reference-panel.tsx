"use client";

import { Braces, Globe2 } from "lucide-react";

import { Card } from "@/components/ui/card";
import { HoverHint } from "@/components/ui/hover-hint";

const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8080";

const endpointGroups = [
  {
    title: "Health",
    description: "Use this to verify the backend is reachable before trying uploads or retrieval.",
    method: "GET",
    path: "/health",
    body: null,
  },
  {
    title: "Create folder",
    description: "Create a new document dock that will hold uploads and a dedicated vector collection.",
    method: "POST",
    path: "/folders",
    body: `{
  "folder_name": "Pay10 Support Docs"
}`,
  },
  {
    title: "Upload files",
    description: "Send one or more PDF, DOCX, or TXT files into a folder using multipart form data.",
    method: "POST",
    path: "/folders/Pay10%20Support%20Docs/upload",
    body: "multipart/form-data with one or more `files` fields",
  },
  {
    title: "Index folder",
    description: "Start background indexing so the uploaded documents become retrievable.",
    method: "POST",
    path: "/folders/Pay10%20Support%20Docs/index",
    body: null,
  },
  {
    title: "Retrieve",
    description: "Query one folder and receive the best-matching chunks with metadata lineage.",
    method: "POST",
    path: "/retrieve",
    body: `{
  "folder_name": "Pay10 Support Docs",
  "query": "What is Pay10?",
  "top_k": 5
}`,
  },
  {
    title: "Eval profile",
    description: "Read or update the folder-specific evaluation provider, model choice, and auto-run toggle.",
    method: "PATCH",
    path: "/folders/Pay10%20Support%20Docs/evaluations/profile",
    body: `{
  "provider": "ollama",
  "model_name": "llama3.1",
  "auto_run_enabled": true
}`,
  },
  {
    title: "Create eval case",
    description: "Add a reusable gold test case for retrieval, answer quality, red-team prompts, or the full suite.",
    method: "POST",
    path: "/folders/Pay10%20Support%20Docs/evaluations/cases",
    body: `{
  "name": "Pay10 definition",
  "question": "What is Pay10?",
  "reference_answer": "Pay10 is a payments platform for businesses.",
  "expected_answer_points": ["payment gateway", "businesses"],
  "expected_source_files": ["payments-faq.txt"],
  "tags": ["faq"],
  "case_type": "all",
  "enabled": true
}`,
  },
  {
    title: "Start eval run",
    description: "Run retrieval, answer, red-team, or the full evaluation suite for the selected folder.",
    method: "POST",
    path: "/folders/Pay10%20Support%20Docs/evaluations/runs",
    body: `{
  "run_type": "full",
  "provider": "openai",
  "model_name": "gpt-4.1-mini",
  "openai_api_key": "sk-..."
}`,
  },
  {
    title: "Settings",
    description: "Read or update the retrieval defaults that control top K and chunking behavior.",
    method: "PATCH",
    path: "/settings",
    body: `{
  "default_top_k": 5,
  "chunk_size": 1400,
  "chunk_overlap": 250
}`,
  },
];

export function ApiReferencePanel() {
  return (
    <Card className="p-5 sm:p-6">
      <div className="grid gap-5 xl:grid-cols-[minmax(0,0.88fr),1.12fr]">
        <div>
          <HoverHint hint="This page mirrors the same routes the interface uses, so external integrations can start from real working payloads.">
            <div>
              <p className="section-label">API Reference</p>
              <p className="mt-3 font-display text-[2.15rem] leading-none text-text">Direct access, quietly mapped</p>
              <p className="mt-3 text-sm leading-6 text-muted">
                Start from the base URL below, then follow the minimal request shapes for folders, uploads, indexing, and retrieval.
              </p>
            </div>
          </HoverHint>

          <div className="mt-6 rounded-[26px] border border-black/[0.06] bg-card px-5 py-5 dark:border-white/10">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-card-secondary text-accent">
                <Globe2 className="h-4 w-4" />
              </div>
              <div>
                <p className="section-label">Base URL</p>
                <p className="mt-2 break-all text-sm text-text">{baseUrl}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          {endpointGroups.map((endpoint) => (
            <div key={`${endpoint.method}-${endpoint.path}`} className="rounded-[28px] border border-black/[0.06] bg-card p-5 dark:border-white/10">
              <div className="flex flex-wrap items-center gap-3">
                <span className="rounded-full bg-card-secondary px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent2 dark:bg-[rgb(var(--accent)/0.18)] dark:text-[rgb(var(--accent2))]">
                  {endpoint.method}
                </span>
                <HoverHint hint={endpoint.description}>
                  <p className="text-sm font-semibold text-text">{endpoint.title}</p>
                </HoverHint>
              </div>
              <div className="mt-3 flex items-start gap-3 rounded-[22px] bg-card-secondary/55 px-4 py-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-2xl bg-card text-accent">
                  <Braces className="h-4 w-4" />
                </div>
                <code className="block text-sm text-text">{endpoint.path}</code>
              </div>
              {endpoint.body ? (
                <pre className="mt-4 overflow-x-auto rounded-[22px] bg-[#1e2329] px-4 py-4 text-xs leading-6 text-slate-100">
                  <code>{endpoint.body}</code>
                </pre>
              ) : (
                <p className="mt-4 text-sm text-muted">No request body required.</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
