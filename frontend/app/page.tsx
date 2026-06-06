"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Compass, FolderPlus, Layers3, LibraryBig } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { CreateFolderDialog } from "@/components/create-folder-dialog";
import { FolderCard } from "@/components/folder-card";
import { RetrievalTestPanel } from "@/components/retrieval-test-panel";
import { useToast } from "@/components/toast-provider";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { HoverHint } from "@/components/ui/hover-hint";
import { deleteFolder, getApiErrorMessage, getFolders } from "@/lib/api";

export default function DashboardPage() {
  const queryClient = useQueryClient();
  const { pushToast } = useToast();
  const { data: folders = [], isLoading } = useQuery({ queryKey: ["folders"], queryFn: getFolders });

  const deleteMutation = useMutation({
    mutationFn: deleteFolder,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["folders"] });
      pushToast({ tone: "success", title: "Folder deleted", description: "The library and its vectors were removed." });
    },
    onError: (error: unknown) =>
      pushToast({ tone: "error", title: "Folder delete failed", description: getApiErrorMessage(error) }),
  });

  return (
    <AppShell>
      <section className="grid gap-5">
        <Card className="overflow-hidden p-5 sm:p-6">
          <div className="grid gap-5 xl:grid-cols-[minmax(0,1.2fr),0.95fr]">
            <div className="min-w-0">
              <p className="section-label">VecSeek Library</p>
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <CreateFolderDialog />
                <HoverHint hint="Jump straight to the live retrieval test bench at the bottom of this page.">
                  <Button variant="secondary" onClick={() => window.location.assign("#retrieval-lab")}>
                    Open Retrieval
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </HoverHint>
              </div>
              <div className="mt-8 grid gap-3 sm:grid-cols-2">
                <div className="rounded-[26px] border border-black/[0.06] bg-card px-5 py-5 dark:border-white/10">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-card-secondary text-accent">
                      <LibraryBig className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.24em] text-muted">Folders</p>
                      <p className="mt-1 text-2xl font-semibold text-text">{folders.length}</p>
                    </div>
                  </div>
                </div>
                <div className="rounded-[26px] border border-black/[0.06] bg-card px-5 py-5 dark:border-white/10">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-card-secondary text-accent2">
                      <Layers3 className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.24em] text-muted">Indexed Chunks</p>
                      <p className="mt-1 text-2xl font-semibold text-text">
                        {folders.reduce((count, folder) => count + folder.indexed_chunk_count, 0)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-[28px] border border-black/[0.06] bg-card-secondary/45 p-5 dark:border-white/10">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-card text-accent shadow-glow">
                  <Compass className="h-5 w-5" />
                </div>
                <div>
                  <p className="section-label">Flow</p>
                  <p className="mt-1 text-sm leading-6 text-muted">
                    Create a folder, upload source documents, run indexing, then validate chunks before using the API.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </Card>

        <Card className="p-4 sm:p-5">
          <div className="flex items-center justify-between gap-4 border-b border-black/[0.06] pb-4 dark:border-white/10">
            <HoverHint hint="Each row is an isolated document space with its own vector collection and retrieval state.">
              <div>
                <p className="section-label">Folders</p>
                <p className="mt-2 text-sm leading-6 text-muted">Everything stays one scan away from upload to retrieval.</p>
              </div>
            </HoverHint>
            {folders.length ? null : (
              <div className="hidden items-center gap-2 rounded-full border border-black/[0.06] bg-card px-3 py-2 text-sm text-muted dark:border-white/10 md:flex">
                <FolderPlus className="h-4 w-4 text-accent" />
                Start with a folder
              </div>
            )}
          </div>

          <div className="mt-4 space-y-3">
            {isLoading ? (
              <div className="rounded-[24px] border border-black/[0.06] bg-card px-5 py-8 text-sm text-muted dark:border-white/10">
                Loading folders...
              </div>
            ) : folders.length ? (
              folders.map((folder) => (
                <FolderCard key={folder.id} folder={folder} onDelete={(name) => deleteMutation.mutate(name)} />
              ))
            ) : (
              <div className="rounded-[24px] border border-dashed border-black/[0.08] bg-card-secondary/35 px-5 py-12 text-center dark:border-white/10">
                <p className="font-display text-3xl text-text">VecSeek starts quietly.</p>
                <p className="mt-3 text-sm leading-6 text-muted">
                  Create a folder, add files, and the rest of the interface will open up around that first dock.
                </p>
              </div>
            )}
          </div>
        </Card>

        <RetrievalTestPanel />
      </section>
    </AppShell>
  );
}
