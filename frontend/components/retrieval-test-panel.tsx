"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Search, Sparkles } from "lucide-react";

import { useToast } from "@/components/toast-provider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { HoverHint } from "@/components/ui/hover-hint";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { getApiErrorMessage, getFolders, getSettings, retrieveChunks } from "@/lib/api";

export function RetrievalTestPanel({ initialFolderName }: { initialFolderName?: string }) {
  const foldersQuery = useQuery({ queryKey: ["folders"], queryFn: getFolders });
  const settingsQuery = useQuery({ queryKey: ["settings"], queryFn: getSettings });
  const { pushToast } = useToast();

  const [folderName, setFolderName] = useState(initialFolderName ?? "");
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState("5");

  useEffect(() => {
    if (!folderName && initialFolderName) {
      setFolderName(initialFolderName);
    }
  }, [folderName, initialFolderName]);

  useEffect(() => {
    if (settingsQuery.data) {
      setTopK(String(settingsQuery.data.default_top_k));
    }
  }, [settingsQuery.data]);

  const mutation = useMutation({
    mutationFn: retrieveChunks,
    onSuccess: () => {
      pushToast({ tone: "success", title: "Retrieval completed", description: "Relevant chunks were returned successfully." });
    },
    onError: (error: unknown) =>
      pushToast({ tone: "error", title: "Retrieval failed", description: getApiErrorMessage(error) }),
  });

  return (
    <Card className="p-5 sm:p-6" id="retrieval-lab">
      <div className="grid gap-5 xl:grid-cols-[minmax(0,0.95fr),1.05fr]">
        <div>
          <HoverHint hint="This is the same public retrieval path your external clients can use when testing search quality.">
            <div>
              <p className="section-label">Retrieval</p>
              <p className="mt-3 font-display text-[2.15rem] leading-none text-text">Live result check</p>
              <p className="mt-3 text-sm leading-6 text-muted">
                Pick a folder, ask a real question, and review the exact chunk text and metadata the API returns.
              </p>
            </div>
          </HoverHint>

          <div className="mt-6 grid gap-4">
            <div>
              <p className="mb-2 text-sm font-medium text-text">Folder</p>
              <Select
                value={folderName}
                onValueChange={setFolderName}
                placeholder="Select a folder"
                items={(foldersQuery.data ?? []).map((folder) => ({
                  label: folder.display_name,
                  value: folder.display_name,
                }))}
              />
            </div>

            <div>
              <p className="mb-2 text-sm font-medium text-text">Top K</p>
              <Input value={topK} onChange={(event) => setTopK(event.target.value)} inputMode="numeric" />
            </div>

            <div>
              <p className="mb-2 text-sm font-medium text-text">Question</p>
              <Textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="What documents are required for Aadhaar biometric update?"
              />
            </div>

            <div className="flex justify-end">
              <Button
                disabled={mutation.isPending}
                onClick={() => {
                  if (!folderName.trim() || !query.trim()) {
                    pushToast({
                      tone: "info",
                      title: "Query required",
                      description: "Choose a folder and enter a non-empty question before searching.",
                    });
                    return;
                  }
                  mutation.mutate({
                    folder_name: folderName,
                    query,
                    top_k: Number(topK),
                  });
                }}
              >
                <Search className="mr-2 h-4 w-4" />
                {mutation.isPending ? "Searching..." : "Search"}
              </Button>
            </div>
          </div>
        </div>

        <div className="rounded-[28px] border border-black/[0.06] bg-card-secondary/35 p-4 dark:border-white/10">
          <div className="flex items-center justify-between gap-3 border-b border-black/[0.06] pb-4 dark:border-white/10">
            <HoverHint hint="Returned rows include the original chunk text plus lineage fields like source file, page, table, and row.">
              <div>
                <p className="section-label">Results</p>
                <p className="mt-2 text-sm leading-6 text-muted">Metadata stays attached so answers remain traceable.</p>
              </div>
            </HoverHint>
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-card text-accent">
              <Sparkles className="h-4 w-4" />
            </div>
          </div>

          <div className="mt-4 space-y-3">
            {mutation.data ? (
              mutation.data.results.length ? (
                mutation.data.results.map((result, index) => (
                  <div key={`${result.metadata.source_file}-${index}`} className="rounded-[24px] border border-black/[0.06] bg-card p-4 dark:border-white/10">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-accent/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent">
                        Score {result.score.toFixed(3)}
                      </span>
                      <span className="rounded-full bg-card-secondary px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-muted">
                        {result.metadata.source_file}
                      </span>
                      <span className="rounded-full bg-card-secondary px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-muted">
                        {result.metadata.content_type}
                      </span>
                    </div>
                    <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-text">{result.content}</p>
                    {result.metadata.explanation ? (
                      <p className="mt-3 text-sm leading-6 text-muted">{String(result.metadata.explanation)}</p>
                    ) : null}
                    <p className="mt-4 text-[11px] uppercase tracking-[0.22em] text-muted">
                      Page {result.metadata.page_number} · Table {result.metadata.table_index} · Row {result.metadata.row_index} · Chunk {result.metadata.chunk_index}
                    </p>
                    <p className="mt-2 text-[11px] uppercase tracking-[0.18em] text-muted">
                      Dense {Number(result.metadata.dense_score ?? 0).toFixed(3)} · Keyword {Number(result.metadata.keyword_score ?? 0).toFixed(3)}
                    </p>
                  </div>
                ))
              ) : (
                <div className="rounded-[24px] border border-dashed border-black/[0.08] bg-card px-4 py-10 text-sm text-muted dark:border-white/10">
                  No retrieval results returned.
                </div>
              )
            ) : (
              <div className="rounded-[24px] border border-dashed border-black/[0.08] bg-card px-4 py-10 text-sm text-muted dark:border-white/10">
                Run a query and the matched chunks will appear here.
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
