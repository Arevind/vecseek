"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useToast } from "@/components/toast-provider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { HoverHint } from "@/components/ui/hover-hint";
import { Input } from "@/components/ui/input";
import { getApiErrorMessage, getSettings, updateSettings } from "@/lib/api";

export function SettingsPanel() {
  const queryClient = useQueryClient();
  const { pushToast } = useToast();
  const { data } = useQuery({ queryKey: ["settings"], queryFn: getSettings });
  const [defaultTopK, setDefaultTopK] = useState("5");
  const [chunkSize, setChunkSize] = useState("1400");
  const [chunkOverlap, setChunkOverlap] = useState("250");
  const [vectorCandidateLimit, setVectorCandidateLimit] = useState("32");
  const [retrievalConcurrencyLimit, setRetrievalConcurrencyLimit] = useState("12");
  const [indexingWorkerConcurrency, setIndexingWorkerConcurrency] = useState("2");
  const [hybridEnabled, setHybridEnabled] = useState(true);
  const [rerankerEnabled, setRerankerEnabled] = useState(true);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (data) {
      setDefaultTopK(String(data.default_top_k));
      setChunkSize(String(data.chunk_size));
      setChunkOverlap(String(data.chunk_overlap));
      setVectorCandidateLimit(String(data.vector_candidate_limit));
      setRetrievalConcurrencyLimit(String(data.retrieval_concurrency_limit));
      setIndexingWorkerConcurrency(String(data.indexing_worker_concurrency));
      setHybridEnabled(data.hybrid_retrieval_enabled);
      setRerankerEnabled(data.reranker_enabled);
    }
  }, [data]);

  const mutation = useMutation({
    mutationFn: updateSettings,
    onSuccess: async () => {
      setMessage("Saved.");
      await queryClient.invalidateQueries({ queryKey: ["settings"] });
      pushToast({
        tone: "success",
        title: "Settings saved",
        description: "Retrieval and chunking defaults were updated.",
      });
    },
    onError: (error: unknown) => {
      const nextMessage = getApiErrorMessage(error);
      setMessage(nextMessage);
      pushToast({ tone: "error", title: "Settings update failed", description: nextMessage });
    },
  });

  if (!data) {
    return <Card className="p-6 text-sm text-muted">Loading settings...</Card>;
  }

  return (
    <Card className="p-5 sm:p-6">
      <div className="grid gap-5 xl:grid-cols-[minmax(0,0.9fr),1.1fr]">
        <div>
          <HoverHint hint="These defaults shape retrieval depth and chunk structure for every folder you index after saving.">
            <div>
              <p className="section-label">Settings</p>
              <p className="mt-3 font-display text-[2.15rem] leading-none text-text">Tune indexing defaults</p>
              <p className="mt-3 text-sm leading-6 text-muted">
                Keep retrieval shallow and precise, or raise chunk size for more context-heavy document responses.
              </p>
            </div>
          </HoverHint>
        </div>

        <div className="rounded-[28px] border border-black/[0.06] bg-card-secondary/35 p-5 dark:border-white/10">
          <div className="grid gap-5 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-text">Default top K</label>
              <Input value={defaultTopK} onChange={(event) => setDefaultTopK(event.target.value)} inputMode="numeric" />
              <p className="mt-2 text-xs uppercase tracking-[0.22em] text-muted">Maximum {data.max_top_k}</p>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-text">Chunk size</label>
              <Input value={chunkSize} onChange={(event) => setChunkSize(event.target.value)} inputMode="numeric" />
              <p className="mt-2 text-xs text-muted">Controls how much text is grouped into one retrievable unit.</p>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-text">Chunk overlap</label>
              <Input value={chunkOverlap} onChange={(event) => setChunkOverlap(event.target.value)} inputMode="numeric" />
              <p className="mt-2 text-xs text-muted">Keep overlap smaller than chunk size to avoid invalid settings.</p>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-text">Vector candidate limit</label>
              <Input value={vectorCandidateLimit} onChange={(event) => setVectorCandidateLimit(event.target.value)} inputMode="numeric" />
              <p className="mt-2 text-xs text-muted">How many dense matches VecSeek inspects before merge and rerank.</p>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-text">Retrieval concurrency</label>
              <Input value={retrievalConcurrencyLimit} onChange={(event) => setRetrievalConcurrencyLimit(event.target.value)} inputMode="numeric" />
              <p className="mt-2 text-xs text-muted">Caps simultaneous RAG calls before short backpressure is applied.</p>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-text">Indexing worker concurrency</label>
              <Input value={indexingWorkerConcurrency} onChange={(event) => setIndexingWorkerConcurrency(event.target.value)} inputMode="numeric" />
              <p className="mt-2 text-xs text-muted">Limits how many folder indexing jobs can run at the same time.</p>
            </div>

            <label className="flex items-center justify-between rounded-[22px] border border-black/[0.06] bg-card px-4 py-3 text-sm text-text dark:border-white/10">
              <span>Hybrid retrieval</span>
              <input type="checkbox" checked={hybridEnabled} onChange={(event) => setHybridEnabled(event.target.checked)} />
            </label>

            <label className="flex items-center justify-between rounded-[22px] border border-black/[0.06] bg-card px-4 py-3 text-sm text-text dark:border-white/10">
              <span>Reranker</span>
              <input type="checkbox" checked={rerankerEnabled} onChange={(event) => setRerankerEnabled(event.target.checked)} />
            </label>
          </div>

          {message ? <p className="mt-5 text-sm text-muted">{message}</p> : null}

          <div className="mt-6 flex justify-end">
            <Button
              disabled={mutation.isPending}
              onClick={() =>
                mutation.mutate({
                  default_top_k: Number(defaultTopK),
                  chunk_size: Number(chunkSize),
                  chunk_overlap: Number(chunkOverlap),
                  vector_candidate_limit: Number(vectorCandidateLimit),
                  retrieval_concurrency_limit: Number(retrievalConcurrencyLimit),
                  indexing_worker_concurrency: Number(indexingWorkerConcurrency),
                  hybrid_retrieval_enabled: hybridEnabled,
                  reranker_enabled: rerankerEnabled,
                })
              }
            >
              {mutation.isPending ? "Saving..." : "Save changes"}
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
}
