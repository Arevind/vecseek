"use client";

import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FileUp, UploadCloud } from "lucide-react";

import { useToast } from "@/components/toast-provider";
import { Card } from "@/components/ui/card";
import { HoverHint } from "@/components/ui/hover-hint";
import { Progress } from "@/components/ui/progress";
import { getApiErrorMessage, uploadFiles } from "@/lib/api";

export function UploadPanel({ folderName }: { folderName: string }) {
  const queryClient = useQueryClient();
  const { pushToast } = useToast();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [messages, setMessages] = useState<string[]>([]);
  const [uploadProgress, setUploadProgress] = useState(0);

  const mutation = useMutation({
    mutationFn: (files: File[]) => uploadFiles(folderName, files, setUploadProgress),
    onSuccess: async (data) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["folder", folderName] }),
        queryClient.invalidateQueries({ queryKey: ["folders"] }),
      ]);
      setMessages(data.results.map((item) => `${item.file_name}: ${item.message}`));
      data.results.forEach((item) => {
        pushToast({
          tone: item.status === "duplicate" ? "info" : item.status === "uploaded" ? "success" : "error",
          title:
            item.status === "duplicate"
              ? "Duplicate detected"
              : item.status === "uploaded"
                ? "Files uploaded"
                : "Upload issue",
          description: `${item.file_name}: ${item.message}`,
        });
      });
      if (inputRef.current) {
        inputRef.current.value = "";
      }
      setUploadProgress(0);
    },
    onError: (error: unknown) => {
      const message = getApiErrorMessage(error);
      setMessages([message]);
      pushToast({ tone: "error", title: "Upload failed", description: message });
      setUploadProgress(0);
    },
  });

  function handleSelectedFiles(files: File[]) {
    if (!files.length || mutation.isPending) {
      return;
    }
    setMessages([]);
    setUploadProgress(0);
    mutation.mutate(files);
  }

  return (
    <Card className="p-5 sm:p-6">
      <div className="flex items-start justify-between gap-4">
        <HoverHint hint="Uploads are stored under this folder and checked for duplicates using the file hash before indexing.">
          <div>
            <p className="section-label">Upload</p>
            <p className="mt-3 font-display text-[2rem] leading-none text-text">Add source files</p>
            <p className="mt-3 text-sm leading-6 text-muted">PDF, DOCX, and TXT files are supported. Upload begins right after selection.</p>
          </div>
        </HoverHint>
        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-card-secondary text-accent">
          <UploadCloud className="h-5 w-5" />
        </div>
      </div>

      <label className="mt-6 flex cursor-pointer flex-col items-center justify-center rounded-[28px] border border-dashed border-black/10 bg-card-secondary/35 p-8 text-center transition hover:border-accent/30 hover:bg-card-secondary/55 dark:border-white/10">
        <div className="flex h-14 w-14 items-center justify-center rounded-[20px] bg-card text-accent shadow-glow">
          <FileUp className="h-6 w-6" />
        </div>
        <span className="mt-4 text-base font-semibold text-text">Select one or more files</span>
        <span className="mt-2 text-sm leading-6 text-muted">Supported formats: .pdf, .docx, .txt</span>
        <input
          ref={inputRef}
          className="hidden"
          multiple
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={(event) => handleSelectedFiles(Array.from(event.target.files ?? []))}
        />
      </label>

      {mutation.isPending ? (
        <div className="mt-5 rounded-[24px] border border-black/[0.06] bg-card px-4 py-4 dark:border-white/10">
          <div className="mb-2 flex items-center justify-between text-sm text-muted">
            <span>Uploading selected files</span>
            <span>{uploadProgress}%</span>
          </div>
          <Progress value={uploadProgress} />
        </div>
      ) : null}

      {messages.length ? (
        <div className="mt-5 space-y-2 rounded-[24px] border border-black/[0.06] bg-card px-4 py-4 text-sm text-muted dark:border-white/10">
          {messages.map((message) => (
            <p key={message}>{message}</p>
          ))}
        </div>
      ) : null}
    </Card>
  );
}
