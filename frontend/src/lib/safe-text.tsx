import type { ReactNode } from "react";

import { sanitizePlainText } from "./safe-text-utils";

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
