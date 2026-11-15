import { describe, expect, it } from "vitest";

import { formatNumber, formatShortDate } from "@/lib/format";

describe("format", () => {
  it("formats integers with the Persian locale", () => {
    expect(formatNumber(12).length).toBeGreaterThan(0);
    expect(formatNumber(0)).not.toBe("");
  });

  it("formats timestamps and rejects invalid values", () => {
    expect(formatShortDate("2026-01-02T08:30:00Z").length).toBeGreaterThan(4);
    expect(formatShortDate("")).toBe("");
    expect(formatShortDate("not-a-date")).toBe("");
    expect(formatShortDate(null)).toBe("");
  });
});
