import { describe, expect, it } from "vitest";

import { canonicalUrl, SITE_ORIGIN } from "./use-page-meta";

describe("canonicalUrl", () => {
  it("uses the production domain and removes transient query parameters", () => {
    expect(canonicalUrl("/editorial/category/اقتصاد?page=2")).toBe(
      `${SITE_ORIGIN}/editorial/category/%D8%A7%D9%82%D8%AA%D8%B5%D8%A7%D8%AF`,
    );
  });

  it("accepts only a clean same-origin HTTPS override", () => {
    expect(canonicalUrl("/editorial/story", `${SITE_ORIGIN}/editorial/original`)).toBe(
      `${SITE_ORIGIN}/editorial/original`,
    );
    expect(canonicalUrl("/editorial/story", "https://example.com/other")).toBe(
      `${SITE_ORIGIN}/editorial/story`,
    );
    expect(canonicalUrl("/editorial/story", "http://karfansa.news.ir/other")).toBe(
      `${SITE_ORIGIN}/editorial/story`,
    );
    expect(canonicalUrl("/editorial/story", `${SITE_ORIGIN}/other?q=1`)).toBe(
      `${SITE_ORIGIN}/editorial/story`,
    );
  });

  it("does not allow an external path to become canonical", () => {
    expect(canonicalUrl("//example.com/other")).toBe(`${SITE_ORIGIN}/`);
  });
});
