import { queryClient } from "@/app/query-client";
import { env } from "@/lib/env";
import { ApiError } from "@/lib/errors";
import type { ApiErrorBody } from "@/types/api";

type Query = Record<string, string | number | boolean | undefined>;
let csrfBootstrap: Promise<void> | undefined;
const publicAuthPaths = new Set([
  "auth/login/",
  "auth/request-login-otp/",
  "auth/verify-login-otp/",
  "auth/register/",
  "auth/verify-registration/",
  "auth/resend-otp/",
  "auth/forgot-password/",
  "auth/verify-reset-otp/",
  "auth/reset-password/",
]);

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
    const payload = (await response.json()) as { error?: ApiErrorBody; detail?: string };
    if (payload.error) return new ApiError(response.status, payload.error);
    if (payload.detail) {
      return new ApiError(response.status, { code: "http_error", message: payload.detail });
    }
  } catch {
    // Non-JSON error body: fall through to the generic error.
  }
  return new ApiError(response.status, {
    code: "http_error",
    message: `Request failed with status ${response.status}.`,
  });
}

function csrfToken(): string | undefined {
  if (typeof document === "undefined") return undefined;
  return document.cookie
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith("csrftoken="))
    ?.slice("csrftoken=".length);
}

async function ensureCsrf(): Promise<void> {
  if (csrfToken()) return;
  csrfBootstrap ??= fetch(buildUrl("auth/csrf/"), { credentials: "include" }).then(
    async (response) => {
      if (!response.ok) throw await toApiError(response);
    },
  );
  try {
    await csrfBootstrap;
  } finally {
    csrfBootstrap = undefined;
  }
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { query, body, headers, ...init } = options;
  if (init.method && !["GET", "HEAD", "OPTIONS"].includes(init.method.toUpperCase())) {
    await ensureCsrf();
  }
  const response = await fetch(buildUrl(path, query), {
    ...init,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(body !== undefined && { "Content-Type": "application/json" }),
      ...(csrfToken() && { "X-CSRFToken": decodeURIComponent(csrfToken()!) }),
      ...headers,
    },
    ...(body !== undefined && { body: JSON.stringify(body) }),
  });

  if (!response.ok) {
    if (response.status === 401 && !publicAuthPaths.has(path.replace(/^\//, ""))) {
      queryClient.setQueryData(["auth", "me"], null);
    }
    throw await toApiError(response);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const apiClient = {
  get: <T>(path: string, options?: Omit<RequestOptions, "body" | "method">) =>
    apiRequest<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "body" | "method">) =>
    apiRequest<T>(path, { ...options, method: "POST", body }),
  patch: <T>(path: string, body?: unknown, options?: Omit<RequestOptions, "body" | "method">) =>
    apiRequest<T>(path, { ...options, method: "PATCH", body }),
};
