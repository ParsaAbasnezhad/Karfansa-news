import { afterEach, describe, expect, it, vi } from "vitest";

import { apiClient } from "@/lib/api-client";
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

afterEach(() => vi.unstubAllGlobals());

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
});
