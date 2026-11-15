import { useState } from "react";

import { Icon } from "@/components/ui/Icon";

interface NewsImageProps {
  src: string;
  alt: string;
  priority?: boolean;
  className?: string;
}

export function NewsImage({
  src,
  alt,
  priority = false,
  className = "news-card-media",
}: NewsImageProps) {
  const [failedSrc, setFailedSrc] = useState("");

  if (!src || failedSrc === src) {
    return (
      <span className={`${className} news-cover-fallback`} aria-hidden="true">
        <Icon name="news" />
      </span>
    );
  }

  return (
    <img
      className={className}
      src={src}
      alt={alt}
      width={640}
      height={360}
      loading={priority ? "eager" : "lazy"}
      decoding="async"
      fetchPriority={priority ? "high" : "auto"}
      onError={() => setFailedSrc(src)}
    />
  );
}
