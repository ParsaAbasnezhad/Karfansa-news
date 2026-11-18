import { describe, expect, it } from "vitest";

import { isSafeHref } from "./safe-text-utils";

describe("public destination links", () => {
  it("allows site paths and normal HTTP destinations", () => {
    expect(isSafeHref("/news?topic=trade")).toBe(true);
    expect(isSafeHref("https://example.com/story")).toBe(true);
  });

  it("rejects executable, ambiguous, and malformed destinations", () => {
    for (const href of [
      "javascript:alert(1)",
      "data:text/html,<script>alert(1)</script>",
      "//evil.example/path",
      "/\\evil.example/path",
      "https://user:pass@example.com/path",
      "https://example.com\n.evil.example",
      "https:///",
    ]) {
      expect(isSafeHref(href), href).toBe(false);
    }
  });
});
