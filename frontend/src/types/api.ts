/** Error envelope returned by the backend: `{ "error": { code, message, details? } }`. */
export interface ApiErrorBody {
  code: string;
  message: string;
  details?: unknown;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  checks: Record<string, string>;
}
