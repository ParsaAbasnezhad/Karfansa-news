/** Strip tags/scripts and keep plain text safe for CMS fields. */
export function sanitizePlainText(value: string): string {
  return value
    .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?>[\s\S]*?<\/style>/gi, "")
    .replace(/<[^>]+>/g, "")
    .replace(/javascript:/gi, "")
    .trim();
}

/** Only public site paths and fully parsed HTTP(S) URLs may become links. */
export function isSafeHref(url: string): boolean {
  const value = url.trim();
  if (!value || value.includes("\\")) return false;
  for (let index = 0; index < value.length; index += 1) {
    const code = value.charCodeAt(index);
    if (code < 32 || code === 127) return false;
  }
  if (value.startsWith("/") && !value.startsWith("//")) return true;
  if (!/^https?:\/\//i.test(value)) return false;
  try {
    const parsed = new URL(value);
    return Boolean(parsed.hostname) && !parsed.username && !parsed.password;
  } catch {
    return false;
  }
}
