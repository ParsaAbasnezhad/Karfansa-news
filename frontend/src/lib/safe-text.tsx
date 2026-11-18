import type { ReactNode } from "react";

/** Strip tags/scripts and keep plain text safe for CMS fields. */
export function sanitizePlainText(value: string): string {
  return value
    .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, "")
    .replace(/<style[\s\S]*?>[\s\S]*?<\/style>/gi, "")
    .replace(/<[^>]+>/g, "")
    .replace(/javascript:/gi, "")
    .trim();
}

export function SafeText({
  value,
  className,
  as: Tag = "p",
}: {
  value: string;
  className?: string;
  as?: "p" | "span" | "div";
}): ReactNode {
  const text = sanitizePlainText(value);
  if (!text) return null;
  return <Tag className={className}>{text}</Tag>;
}

export function SafeMultiline({ value, className }: { value: string; className?: string }) {
  const text = sanitizePlainText(value);
  if (!text) return null;
  return (
    <div className={className}>
      {text.split(/\n+/).map((paragraph, index) => (
        <p key={`${index}-${paragraph.slice(0, 12)}`}>{paragraph}</p>
      ))}
    </div>
  );
}

export function isSafeHref(url: string): boolean {
  const value = url.trim();
  if (!value) return false;
  if (value.startsWith("/") && !value.startsWith("//")) return true;
  return /^https?:\/\//i.test(value);
}
