"use client";

import { useEffect, useRef, useState } from "react";
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
  const [awaitingJob, setAwaitingJob] = useState(false);

  const statusQuery = useQuery({
    queryKey: ["index-status", folderName],
    queryFn: () => getIndexStatus(folderName),
    refetchInterval: (query) => {
      const latestJob = query.state.data?.latest_job;
      const currentFolderStatus = query.state.data?.status ?? folderStatus;
      const shouldPoll =
        awaitingJob ||
        latestJob?.status === "pending" ||
        latestJob?.status === "running" ||
        currentFolderStatus === "indexing";
      return shouldPoll ? 1500 : false;
    },
  });

  const mutation = useMutation({
    mutationFn: () => indexFolder(folderName),
    onMutate: () => {
      setAwaitingJob(true);
    },
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
    onError: (error: unknown) => {
      setAwaitingJob(false);
      pushToast({ tone: "error", title: "Indexing failed", description: getApiErrorMessage(error) });
    },
  });

  useEffect(() => {
    const latestJob = statusQuery.data?.latest_job;
    const currentFolderStatus = statusQuery.data?.status ?? folderStatus;
    if (!latestJob) {
      if (currentFolderStatus !== "indexing") {
        setAwaitingJob(false);
      }
      return;
    }
    if (latestJob.status === "pending" || latestJob.status === "running") {
      setAwaitingJob(false);
    }
    const previousStatus = lastJobStatusRef.current;
    if (latestJob.status !== previousStatus) {
      lastJobStatusRef.current = latestJob.status;
      if (latestJob.status === "completed") {
        setAwaitingJob(false);
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
        setAwaitingJob(false);
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
  }, [folderName, folderStatus, pushToast, queryClient, statusQuery.data]);

  const actionLabel =
    folderStatus === "needs_reindex" || folderStatus === "indexed" ? "Re-index folder" : "Index folder";
  const latestJob = statusQuery.data?.latest_job;
  const progressPercent = latestJob?.progress_percent ?? 0;
  const liveFolderStatus = statusQuery.data?.status ?? folderStatus;
  const isRunning = latestJob?.status === "running";
  const isQueued = latestJob?.status === "pending" || awaitingJob;
  const showProgress = isRunning || isQueued || liveFolderStatus === "indexing";
  const progressLabel = latestJob?.status_message ?? (isQueued ? "Queueing indexing job" : "Indexing documents");
  const progressValue = latestJob ? progressPercent : isQueued ? 8 : 0;

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
        <StatusBadge status={liveFolderStatus} />
        {latestJob ? (
          <p className="text-sm text-muted">
            Latest job: {latestJob.status} · files {latestJob.processed_files}/{latestJob.total_files} · chunks {latestJob.total_chunks}
          </p>
        ) : isQueued ? (
          <p className="text-sm text-muted">Indexing request accepted. VecSeek is preparing the background job now.</p>
        ) : (
          <p className="text-sm text-muted">No indexing job has run yet.</p>
        )}
      </div>

      {showProgress ? (
        <div className="mt-5 rounded-[24px] border border-black/[0.06] bg-card px-4 py-4 dark:border-white/10">
          <div className="mb-2 flex items-center justify-between text-sm text-muted">
            <span>{progressLabel}</span>
            <span>{progressValue}%</span>
          </div>
          <Progress value={progressValue} />
          <p className="mt-2 text-xs text-muted">
            Phase: {latestJob?.phase ?? (isQueued ? "queued" : "running")} · files {latestJob?.processed_files ?? 0}/{latestJob?.total_files ?? 0}
          </p>
        </div>
      ) : null}

      {latestJob?.error_message ? <p className="mt-4 text-sm text-danger">{latestJob.error_message}</p> : null}

      <div className="mt-6 flex justify-end">
        <Button disabled={mutation.isPending || isRunning || isQueued} onClick={() => mutation.mutate()}>
          {mutation.isPending || isRunning || isQueued ? (
            <>
              <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />
              {isQueued ? "Queueing..." : "Processing..."}
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
