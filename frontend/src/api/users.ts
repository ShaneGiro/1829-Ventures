import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Page, User } from "@/api/types";

/** Human users available as task assignees. */
export function useUsers(params?: { limit?: number; offset?: number }) {
  return useQuery({
    queryKey: ["users", params],
    queryFn: () => api.get<Page<User>>("/users", params),
  });
}
