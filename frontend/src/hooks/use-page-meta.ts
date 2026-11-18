import { useEffect } from "react";

interface PageMetaOptions {
  type?: "website" | "article";
  image?: string | undefined;
  publishedAt?: string | undefined;
  modifiedAt?: string | undefined;
  author?: string | undefined;
  canonicalSearch?: string | undefined;
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

function removeMeta(key: string, attribute: "name" | "property" = "property") {
  document.querySelector(`meta[${attribute}="${key}"]`)?.remove();
}

export function usePageMeta(title: string, description?: string, options?: PageMetaOptions): void {
  const image = options?.image;
  const type = options?.type ?? "website";
  const publishedAt = options?.publishedAt;
  const modifiedAt = options?.modifiedAt;
  const author = options?.author;
  const canonicalSearch = options?.canonicalSearch;

  useEffect(() => {
    document.title = title;
    const canonicalUrl = `${window.location.origin}${window.location.pathname}${canonicalSearch ? `?${canonicalSearch}` : ""}`;
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
    setMeta("og:site_name", "کارفنسا نیوز");
    setMeta("twitter:title", title, "name");
    setMeta("twitter:description", description || title, "name");
    setMeta("twitter:card", image ? "summary_large_image" : "summary", "name");
    if (image) {
      const imageUrl = new URL(image, window.location.origin).href;
      setMeta("og:image", imageUrl);
      setMeta("twitter:image", imageUrl, "name");
    } else {
      removeMeta("og:image");
      removeMeta("twitter:image", "name");
    }
    if (type === "article" && publishedAt) setMeta("article:published_time", publishedAt);
    else removeMeta("article:published_time");
    if (type === "article" && modifiedAt) setMeta("article:modified_time", modifiedAt);
    else removeMeta("article:modified_time");
    if (type === "article" && author) setMeta("article:author", author);
    else removeMeta("article:author");
  }, [title, description, type, image, publishedAt, modifiedAt, author, canonicalSearch]);
}
