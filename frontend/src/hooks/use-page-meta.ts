import { useEffect } from "react";

export const SITE_ORIGIN = "https://karfansa.news.ir";
export const SITE_NAME = "کارفنسا نیوز";

let lastSeoLocation: string | undefined;

interface PageMetaOptions {
  type?: "website" | "article" | undefined;
  image?: string | undefined;
  publishedAt?: string | undefined;
  modifiedAt?: string | undefined;
  author?: string | undefined;
  section?: string | undefined;
  canonicalPath?: string | undefined;
  canonicalUrl?: string | undefined;
  robots?: "index,follow" | "noindex,follow" | "noindex,nofollow";
}

function setMeta(key: string, value: string, attribute: "name" | "property" = "property") {
  const matches = document.querySelectorAll<HTMLMetaElement>(`meta[${attribute}="${key}"]`);
  const tag = matches[0] ?? document.createElement("meta");
  if (!matches.length) {
    tag.setAttribute(attribute, key);
    document.head.appendChild(tag);
  }
  tag.content = value;
  matches.forEach((duplicate, index) => {
    if (index > 0) duplicate.remove();
  });
}

function removeMeta(key: string, attribute: "name" | "property" = "property") {
  document.querySelectorAll(`meta[${attribute}="${key}"]`).forEach((tag) => tag.remove());
}

export function canonicalUrl(path: string, override?: string): string {
  if (override) {
    try {
      const url = new URL(override);
      if (url.protocol === "https:" && url.origin === SITE_ORIGIN && !url.search && !url.hash) {
        return url.href;
      }
    } catch {
      // Ignore an invalid API value and keep the public route's canonical URL.
    }
  }
  const route = new URL(path, SITE_ORIGIN);
  if (route.origin !== SITE_ORIGIN) return `${SITE_ORIGIN}/`;
  route.search = "";
  route.hash = "";
  return route.href;
}

function publicImageUrl(image: string): string | undefined {
  try {
    const url = new URL(image, SITE_ORIGIN);
    return url.protocol === "https:" ? url.href : undefined;
  } catch {
    return undefined;
  }
}

export function usePageMeta(title: string, description?: string, options?: PageMetaOptions): void {
  const image = options?.image;
  const type = options?.type ?? "website";
  const publishedAt = options?.publishedAt;
  const modifiedAt = options?.modifiedAt;
  const author = options?.author;
  const section = options?.section;
  const path = options?.canonicalPath;
  const override = options?.canonicalUrl;
  const privateRoute = /^\/(?:login|register|verify|forgot-password|reset-password|account|status)(?:\/|$)/.test(
    typeof window === "undefined" ? "" : window.location.pathname,
  );
  const robots = options?.robots ?? (privateRoute ? "noindex,nofollow" : "index,follow");

  useEffect(() => {
    const currentLocation = `${window.location.pathname}${window.location.search}`;
    if (lastSeoLocation && currentLocation !== lastSeoLocation) {
      document.getElementById("seo-jsonld")?.remove();
    }
    lastSeoLocation = currentLocation;
    document.title = title;
    document.documentElement.lang = "fa-IR";
    document.documentElement.dir = "rtl";

    const url = canonicalUrl(path ?? window.location.pathname, override);
    const canonicals = document.querySelectorAll<HTMLLinkElement>('link[rel="canonical"]');
    const canonical = canonicals[0] ?? document.createElement("link");
    if (!canonicals.length) {
      canonical.rel = "canonical";
      document.head.appendChild(canonical);
    }
    canonical.href = url;
    canonicals.forEach((duplicate, index) => {
      if (index > 0) duplicate.remove();
    });

    const summary = description?.trim() || title;
    setMeta("description", summary, "name");
    setMeta("robots", robots, "name");
    setMeta("googlebot", robots === "index,follow" ? "index,follow,max-image-preview:large" : robots, "name");
    setMeta("og:title", title);
    setMeta("og:description", summary);
    setMeta("og:type", type);
    setMeta("og:url", url);
    setMeta("og:locale", "fa_IR");
    setMeta("og:site_name", SITE_NAME);
    setMeta("twitter:title", title, "name");
    setMeta("twitter:description", summary, "name");
    const imageUrl = image ? publicImageUrl(image) : undefined;
    setMeta("twitter:card", imageUrl ? "summary_large_image" : "summary", "name");
    if (imageUrl) {
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
    if (type === "article" && section) setMeta("article:section", section);
    else removeMeta("article:section");
  }, [title, description, type, image, publishedAt, modifiedAt, author, section, path, override, robots]);
}
