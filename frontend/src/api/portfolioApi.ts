import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  AgentActivitySummary,
  Fund,
  Investment,
  Page,
  PortfolioSummary,
} from "@/api/types";

export function usePortfolioSummary() {
  return useQuery({
    queryKey: ["analytics", "portfolio"],
    queryFn: () => api.get<PortfolioSummary>("/analytics/portfolio"),
  });
}

export function useAgentActivity() {
  return useQuery({
    queryKey: ["analytics", "agent-activity"],
    queryFn: () => api.get<AgentActivitySummary>("/analytics/agent-activity"),
  });
}

export function useFunds() {
  return useQuery({
    queryKey: ["funds"],
    queryFn: () => api.get<Page<Fund>>("/funds"),
  });
}

export function useInvestments(params?: { limit?: number }) {
  return useQuery({
    queryKey: ["investments", params],
    queryFn: () => api.get<Page<Investment>>("/investments", params),
  });
}
