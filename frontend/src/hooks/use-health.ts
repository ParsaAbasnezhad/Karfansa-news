import { useQuery } from "@tanstack/react-query";

import { fetchHealth } from "@/services/health";

export function useHealth() {
  return useQuery({
    queryKey: ["system", "health"],
    queryFn: ({ signal }) => fetchHealth(signal),
    retry: false,
  });
}
