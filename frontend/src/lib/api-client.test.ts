import { afterEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "@/lib/api-client";
import { queryClient } from "@/app/query-client";
import { ApiError } from "@/lib/errors";

function mockFetch(status: number, body: unknown): void {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
    ),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  queryClient.clear();
});

describe("apiClient", () => {
  it("returns parsed JSON on success", async () => {
    mockFetch(200, { status: "ok" });
    await expect(apiClient.get("health/")).resolves.toEqual({ status: "ok" });
  });

  it("throws ApiError built from the backend error envelope", async () => {
    mockFetch(404, { error: { code: "not_found", message: "Missing" } });
    await expect(apiClient.get("nope/")).rejects.toMatchObject({
      status: 404,
      code: "not_found",
      message: "Missing",
    });
    await expect(apiClient.get("nope/")).rejects.toBeInstanceOf(ApiError);
  });

  it("sends session cookies and a CSRF header for auth mutations", async () => {
    vi.stubGlobal("document", { cookie: "csrftoken=abc123" });
    mockFetch(200, { user: { id: 1 } });
    await apiClient.post("auth/login/", { identifier: "user@example.com", password: "secret" });
    expect(fetch).toHaveBeenCalledWith(
      "/api/v1/auth/login/",
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        headers: expect.objectContaining({ "X-CSRFToken": "abc123" }),
      }),
    );
  });

  it("bootstraps the CSRF cookie before the first mutation", async () => {
    vi.stubGlobal("document", { cookie: "" });
    const request = vi.fn(async (url: string) => {
      if (url.endsWith("auth/csrf/")) {
        document.cookie = "csrftoken=fresh-token";
        return new Response(JSON.stringify({ message: "ok" }), { status: 200 });
      }
      return new Response(JSON.stringify({ message: "sent" }), { status: 200 });
    });
    vi.stubGlobal("fetch", request);
    await apiClient.post("auth/forgot-password/", { identifier: "user@example.com" });
    expect(request).toHaveBeenNthCalledWith(
      1,
      "/api/v1/auth/csrf/",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(request).toHaveBeenNthCalledWith(
      2,
      "/api/v1/auth/forgot-password/",
      expect.objectContaining({
        headers: expect.objectContaining({ "X-CSRFToken": "fresh-token" }),
      }),
    );
  });

  it("clears the cached session on a protected 401 but not invalid login", async () => {
    vi.stubGlobal("document", { cookie: "csrftoken=abc123" });
    queryClient.setQueryData(["auth", "me"], { id: 1 });
    mockFetch(401, { error: { code: "unauthorized", message: "Unauthorized" } });
    await expect(apiClient.post("auth/change-password/", {})).rejects.toBeInstanceOf(ApiError);
    expect(queryClient.getQueryData(["auth", "me"])).toBeNull();
    queryClient.setQueryData(["auth", "me"], { id: 1 });
    await expect(apiClient.post("auth/login/", {})).rejects.toBeInstanceOf(ApiError);
    expect(queryClient.getQueryData(["auth", "me"])).toEqual({ id: 1 });
  });
});
