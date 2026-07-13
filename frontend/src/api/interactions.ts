import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Interaction, Page } from "@/api/types";

export interface OutreachInteraction extends Interaction {
  channel?: string | null;
  direction: "inbound" | "outbound" | "internal";
  follow_up_status: "none" | "needed" | "scheduled" | "complete";
  created_by_id?: string | null;
}

export interface InteractionCreateInput {
  interaction_type: string;
  summary?: string;
  body?: string;
  occurred_at?: string;
  company_id?: string;
  person_id?: string;
  deal_id?: string;
  channel?: string;
  direction?: OutreachInteraction["direction"];
  follow_up_status?: OutreachInteraction["follow_up_status"];
}

export function useInteractions(params?: {
  company_id?: string;
  person_id?: string;
  limit?: number;
  channel?: string;
  direction?: string;
  follow_up_status?: string;
  created_by_id?: string;
}) {
  return useQuery({
    queryKey: ["interactions", params],
    queryFn: () => api.get<Page<OutreachInteraction>>("/interactions", params),
  });
}

export function useCreateInteraction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: InteractionCreateInput) =>
      api.post<OutreachInteraction>("/interactions", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["interactions"] }),
  });
}
