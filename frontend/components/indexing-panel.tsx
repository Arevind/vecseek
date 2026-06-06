"use client";

import { useEffect, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { LoaderCircle, RefreshCw, Sparkles } from "lucide-react";

import { useToast } from "@/components/toast-provider";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { HoverHint } from "@/components/ui/hover-hint";
import { Progress } from "@/components/ui/progress";
import { getApiErrorMessage, getIndexStatus, indexFolder } from "@/lib/api";
import type { FolderStatus } from "@/lib/types";

export function IndexingPanel({ folderName, folderStatus }: { folderName: string; folderStatus: FolderStatus }) {
  const queryClient = useQueryClient();
  const { pushToast } = useToast();
  const lastJobStatusRef = useRef<string | null>(null);
  const statusQuery = useQuery({
    queryKey: ["index-status", folderName],
    queryFn: () => getIndexStatus(folderName),
    refetchInterval: (query) => {
      const latestJob = query.state.data?.latest_job;
      return latestJob?.status === "running" ? 1500 : folderStatus === "indexing" ? 1500 : false;
    },
  });

  const mutation = useMutation({
    mutationFn: () => indexFolder(folderName),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["folder", folderName] }),
        queryClient.invalidateQueries({ queryKey: ["folders"] }),
        queryClient.invalidateQueries({ queryKey: ["index-status", folderName] }),
      ]);
      pushToast({
        tone: "info",
        title: folderStatus === "needs_reindex" ? "Re-index started" : "Indexing started",
        description: "The folder is indexing in the background now.",
      });
    },
    onError: (error: unknown) =>
      pushToast({ tone: "error", title: "Indexing failed", description: getApiErrorMessage(error) }),
  });

  useEffect(() => {
    const latestJob = statusQuery.data?.latest_job;
    if (!latestJob) {
      return;
    }
    const previousStatus = lastJobStatusRef.current;
    if (latestJob.status !== previousStatus) {
      lastJobStatusRef.current = latestJob.status;
      if (latestJob.status === "completed") {
        pushToast({
          tone: "success",
          title: folderStatus === "needs_reindex" ? "Folder re-indexed" : "Folder indexed",
          description: "The retrieval collection was rebuilt successfully.",
        });
        void Promise.all([
          queryClient.invalidateQueries({ queryKey: ["folder", folderName] }),
          queryClient.invalidateQueries({ queryKey: ["folders"] }),
        ]);
      }
      if (latestJob.status === "failed") {
        pushToast({
          tone: "error",
          title: "Indexing failed",
          description: latestJob.error_message ?? "The indexing job failed.",
        });
        void Promise.all([
          queryClient.invalidateQueries({ queryKey: ["folder", folderName] }),
          queryClient.invalidateQueries({ queryKey: ["folders"] }),
        ]);
      }
    }
  }, [folderName, folderStatus, pushToast, queryClient, statusQuery.data?.latest_job]);

  const actionLabel =
    folderStatus === "needs_reindex" || folderStatus === "indexed" ? "Re-index folder" : "Index folder";
  const latestJob = statusQuery.data?.latest_job;
  const progressPercent = latestJob?.progress_percent ?? 0;
  const isRunning = latestJob?.status === "running";

  return (
    <Card className="p-5 sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <HoverHint hint="Indexing converts processed document blocks into embeddings and stores them in the folder's Qdrant collection.">
          <div>
            <p className="section-label">Indexing</p>
            <p className="mt-3 font-display text-[2rem] leading-none text-text">Build retrieval state</p>
            <p className="mt-3 text-sm leading-6 text-muted">Use this after uploads, edits, or deletions so the live search results stay current.</p>
          </div>
        </HoverHint>
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-card-secondary text-accent2">
          <Sparkles className="h-5 w-5" />
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <StatusBadge status={folderStatus} />
        {latestJob ? (
          <p className="text-sm text-muted">
            Latest job: {latestJob.status} · files {latestJob.processed_files}/{latestJob.total_files} · chunks {latestJob.total_chunks}
          </p>
        ) : (
          <p className="text-sm text-muted">No indexing job has run yet.</p>
        )}
      </div>

      {isRunning ? (
        <div className="mt-5 rounded-[24px] border border-black/[0.06] bg-card px-4 py-4 dark:border-white/10">
          <div className="mb-2 flex items-center justify-between text-sm text-muted">
            <span>{latestJob?.status_message ?? "Indexing documents"}</span>
            <span>{progressPercent}%</span>
          </div>
          <Progress value={progressPercent} />
          <p className="mt-2 text-xs text-muted">
            Phase: {latestJob?.phase ?? "running"} · files {latestJob?.processed_files ?? 0}/{latestJob?.total_files ?? 0}
          </p>
        </div>
      ) : null}

      {latestJob?.error_message ? <p className="mt-4 text-sm text-danger">{latestJob.error_message}</p> : null}

      <div className="mt-6 flex justify-end">
        <Button disabled={mutation.isPending || isRunning} onClick={() => mutation.mutate()}>
          {mutation.isPending || isRunning ? (
            <>
              <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </>
          ) : folderStatus === "needs_reindex" ? (
            <>
              <RefreshCw className="mr-2 h-4 w-4" />
              {actionLabel}
            </>
          ) : (
            actionLabel
          )}
        </Button>
      </div>
    </Card>
  );
}
