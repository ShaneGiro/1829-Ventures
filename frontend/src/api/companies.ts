import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  Company,
  CompanyCompleteness,
  CompanyCreate,
  CompanyUpdate,
  Page,
} from "@/api/types";

const KEY = "companies";

export function useCompanies(params?: { limit?: number; offset?: number; q?: string }) {
  return useQuery({
    queryKey: [KEY, params],
    queryFn: () => api.get<Page<Company>>("/companies", params),
  });
}

export function useCompany(id: string | undefined) {
  return useQuery({
    queryKey: [KEY, id],
    queryFn: () => api.get<Company>(`/companies/${id}`),
    enabled: !!id,
  });
}

export function useCompanyCompleteness(id: string | undefined) {
  return useQuery({
    queryKey: [KEY, id, "completeness"],
    queryFn: () => api.get<CompanyCompleteness>(`/companies/${id}/completeness`),
    enabled: !!id,
  });
}

export function useCreateCompany() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CompanyCreate) => api.post<Company>("/companies", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEY] }),
  });
}

export function useUpdateCompany(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: CompanyUpdate) => api.patch<Company>(`/companies/${id}`, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [KEY, id] });
      qc.invalidateQueries({ queryKey: [KEY] });
    },
  });
}
