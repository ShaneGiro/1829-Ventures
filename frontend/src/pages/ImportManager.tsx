import { useEffect, useState } from "react";
import {
  DEALROOM_UPLOAD_ACCEPT,
  discardUncommittedImports,
  downloadDealroomTemplate,
  useCommitImport,
  useImportBatch,
  useImportRows,
  useUploadDealroomFile,
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
  const [templateError, setTemplateError] = useState(false);
  const upload = useUploadDealroomFile();
  const { data: batch } = useImportBatch(batchId);
  const { data: rows } = useImportRows(batchId);
  const commit = useCommitImport(batchId ?? "");

  // On page load/refresh, discard any uploaded-but-uncommitted batches so
  // forgotten staging data doesn't pile up in the database.
  useEffect(() => {
    void discardUncommittedImports().catch(() => {});
  }, []);

  const onFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) upload.mutate(file, { onSuccess: (b) => setBatchId(b.id) });
  };

  const onDownloadTemplate = () => {
    setTemplateError(false);
    downloadDealroomTemplate().catch(() => setTemplateError(true));
  };

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Dealroom imports</h1>

      <Card>
        <CardHeader className="flex items-center justify-between">
          <CardTitle>Upload export</CardTitle>
          <Button size="sm" variant="outline" onClick={onDownloadTemplate}>
            Download template
          </Button>
        </CardHeader>
        <CardContent className="space-y-2">
          <input
            type="file"
            accept={DEALROOM_UPLOAD_ACCEPT}
            onChange={onFile}
            disabled={upload.isPending}
          />
          <p className="text-xs text-muted-foreground">
            Accepts a Dealroom CSV or Excel (.xlsx) export.
          </p>
          {upload.isPending && <p className="text-sm text-muted-foreground">Uploading…</p>}
          {upload.isError && (
            <p className="text-sm text-red-700">
              {upload.error instanceof Error ? upload.error.message : "Upload failed."}
            </p>
          )}
          {templateError && <p className="text-sm text-red-700">Template download failed.</p>}
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
