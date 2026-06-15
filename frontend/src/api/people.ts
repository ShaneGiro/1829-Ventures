import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Affiliation, Page, Person } from "@/api/types";

export function usePeople(params?: { limit?: number; offset?: number; q?: string }) {
  return useQuery({
    queryKey: ["people", params],
    queryFn: () => api.get<Page<Person>>("/people", params),
  });
}

export function usePerson(id: string | undefined) {
  return useQuery({
    queryKey: ["people", id],
    queryFn: () => api.get<Person>(`/people/${id}`),
    enabled: !!id,
  });
}

export function usePersonAffiliations(id: string | undefined) {
  return useQuery({
    queryKey: ["people", id, "affiliations"],
    queryFn: () => api.get<Affiliation[]>(`/people/${id}/affiliations`),
    enabled: !!id,
  });
}
