import { describe, expect, it } from "vitest";

import {
  normalizeIdentifier,
  safeRedirect,
  validEmail,
  validMobile,
  validatePasswordPair,
} from "@/features/auth/validation";

describe("auth input handling", () => {
  it("normalizes Iranian mobile digits and email case", () => {
    expect(normalizeIdentifier(" ۰۹۱۲ ۳۴۵ ۶۷۸۹ ")).toBe("+989123456789");
    expect(normalizeIdentifier("00989123456789")).toBe("+989123456789");
    expect(normalizeIdentifier(" USER@Example.COM ")).toBe("user@example.com");
    expect(validMobile("+989123456789")).toBe(true);
    expect(validMobile("+981234")).toBe(false);
    expect(validEmail("user@example.com")).toBe(true);
    expect(validEmail("user@")).toBe(false);
  });

  it("rejects mismatched passwords and unsafe redirects", () => {
    expect(validatePasswordPair("password123", "different123")).toBeTruthy();
    expect(validatePasswordPair("password123", "password123")).toBeUndefined();
    expect(safeRedirect("/account/security?tab=profile")).toBe("/account/security?tab=profile");
    expect(safeRedirect("//evil.example/path")).toBe("/");
    expect(safeRedirect("https://evil.example/path")).toBe("/");
    expect(safeRedirect("/\\evil.example")).toBe("/");
  });
});
