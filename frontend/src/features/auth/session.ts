import { useQuery } from "@tanstack/react-query";

import { authApi, type AuthUser } from "@/features/auth/api";
import { ApiError } from "@/lib/errors";

export const sessionKey = ["auth", "me"] as const;

export function useSession({ refreshOnMount = false }: { refreshOnMount?: boolean } = {}): {
  user: AuthUser | null;
  isPending: boolean;
  isFetching: boolean;
  isError: boolean;
  refetch: () => void;
} {
  const query = useQuery({
    queryKey: sessionKey,
    queryFn: async () => {
      try {
        return (await authApi.me()).user;
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null;
        throw error;
      }
    },
    retry: false,
    staleTime: 60_000,
    refetchOnMount: refreshOnMount ? "always" : false,
    refetchOnWindowFocus: "always",
  });
  return {
    user: query.data ?? null,
    isPending: query.isPending,
    isFetching: query.isFetching,
    isError: query.isError,
    refetch: () => void query.refetch(),
  };
}
