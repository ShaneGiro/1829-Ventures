import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { AgentEvent, AgentPolicy, Page, PolicyState } from "@/api/types";

/** Ritchie activity feed: authorized writes + policy_blocked attempts. */
export function useAgentEvents(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ["agent", "events", params],
    queryFn: () => api.get<Page<AgentEvent>>("/agent/events", params),
  });
}

/** Current binary authorization policy rows (human-readable, human-editable). */
export function useAgentPolicies() {
  return useQuery({
    queryKey: ["agent", "policies"],
    queryFn: () => api.get<AgentPolicy[]>("/agent/policies"),
  });
}

export function useSetPolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { tool: string; field_name?: string | null; state: PolicyState }) =>
      api.put<AgentPolicy>("/agent/policies", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agent", "policies"] }),
  });
}

export function useSendRitchieMessage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { prompt: string; entity_type?: string | null; entity_id?: string | null }) =>
      api.post<{ event_id: string; status: string }>("/agent/messages", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agent", "events"] }),
  });
}

export function useChatWithRitchie() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { prompt: string; entity_type?: string | null; entity_id?: string | null }) =>
      api.post<{ event_id: string; status: string; message: string; elapsed_ms?: number | null }>(
        "/agent/chat",
        body,
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agent", "events"] }),
  });
}
