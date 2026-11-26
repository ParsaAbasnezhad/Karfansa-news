import { useEffect } from "react";

import { canonicalUrl, SITE_NAME, SITE_ORIGIN } from "@/hooks/use-page-meta";
import type { EditorialDetail } from "../types/editorial";

const LOGO_URL = `${SITE_ORIGIN}/KARFANSA%20%E2%80%94%20Logo.svg`;

export function useEditorialStructuredData(item?: EditorialDetail) {
  useEffect(() => {
    if (!item) return;
    const existing = document.querySelector<HTMLScriptElement>("#seo-jsonld");
    if (item.seo_noindex) {
      existing?.remove();
      return;
    }

    const articleUrl = canonicalUrl(`/editorial/${encodeURIComponent(item.slug)}`, item.seo_canonical_url);
    const imagePath = item.seo_social_image_url || item.featured_image_url;
    const imageUrl = imagePath ? new URL(imagePath, SITE_ORIGIN).href : undefined;
    const article = {
      "@type": item.source_url || item.source_name ? "Article" : "NewsArticle",
      "@id": `${articleUrl}#article`,
      headline: item.title,
      description: item.seo_description || item.summary,
      mainEntityOfPage: { "@type": "WebPage", "@id": articleUrl },
      datePublished: item.published_at,
      dateModified: item.updated_at,
      inLanguage: "fa-IR",
      ...(imageUrl ? { image: [imageUrl] } : {}),
      ...(item.author_name
        ? {
            author: {
              "@type": "Person",
              name: item.author_name,
              ...(item.author_id ? { url: `${SITE_ORIGIN}/authors/${item.author_id}` } : {}),
            },
          }
        : {}),
      publisher: {
        "@type": "NewsMediaOrganization",
        "@id": `${SITE_ORIGIN}/#organization`,
        name: SITE_NAME,
        url: `${SITE_ORIGIN}/`,
        logo: { "@type": "ImageObject", url: LOGO_URL },
      },
      ...(item.category ? { articleSection: item.category.name } : {}),
      ...(item.tags.length ? { keywords: item.tags.join(", ") } : {}),
      ...(item.source_url ? { isBasedOn: item.source_url } : {}),
    };
    const graph = {
      "@context": "https://schema.org",
      "@graph": [
        article,
        {
          "@type": "BreadcrumbList",
          "@id": `${articleUrl}#breadcrumb`,
          itemListElement: [
            { "@type": "ListItem", position: 1, name: "صفحه اصلی", item: `${SITE_ORIGIN}/` },
            { "@type": "ListItem", position: 2, name: "اخبار اختصاصی", item: `${SITE_ORIGIN}/editorial` },
            { "@type": "ListItem", position: 3, name: item.title, item: articleUrl },
          ],
        },
      ],
    };

    const script = existing ?? document.createElement("script");
    script.id = "seo-jsonld";
    script.type = "application/ld+json";
    script.textContent = JSON.stringify(graph).replace(/</g, "\\u003c");
    if (!existing) document.head.appendChild(script);
    return () => script.remove();
  }, [item]);
}
