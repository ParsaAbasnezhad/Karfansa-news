import { useEffect } from "react";

interface PageMetaOptions {
  type?: "website" | "article";
  image?: string | undefined;
}

function setMeta(key: string, value: string, attribute: "name" | "property" = "property") {
  let tag = document.querySelector<HTMLMetaElement>(`meta[${attribute}="${key}"]`);
  if (!tag) {
    tag = document.createElement("meta");
    tag.setAttribute(attribute, key);
    document.head.appendChild(tag);
  }
  tag.content = value;
}

export function usePageMeta(title: string, description?: string, options?: PageMetaOptions): void {
  const image = options?.image;
  const type = options?.type ?? "website";

  useEffect(() => {
    document.title = title;
    const canonicalUrl = `${window.location.origin}${window.location.pathname}`;
    let canonical = document.querySelector<HTMLLinkElement>('link[rel="canonical"]');
    if (!canonical) {
      canonical = document.createElement("link");
      canonical.rel = "canonical";
      document.head.appendChild(canonical);
    }
    canonical.href = canonicalUrl;

    setMeta("description", description || title, "name");
    setMeta("og:title", title);
    setMeta("og:description", description || title);
    setMeta("og:type", type);
    setMeta("og:url", canonicalUrl);
    setMeta("og:locale", "fa_IR");
    setMeta("twitter:card", image ? "summary_large_image" : "summary", "name");
    if (image) setMeta("og:image", image);
    else document.querySelector('meta[property="og:image"]')?.remove();
  }, [title, description, type, image]);
}
