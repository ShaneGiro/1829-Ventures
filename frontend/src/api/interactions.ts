import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Interaction, Page } from "@/api/types";

export function useInteractions(params?: { company_id?: string; limit?: number }) {
  return useQuery({
    queryKey: ["interactions", params],
    queryFn: () => api.get<Page<Interaction>>("/interactions", params),
  });
}

export function useCreateInteraction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Partial<Interaction>) => api.post<Interaction>("/interactions", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["interactions"] }),
  });
}
