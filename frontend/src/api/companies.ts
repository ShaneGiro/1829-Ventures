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
  CompanyDealroomData,
  CompanyUpdate,
  Page,
  Rubric,
  RubricUpdate,
} from "@/api/types";

const KEY = "companies";
const PAGE_SIZE = 50;

/** Structured company filters, mirroring the backend `CompanyFilters`. */
export interface CompanyFilters {
  sector?: string[];
  relationship_status?: string[];
  stage?: string[];
  country?: string[];
  state?: string[];
  city?: string[];
  source_system?: string[];
  has_rit_nexus?: boolean;
  imported_unreviewed?: boolean;
  has_website?: boolean;
  min_completeness?: number;
  max_completeness?: number;
  dealroom_filter?: string[];
}

export type DealroomColumnKind = "text" | "number" | "date" | "boolean";

export interface DealroomColumnOption {
  name: string;
  kind: DealroomColumnKind;
}

export function useCompanies(params?: { limit?: number; offset?: number; q?: string }) {
  return useQuery({
    queryKey: [KEY, params],
    queryFn: () => api.get<Page<Company>>("/companies", params),
  });
}

/** Paginated company list with infinite scroll, optional `q` search, and filters. */
export function useInfiniteCompanies(q?: string, filters?: CompanyFilters) {
  return useInfiniteQuery({
    queryKey: [KEY, "infinite", q ?? "", filters ?? {}],
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      api.get<Page<Company>>("/companies", {
        limit: PAGE_SIZE,
        offset: pageParam,
        q: q || undefined,
        sector: filters?.sector?.length ? filters.sector : undefined,
        relationship_status: filters?.relationship_status?.length
          ? filters.relationship_status
          : undefined,
        stage: filters?.stage?.length ? filters.stage : undefined,
        country: filters?.country?.length ? filters.country : undefined,
        state: filters?.state?.length ? filters.state : undefined,
        city: filters?.city?.length ? filters.city : undefined,
        source_system: filters?.source_system?.length ? filters.source_system : undefined,
        has_rit_nexus: filters?.has_rit_nexus,
        imported_unreviewed: filters?.imported_unreviewed,
        has_website: filters?.has_website,
        min_completeness: filters?.min_completeness,
        max_completeness: filters?.max_completeness,
        dealroom_filter: filters?.dealroom_filter?.length ? filters.dealroom_filter : undefined,
      }),
    getNextPageParam: (lastPage) => {
      const loaded = lastPage.offset + lastPage.items.length;
      return loaded < lastPage.total ? loaded : undefined;
    },
  });
}

export function useDealroomColumns() {
  return useQuery({
    queryKey: [KEY, "dealroom-columns"],
    queryFn: () => api.get<DealroomColumnOption[]>("/companies/dealroom-columns"),
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

export function useCompanyDealroomData(id: string | undefined) {
  return useQuery({
    queryKey: [KEY, id, "dealroom-data"],
    queryFn: () => api.get<CompanyDealroomData>(`/companies/${id}/dealroom-data`),
    enabled: !!id,
  });
}

export function useCompanyRubric(id: string | undefined) {
  return useQuery({
    queryKey: [KEY, id, "rubric"],
    queryFn: () => api.get<Rubric>(`/companies/${id}/rubric`),
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

export function useUpdateCompanyRubric(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: RubricUpdate) => api.patch<Rubric>(`/companies/${id}/rubric`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEY, id, "rubric"] }),
  });
}
