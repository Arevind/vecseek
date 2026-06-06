import { Badge } from "@/components/ui/badge";
import type { FolderStatus } from "@/lib/types";

const config: Record<FolderStatus, { label: string; variant: "default" | "success" | "warning" | "danger" }> = {
  empty: { label: "Empty", variant: "default" },
  has_files: { label: "Has Files", variant: "default" },
  indexing: { label: "Indexing", variant: "warning" },
  indexed: { label: "Indexed", variant: "success" },
  needs_reindex: { label: "Needs Re-index", variant: "warning" },
  failed: { label: "Failed", variant: "danger" },
};

export function StatusBadge({ status }: { status: FolderStatus }) {
  return <Badge variant={config[status].variant}>{config[status].label}</Badge>;
}
