import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  Company,
  CompanyCompleteness,
  CompanyCreate,
  CompanyUpdate,
  Page,
} from "@/api/types";

const KEY = "companies";
const PAGE_SIZE = 50;

export function useCompanies(params?: { limit?: number; offset?: number; q?: string }) {
  return useQuery({
    queryKey: [KEY, params],
    queryFn: () => api.get<Page<Company>>("/companies", params),
  });
}

/** Paginated company list with infinite scroll. Optionally filtered by `q`. */
export function useInfiniteCompanies(q?: string) {
  return useInfiniteQuery({
    queryKey: [KEY, "infinite", q ?? ""],
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      api.get<Page<Company>>("/companies", {
        limit: PAGE_SIZE,
        offset: pageParam,
        q: q || undefined,
      }),
    getNextPageParam: (lastPage) => {
      const loaded = lastPage.offset + lastPage.items.length;
      return loaded < lastPage.total ? loaded : undefined;
    },
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
