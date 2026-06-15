import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api";
import type { components } from "@/types/api";

export type CurrentUser = components["schemas"]["UserRead"];

const ME_KEY = ["auth", "me"] as const;

/**
 * Current-session hook. Fetches /auth/me; a 401 resolves to `null` (logged out)
 * rather than throwing, so callers can branch on `user`.
 */
export function useAuth() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: ME_KEY,
    queryFn: async (): Promise<CurrentUser | null> => {
      try {
        return await api.get<CurrentUser>("/auth/me");
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null;
        throw error;
      }
    },
  });

  const logout = useMutation({
    mutationFn: () => api.post<void>("/auth/logout"),
    onSuccess: () => {
      queryClient.setQueryData(ME_KEY, null);
      queryClient.invalidateQueries({ queryKey: ME_KEY });
    },
  });

  return {
    user: query.data ?? null,
    isLoading: query.isLoading,
    isAuthenticated: !!query.data,
    error: query.error,
    logout: logout.mutate,
  };
}

/** Redirect the browser to the backend's Google OAuth entrypoint. */
export function startLogin(): void {
  window.location.href = "/api/auth/login";
}
