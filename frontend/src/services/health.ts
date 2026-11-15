import { apiClient } from "@/lib/api-client";
import type { HealthResponse } from "@/types/api";

export function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  return apiClient.get<HealthResponse>("health/", signal ? { signal } : undefined);
}
