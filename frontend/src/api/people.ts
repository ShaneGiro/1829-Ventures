import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Affiliation, Page, Person, PersonUpdate } from "@/api/types";

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

export function useUpdatePerson(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: PersonUpdate) => api.patch<Person>(`/people/${id}`, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["people", id] });
      queryClient.invalidateQueries({ queryKey: ["people"] });
    },
  });
}
