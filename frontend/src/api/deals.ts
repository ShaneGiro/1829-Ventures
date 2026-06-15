import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Deal, DealStatus, Page, Rubric, RubricUpdate } from "@/api/types";

export function useDeals(params?: { company_id?: string; limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ["deals", params],
    queryFn: () => api.get<Page<Deal>>("/deals", params),
  });
}

export function useDealStatuses() {
  return useQuery({
    queryKey: ["deal-statuses"],
    queryFn: () => api.get<Page<DealStatus>>("/deal-statuses"),
  });
}

export function useUpdateDeal(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Partial<Deal>) => api.patch<Deal>(`/deals/${id}`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["deals"] }),
  });
}

/** Move a deal to a different pipeline stage. */
export function useMoveDeal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, dealStatusId }: { id: string; dealStatusId: string }) =>
      api.patch<Deal>(`/deals/${id}`, { deal_status_id: dealStatusId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["deals"] }),
  });
}

/** Soft-delete (archive) a deal, removing it from the pipeline. */
export function useArchiveDeal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.post<Deal>(`/deals/${id}/archive`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["deals"] }),
  });
}

export function useDealRubric(dealId: string | undefined) {
  return useQuery({
    queryKey: ["deals", dealId, "rubric"],
    queryFn: () => api.get<Rubric>(`/deals/${dealId}/rubric`),
    enabled: !!dealId,
  });
}

export function useUpdateRubric(dealId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: RubricUpdate) => api.patch<Rubric>(`/deals/${dealId}/rubric`, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["deals", dealId, "rubric"] }),
  });
}
