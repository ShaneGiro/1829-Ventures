import { useState } from "react";
import {
  useCommitImport,
  useImportBatch,
  useImportRows,
  useUploadDealroomCsv,
} from "@/api/importsApi";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const ROW_STYLE: Record<string, string> = {
  conflict: "border-amber-500 text-amber-700",
  skipped: "border-muted text-muted-foreground",
  committed: "border-green-500 text-green-700",
  created: "border-green-500 text-green-700",
  matched: "border-blue-500 text-blue-700",
};

export function ImportManager() {
  const [batchId, setBatchId] = useState<string | undefined>();
  const upload = useUploadDealroomCsv();
  const { data: batch } = useImportBatch(batchId);
  const { data: rows } = useImportRows(batchId);
  const commit = useCommitImport(batchId ?? "");

  const onFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) upload.mutate(file, { onSuccess: (b) => setBatchId(b.id) });
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Dealroom imports</h1>

      <Card>
        <CardHeader>
          <CardTitle>Upload CSV</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <input type="file" accept=".csv" onChange={onFile} disabled={upload.isPending} />
          {upload.isPending && <p className="text-sm text-muted-foreground">Uploading…</p>}
          {upload.isError && <p className="text-sm text-red-700">Upload failed.</p>}
        </CardContent>
      </Card>

      {batch && (
        <Card>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>
              Batch {batch.filename ?? batch.id} · <Badge>{batch.status}</Badge>
            </CardTitle>
            <Button
              size="sm"
              onClick={() => commit.mutate({ commit_clean: true, skip_conflicts: true })}
              disabled={commit.isPending || batch.status === "committed"}
            >
              {commit.isPending ? "Committing…" : "Commit clean rows"}
            </Button>
          </CardHeader>
          <CardContent>
            <div className="mb-3 text-sm text-muted-foreground">
              {batch.total_rows} rows detected.
            </div>
            <div className="max-h-[420px] space-y-1 overflow-auto">
              {rows?.items.map((r) => (
                <div
                  key={r.id}
                  className="flex items-center justify-between rounded-md border p-2 text-sm"
                >
                  <span className="truncate">
                    Row {r.row_number}
                    {r.skip_reason ? ` — ${r.skip_reason}` : ""}
                  </span>
                  <Badge className={ROW_STYLE[r.status] ?? ""}>{r.status}</Badge>
                </div>
              ))}
              {rows?.items.length === 0 && (
                <p className="text-sm text-muted-foreground">No rows.</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
