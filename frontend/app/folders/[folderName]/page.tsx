"use client";

import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import { FileStack } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { DocumentTable } from "@/components/document-table";
import { IndexingPanel } from "@/components/indexing-panel";
import { RetrievalTestPanel } from "@/components/retrieval-test-panel";
import { StatusBadge } from "@/components/status-badge";
import { UploadPanel } from "@/components/upload-panel";
import { Card } from "@/components/ui/card";
import { HoverHint } from "@/components/ui/hover-hint";
import { getFolder } from "@/lib/api";

export default function FolderDetailPage({
  params,
}: {
  params: Promise<{ folderName: string }>;
}) {
  const { folderName } = use(params);
  const decodedFolderName = decodeURIComponent(folderName);
  const { data, isLoading } = useQuery({
    queryKey: ["folder", decodedFolderName],
    queryFn: () => getFolder(decodedFolderName),
  });

  return (
    <AppShell>
      {isLoading || !data ? (
        <Card className="p-6 text-sm text-muted">Loading folder...</Card>
      ) : (
        <section className="grid gap-5">
          <Card className="p-5 sm:p-6">
            <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr),320px]">
              <HoverHint hint="This folder has its own upload library, indexing lifecycle, and isolated retrieval collection.">
                <div>
                  <p className="section-label">Folder</p>
                  <p className="mt-3 font-display text-[2.3rem] leading-none text-text">{data.display_name}</p>
                  <p className="mt-3 text-sm leading-6 text-muted">{data.collection_name}</p>
                </div>
              </HoverHint>

              <div className="rounded-[28px] border border-black/[0.06] bg-card-secondary/45 p-5 dark:border-white/10">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="section-label">State</p>
                    <div className="mt-3">
                      <StatusBadge status={data.status} />
                    </div>
                  </div>
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-card text-accent">
                    <FileStack className="h-5 w-5" />
                  </div>
                </div>
                <p className="mt-4 text-sm leading-6 text-muted">
                  Upload sources first, then index this folder so retrieval can return stored chunks with lineage.
                </p>
              </div>
            </div>
          </Card>

          <div className="grid gap-5 xl:grid-cols-[1.08fr,0.92fr]">
            <UploadPanel folderName={data.display_name} />
            <IndexingPanel folderName={data.display_name} folderStatus={data.status} />
          </div>

          <DocumentTable folderName={data.display_name} documents={data.documents} />
          <RetrievalTestPanel initialFolderName={data.display_name} />
        </section>
      )}
    </AppShell>
  );
}
