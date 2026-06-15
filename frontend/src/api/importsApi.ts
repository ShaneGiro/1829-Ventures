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

/** Upload a Dealroom CSV (multipart) to create a preview batch. */
export function useUploadDealroomCsv() {
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
      if (!res.ok) throw new ApiError(res.status, `Upload failed: ${res.status}`);
      return (await res.json()) as ImportBatch;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["imports"] }),
  });
}

export function useCommitImport(batchId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { commit_clean?: boolean; skip_conflicts?: boolean }) =>
      api.post<ImportBatch>(`/imports/${batchId}/commit`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["imports", batchId] }),
  });
}
