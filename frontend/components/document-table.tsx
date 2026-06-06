"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FileText, Trash2 } from "lucide-react";

import { useToast } from "@/components/toast-provider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { HoverHint } from "@/components/ui/hover-hint";
import { deleteDocument, getApiErrorMessage } from "@/lib/api";
import type { DocumentItem } from "@/lib/types";

export function DocumentTable({
  folderName,
  documents,
}: {
  folderName: string;
  documents: DocumentItem[];
}) {
  const queryClient = useQueryClient();
  const { pushToast } = useToast();
  const mutation = useMutation({
    mutationFn: (documentId: string) => deleteDocument(folderName, documentId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["folder", folderName] }),
        queryClient.invalidateQueries({ queryKey: ["folders"] }),
      ]);
      pushToast({
        tone: "success",
        title: "Document deleted",
        description: "The folder now requires re-indexing to remove stale chunks.",
      });
    },
    onError: (error: unknown) =>
      pushToast({ tone: "error", title: "Delete failed", description: getApiErrorMessage(error) }),
  });

  return (
    <Card className="overflow-hidden p-5 sm:p-6">
      <div className="flex items-center justify-between gap-4 border-b border-black/[0.06] pb-4 dark:border-white/10">
        <HoverHint hint="This list shows everything currently stored inside the selected folder before indexing or re-indexing.">
          <div>
            <p className="section-label">Files</p>
            <p className="mt-2 text-sm leading-6 text-muted">Delete any file here if you want the next index run to exclude it.</p>
          </div>
        </HoverHint>
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-card-secondary text-accent">
          <FileText className="h-4 w-4" />
        </div>
      </div>

      {documents.length ? (
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full">
            <thead className="text-left text-[11px] uppercase tracking-[0.22em] text-muted">
              <tr className="border-b border-black/[0.06] dark:border-white/10">
                <th className="px-1 py-3 font-medium">File</th>
                <th className="px-1 py-3 font-medium">Type</th>
                <th className="px-1 py-3 font-medium">Status</th>
                <th className="px-1 py-3 font-medium">Uploaded</th>
                <th className="px-1 py-3 text-right font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((document) => (
                <tr key={document.id} className="border-b border-black/[0.06] last:border-b-0 dark:border-white/[0.08]">
                  <td className="px-1 py-4 text-sm text-text">{document.file_name}</td>
                  <td className="px-1 py-4 text-sm uppercase text-muted">{document.file_type}</td>
                  <td className="px-1 py-4 text-sm text-text">{document.status}</td>
                  <td className="px-1 py-4 text-sm text-muted">{new Date(document.uploaded_at).toLocaleString()}</td>
                  <td className="px-1 py-4 text-right">
                    <Button variant="danger" onClick={() => mutation.mutate(document.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="mt-4 rounded-[24px] border border-dashed border-black/[0.08] bg-card-secondary/35 px-4 py-10 text-sm text-muted dark:border-white/10">
          No files uploaded yet.
        </div>
      )}
    </Card>
  );
}
