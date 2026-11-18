export function latinDigits(value: string): string {
  return value.replace(/[۰-۹٠-٩]/g, (digit) =>
    String.fromCharCode(digit.charCodeAt(0) - (digit >= "۰" ? 1728 : 1584)),
  );
}

export function normalizeIdentifier(value: string): string {
  const trimmed = latinDigits(value.trim());
  if (trimmed.includes("@")) return trimmed.toLowerCase();
  const compact = trimmed.replace(/[\s()-]/g, "");
  if (/^09\d{9}$/.test(compact)) return `+98${compact.slice(1)}`;
  if (/^00989\d{9}$/.test(compact)) return `+${compact.slice(2)}`;
  if (/^989\d{9}$/.test(compact)) return `+${compact}`;
  return compact;
}

export function validEmail(value: string): boolean {
  return value.length <= 254 && /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value);
}

export function validMobile(value: string): boolean {
  return /^\+989\d{9}$/.test(normalizeIdentifier(value));
}

export function validatePasswordPair(password: string, confirmation: string): string | undefined {
  if (password.length < 8) return "رمز عبور باید دست‌کم ۸ نویسه باشد.";
  if (password !== confirmation) return "تکرار رمز عبور با رمز عبور یکسان نیست.";
  return undefined;
}

export function safeRedirect(value: string | null | undefined): string {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.includes("\\"))
    return "/";
  return value;
}
