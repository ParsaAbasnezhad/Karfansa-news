import { useEffect } from "react";
import type { EditorialDetail } from "../types/editorial";

export function useEditorialStructuredData(item?: EditorialDetail) {
  useEffect(() => {
    if (!item) return;
    const canonical = `${window.location.origin}/editorial/${encodeURIComponent(item.slug)}`;
    const image = item.featured_image_url
      ? new URL(item.featured_image_url, window.location.origin).href
      : undefined;
    const graph = [
      {
        "@type": "NewsArticle",
        headline: item.title,
        description: item.seo_description || item.summary,
        mainEntityOfPage: canonical,
        datePublished: item.published_at,
        dateModified: item.updated_at,
        ...(image ? { image: [image] } : {}),
        ...(item.author_name ? { author: { "@type": "Person", name: item.author_name } } : {}),
        publisher: { "@type": "Organization", name: "کارفنسا" },
        ...(item.category ? { articleSection: item.category.name } : {}),
        ...(item.tags.length > 0 ? { keywords: item.tags.join(", ") } : {}),
      },
      {
        "@type": "BreadcrumbList",
        itemListElement: [
          { "@type": "ListItem", position: 1, name: "صفحه اصلی", item: window.location.origin },
          {
            "@type": "ListItem",
            position: 2,
            name: "اخبار اختصاصی کارفنسا",
            item: `${window.location.origin}/editorial`,
          },
          { "@type": "ListItem", position: 3, name: item.title, item: canonical },
        ],
      },
    ];
    const script = document.createElement("script");
    script.type = "application/ld+json";
    script.dataset.editorialStructuredData = "true";
    script.textContent = JSON.stringify({
      "@context": "https://schema.org",
      "@graph": graph,
    }).replace(/</g, "\\u003c");
    document.head.appendChild(script);
    return () => script.remove();
  }, [item]);
}
