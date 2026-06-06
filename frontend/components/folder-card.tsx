import Link from "next/link";
import { ArrowUpRight, FolderOpen, Trash2 } from "lucide-react";

import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";
import { HoverHint } from "@/components/ui/hover-hint";
import type { Folder } from "@/lib/types";

export function FolderCard({
  folder,
  onDelete,
}: {
  folder: Folder;
  onDelete: (folderName: string) => void;
}) {
  return (
    <div className="grid gap-4 rounded-[26px] border border-black/[0.06] bg-card px-5 py-5 transition hover:border-accent/25 hover:shadow-float dark:border-white/10 md:grid-cols-[minmax(0,1.5fr),0.8fr,0.8fr,auto] md:items-center">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge status={folder.status} />
          <p className="text-xs uppercase tracking-[0.22em] text-muted">{folder.collection_name}</p>
        </div>
        <h3 className="mt-3 text-lg font-semibold text-text">{folder.display_name}</h3>
        <p className="mt-1 text-sm text-muted">Created for one isolated document corpus and retrieval index.</p>
      </div>

      <div className="rounded-[22px] border border-black/[0.06] bg-card-secondary/45 px-4 py-3 dark:border-white/10">
        <p className="text-[11px] uppercase tracking-[0.24em] text-muted">Documents</p>
        <p className="mt-2 text-2xl font-semibold text-text">{folder.document_count}</p>
      </div>

      <div className="rounded-[22px] border border-black/[0.06] bg-card-secondary/45 px-4 py-3 dark:border-white/10">
        <p className="text-[11px] uppercase tracking-[0.24em] text-muted">Chunks</p>
        <p className="mt-2 text-2xl font-semibold text-text">{folder.indexed_chunk_count}</p>
      </div>

      <div className="flex items-center gap-2 md:justify-end">
        <HoverHint hint="Open the folder to upload files, manage indexing, and test retrieval." align="right">
          <Link href={`/folders/${encodeURIComponent(folder.display_name)}`}>
            <Button className="gap-2">
              <FolderOpen className="h-4 w-4" />
              Open
              <ArrowUpRight className="h-4 w-4" />
            </Button>
          </Link>
        </HoverHint>
        <HoverHint hint="Delete the folder, local files, and its vector index." align="right">
          <Button variant="danger" onClick={() => onDelete(folder.display_name)} aria-label={`Delete ${folder.display_name}`}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </HoverHint>
      </div>
    </div>
  );
}
