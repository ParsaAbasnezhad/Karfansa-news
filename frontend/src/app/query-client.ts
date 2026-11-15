import { MutationCache, QueryCache, QueryClient } from "@tanstack/react-query";

import { reportError } from "@/lib/errors";

/** Global error handling for every query and mutation lives here. */
export const queryClient = new QueryClient({
  queryCache: new QueryCache({ onError: reportError }),
  mutationCache: new MutationCache({ onError: reportError }),
  defaultOptions: {
    queries: { staleTime: 30_000, refetchOnWindowFocus: false },
  },
});
