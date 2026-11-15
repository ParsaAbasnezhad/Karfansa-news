import { env } from "@/lib/env";
import { ApiError } from "@/lib/errors";
import type { ApiErrorBody } from "@/types/api";

type Query = Record<string, string | number | boolean | undefined>;

interface RequestOptions extends Omit<RequestInit, "body"> {
  query?: Query;
  body?: unknown;
}

function buildUrl(path: string, query?: Query): string {
  const base = env.apiUrl.replace(/\/$/, "");
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined) params.set(key, String(value));
  }
  const search = params.size > 0 ? `?${params.toString()}` : "";
  return `${base}/${path.replace(/^\//, "")}${search}`;
}

async function toApiError(response: Response): Promise<ApiError> {
  try {
    const payload = (await response.json()) as { error?: ApiErrorBody };
    if (payload.error) return new ApiError(response.status, payload.error);
  } catch {
    // Non-JSON error body: fall through to the generic error.
  }
  return new ApiError(response.status, {
    code: "http_error",
    message: `Request failed with status ${response.status}.`,
  });
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { query, body, headers, ...init } = options;
  const response = await fetch(buildUrl(path, query), {
    ...init,
    headers: {
      Accept: "application/json",
      ...(body !== undefined && { "Content-Type": "application/json" }),
      ...headers,
    },
    ...(body !== undefined && { body: JSON.stringify(body) }),
  });

  if (!response.ok) throw await toApiError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const apiClient = {
  get: <T>(path: string, options?: Omit<RequestOptions, "body" | "method">) =>
    apiRequest<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "body" | "method">) =>
    apiRequest<T>(path, { ...options, method: "POST", body }),
};
