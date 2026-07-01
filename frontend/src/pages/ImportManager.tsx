import { useEffect, useMemo, useState } from "react";
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

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

export function ImportManager() {
  const [batchId, setBatchId] = useState<string | undefined>();
  const [templateError, setTemplateError] = useState(false);
  const upload = useUploadDealroomFile();
  const { data: batch } = useImportBatch(batchId);
  const { data: rows } = useImportRows(batchId);
  const commit = useCommitImport(batchId ?? "");

  const rawColumns = useMemo(() => {
    const seen = new Set<string>();
    const columns: string[] = [];
    rows?.items.forEach((row) => {
      Object.keys(row.raw_data ?? {}).forEach((column) => {
        if (!seen.has(column)) {
          seen.add(column);
          columns.push(column);
        }
      });
    });
    return columns;
  }, [rows]);

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
            <div className="max-h-[560px] overflow-auto rounded-md border">
              {rows?.items.length ? (
                <table className="min-w-full border-separate border-spacing-0 text-left text-sm">
                  <thead className="sticky top-0 z-10 bg-background">
                    <tr>
                      <th className="sticky left-0 z-20 border-b bg-background px-3 py-2 font-medium">
                        Row
                      </th>
                      <th className="border-b px-3 py-2 font-medium">Status</th>
                      <th className="min-w-56 border-b px-3 py-2 font-medium">Import note</th>
                      {rawColumns.map((column) => (
                        <th
                          key={column}
                          className="min-w-48 border-b px-3 py-2 align-bottom font-medium"
                        >
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {rows.items.map((r) => (
                      <tr key={r.id} className="odd:bg-muted/30">
                        <td className="sticky left-0 border-b bg-inherit px-3 py-2 font-medium">
                          {r.row_number}
                        </td>
                        <td className="border-b px-3 py-2 align-top">
                          <Badge className={ROW_STYLE[r.status] ?? ""}>{r.status}</Badge>
                        </td>
                        <td className="max-w-72 whitespace-pre-wrap break-words border-b px-3 py-2 align-top text-muted-foreground">
                          {r.skip_reason ?? ""}
                        </td>
                        {rawColumns.map((column) => (
                          <td
                            key={`${r.id}-${column}`}
                            className="max-w-80 whitespace-pre-wrap break-words border-b px-3 py-2 align-top"
                          >
                            {formatCellValue(r.raw_data?.[column])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : null}
              {rows?.items.length === 0 && (
                <p className="p-3 text-sm text-muted-foreground">No rows.</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
