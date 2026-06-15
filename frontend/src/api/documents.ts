import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { DocumentMeta, Page } from "@/api/types";

export function useDocuments(params?: { company_id?: string; deal_id?: string; limit?: number }) {
  return useQuery({
    queryKey: ["documents", params],
    queryFn: () => api.get<Page<DocumentMeta>>("/documents", params),
  });
}
