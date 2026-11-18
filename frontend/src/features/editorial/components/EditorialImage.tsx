import { useState } from "react";
import { Icon } from "@/components/ui/Icon";

interface EditorialImageProps {
  src: string;
  srcSet?: string;
  alt: string;
  width?: number | null;
  height?: number | null;
  priority?: boolean;
  className?: string;
  sizes?: string;
}

export function EditorialImage({
  src,
  srcSet,
  alt,
  width,
  height,
  priority = false,
  className = "",
  sizes = "(max-width: 640px) 100vw, 50vw",
}: EditorialImageProps) {
  const [failedSrc, setFailedSrc] = useState("");
  if (!src || src === failedSrc) {
    return (
      <span className={`kfe-image kfe-image-fallback ${className}`} aria-hidden="true">
        <Icon name="news" />
      </span>
    );
  }
  return (
    <img
      className={`kfe-image ${className}`}
      src={src}
      srcSet={srcSet || undefined}
      alt={alt}
      width={width || 1200}
      height={height || 675}
      sizes={sizes}
      loading={priority ? "eager" : "lazy"}
      decoding="async"
      fetchPriority={priority ? "high" : "auto"}
      onError={() => setFailedSrc(src)}
    />
  );
}
