import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api";
import type { ImportBatch, ImportRow, Page } from "@/api/types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export function useImportBatch(batchId: string | undefined) {
  return useQuery({
    queryKey: ["imports", batchId],
    queryFn: () => api.get<ImportBatch>(`/imports/${batchId}`),
    enabled: !!batchId,
  });
}

export function useImportRows(batchId: string | undefined, params?: { status?: string }) {
  return useQuery({
    queryKey: ["imports", batchId, "rows", params],
    queryFn: () => api.get<Page<ImportRow>>(`/imports/${batchId}/rows`, params),
    enabled: !!batchId,
  });
}

/** Accepted Dealroom upload extensions (kept in sync with the backend registry). */
export const DEALROOM_UPLOAD_ACCEPT = ".csv,.xlsx,.xlsm";

/** Upload a Dealroom export (CSV or Excel, multipart) to create a preview batch. */
export function useUploadDealroomFile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (file: File): Promise<ImportBatch> => {
      const formData = new FormData();
      formData.append("file", file);
      // Direct fetch for multipart so the browser sets the boundary header.
      const res = await fetch(`${API_BASE}/imports/dealroom`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });
      if (!res.ok) {
        const message = await res
          .json()
          .then((body: { message?: string }) => body.message)
          .catch(() => undefined);
        throw new ApiError(res.status, message ?? `Upload failed: ${res.status}`);
      }
      return (await res.json()) as ImportBatch;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["imports"] }),
  });
}

/** Erase staged import batches that were never committed. Called on page load so
 *  forgotten uploads don't accumulate in the database. */
export async function discardUncommittedImports(): Promise<number> {
  const res = await fetch(`${API_BASE}/imports/uncommitted`, {
    method: "DELETE",
    credentials: "include",
  });
  if (!res.ok) throw new ApiError(res.status, `Discard failed: ${res.status}`);
  const body = (await res.json()) as { deleted: number };
  return body.deleted;
}

/** Download the canonical Dealroom column template (CSV, header row only). */
export async function downloadDealroomTemplate(): Promise<void> {
  const res = await fetch(`${API_BASE}/imports/dealroom/template`, {
    credentials: "include",
  });
  if (!res.ok) throw new ApiError(res.status, `Template download failed: ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "dealroom_import_template.csv";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function useCommitImport(batchId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { commit_clean?: boolean; skip_conflicts?: boolean }) =>
      api.post<ImportBatch>(`/imports/${batchId}/commit`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["imports", batchId] }),
  });
}
