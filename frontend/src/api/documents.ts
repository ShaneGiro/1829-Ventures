import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { DocumentMeta, Page } from "@/api/types";

interface PresignedUpload {
  document_id: string;
  upload_url: string;
  storage_key: string;
  fields: Record<string, string>;
}

interface UploadInput {
  file: File;
  company_id?: string;
  deal_id?: string;
  person_id?: string;
}

export function useDocuments(params?: {
  company_id?: string;
  deal_id?: string;
  person_id?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: ["documents", params],
    queryFn: () => api.get<Page<DocumentMeta>>("/documents", params),
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ file, ...links }: UploadInput) => {
      const upload = await api.post<PresignedUpload>("/documents/presigned-upload", {
        filename: file.name,
        content_type: file.type || undefined,
        size_bytes: file.size,
        ...links,
      });
      const form = new FormData();
      Object.entries(upload.fields).forEach(([key, value]) => form.append(key, value));
      form.append("file", file);
      const response = await fetch(upload.upload_url, { method: "POST", body: form });
      if (!response.ok) throw new Error(`Storage upload failed (${response.status}).`);
      return api.post<DocumentMeta>(`/documents/${upload.document_id}/confirm`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });
}

export function useArchiveDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (documentId: string) =>
      api.post<DocumentMeta>(`/documents/${documentId}/archive`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });
}

export async function downloadDocument(documentId: string): Promise<void> {
  const result = await api.get<{ download_url: string }>(`/documents/${documentId}/download`);
  window.open(result.download_url, "_blank", "noopener,noreferrer");
}
