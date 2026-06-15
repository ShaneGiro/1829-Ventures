import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Page, Task, TaskCreate } from "@/api/types";

const KEY = "tasks";

export function useTasks(params?: {
  company_id?: string;
  owner_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: [KEY, params],
    queryFn: () => api.get<Page<Task>>("/tasks", params),
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: TaskCreate) => api.post<Task>("/tasks", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEY] }),
  });
}

export function useCompleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.post<Task>(`/tasks/${id}/complete`, {}),
    onSuccess: () => qc.invalidateQueries({ queryKey: [KEY] }),
  });
}
