# Karfansa News: search architecture and launch guide

Production origin: `https://karfansa.news.ir` · Language: Persian (`fa-IR`) · Direction: RTL.

## Architecture decision and audit

The previous production stack served Vite's `index.html` for every React route. Its first response contained a loader and a generic title; article content, canonical links, social metadata, and JSON-LD appeared only after JavaScript and API calls. This made bot rendering and social previews depend on client execution. Public item paths could also return the SPA shell with HTTP 200 for unpublished or missing records. The old sitemap covered only a capped editorial slice and there was no current News sitemap or canonical-domain robots endpoint.

Full React SSR would require a Node rendering service and server/client data coordination. Build-time SSG would miss new and edited articles until a rebuild. The chosen lightweight server-side prerender uses existing Django models and selectors for public initial HTML; React remains the interactive client. Production Nginx sends `/`, `/news`, `/editorial`, `/editorial/category/*`, `/editorial/*`, `/authors/*`, `/about`, and `/contact` to Django. Django emits semantic content and one canonical/metadata/JSON-LD set. The same Vite build provides stable `/assets/app.js` and `/assets/app.css` entry files; lazy chunks remain hashed. Named author profiles are simple Django pages. No Node server or framework migration is needed.

Public item requests now return 200 only for visible records, 404 for drafts/missing records, and 410 for explicitly archived editorial articles. Trailing slash variants redirect to the clean path. Filter/search query pages are `noindex,follow`; the legacy clean `?category=` URL redirects to the corresponding category path. RSS detail pages remain accessible for attribution and outbound navigation, but are `noindex,follow` and never carry Karfansa authorship markup.

## Search identity and structured data

- Homepage title: `کارفنسا نیوز | اخبار اقتصادی، تجارت و بازارهای جهانی`.
- Canonical URLs are rooted at `SEO_SITE_URL`, independent of the incoming Host header. The initial HTML sets `lang="fa-IR"`, RTL, one description, Open Graph tags, Twitter Card tags, a canonical link, and the existing official SVG logo/favicon.
- The initial HTML has one `#seo-jsonld` graph. It uses `WebSite` and `NewsMediaOrganization` for site identity; `CollectionPage`, `AboutPage`, `ContactPage`, `BreadcrumbList`, `NewsArticle`/`Article`, and `Person` appear only when supported by real records. Sourced editorial pieces use `Article` and preserve source attribution; only source-free editorial rows use `NewsArticle`. RSS rows never claim Karfansa authorship or publisher ownership.
- An author's `Person` and `/authors/{id}` profile require a nonempty real first and last name on the linked staff user. No biography, credential, address, or social account is inferred.
- Set `SEO_VERIFIED_SOCIAL_URLS` only after checking those official accounts. Empty means no `sameAs` claim.
- Article and category SEO title, description, social image, indexing preference, and strictly same-origin canonical override are managed in Django Admin. A stale override makes the page `noindex` until an editor repairs it. Admin shows approximate snippet previews and character counters. Google can still rewrite snippets.
- The separate advertising carousel visibly says `تبلیغات`, and its links use `rel="sponsored"`. RSS items expose their actual source name and original URL. The existing About and Contact CMS pages remain the public transparency pages; editorial staff should keep their source, correction, contact, and advertising disclosures current.

Large image previews are allowed with `max-image-preview:large`. Editors should upload original, relevant article images at least 1200 px wide and preferably a landscape crop; this is Google's current [Discover image guidance](https://developers.google.com/search/docs/appearance/google-discover). The app does not fabricate a generic article image when none exists. Neither markup nor image size guarantees Discover or Google News placement.

## Sitemaps and crawling

- `/robots.txt` names both sitemap endpoints and disallows administrative, API, and account routes. Public routes are crawlable.
- `/sitemap.xml` includes the homepage, populated news and editorial listings, About, Contact, active categories with public content, real named authors, and published self-canonical indexable editorial articles. It excludes empty listings, draft, future, archived, `noindex`, alternate-canonical, account, admin, and RSS detail URLs.
- Regular sitemaps split into `/sitemaps/static-{n}.xml` and `/sitemaps/editorial-{n}.xml` when needed. Chunk size is 10,000 URLs, below Google's [50,000 URL / 50 MB limit](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap). Entries use actual modification timestamps when available. Caches rotate on model saves/deletes and the admin bulk archive action.
- `/news-sitemap.xml` contains only original published editorial items from the most recent two days; sourced editorial and aggregated RSS rows are excluded. It splits at 1,000 articles. The [Google News sitemap rules](https://developers.google.com/search/docs/crawling-indexing/sitemaps/news-sitemap) also require publication name, language, publication date, and title, which the XML supplies.

The sitemap tells Google which URLs matter; it does not force crawl, indexing, a rich result, Sitelinks, a Knowledge Panel, or News inclusion.

## Production rollout

1. Keep the current PostgreSQL, Redis, media, static, and Docker volumes. Build the existing backend/frontend images and run the new editorial migration as part of the normal deployment process in [deployment.md](deployment.md).
2. In the private `.env.production`, set `SEO_SITE_URL=https://karfansa.news.ir`. Leave `SEO_GOOGLE_VERIFICATION` and `SEO_VERIFIED_SOCIAL_URLS` blank until ownership is confirmed. The production frontend Nginx must remain behind the trusted TLS proxy as documented.
3. Confirm a direct `view-source:` fetch of `/`, a published `/editorial/{slug}`, `/about`, and `/contact` contains visible content, a single canonical, and one `#seo-jsonld` without running JavaScript. Confirm a draft returns 404, an archived article 410, a slash variant 301, and an RSS detail has `noindex`.
4. Fetch `/robots.txt`, `/sitemap.xml`, `/news-sitemap.xml`, and any child `/sitemaps/*.xml` over the public HTTPS origin. The backend must be migrated before the frontend is switched to the new public HTML routes.
5. Monitor the Search Console Page indexing, Sitemaps, Search results, Discover (when available), and Core Web Vitals reports after rollout. Check actual mobile LCP, INP, and CLS from field data; local build success is not a field performance measurement.

## Exact Search Console registration

1. Sign in at [Google Search Console](https://search.google.com/search-console/) with the publisher-controlled Google account. Select **Add property** and choose **Domain**. Enter `karfansa.news.ir` with no scheme or slash. Google's [property guide](https://support.google.com/webmasters/answer/34592) confirms a subdomain can be a Domain property.
2. Copy the exact TXT value supplied by Google (it begins `google-site-verification=`). At the DNS provider, create the TXT record for the hostname Google specifies for `karfansa.news.ir`; use the provider's relative/absolute host syntax correctly. Wait for DNS propagation, then click **Verify**. Do not put a made-up value in the repository. Google's [verification guide](https://support.google.com/webmasters/answer/9008080) explains the DNS method.
3. If DNS access is unavailable, add a **URL-prefix** property for `https://karfansa.news.ir/`. Choose **HTML tag**, copy only the actual `content` value into private `SEO_GOOGLE_VERIFICATION`, deploy, check the token in the live homepage `<head>` source, then click **Verify**. HTML-tag verification applies to URL-prefix properties, not Domain properties. Keep the token in place while retaining verification.
4. In the verified property, open **Sitemaps**. Submit `https://karfansa.news.ir/sitemap.xml` and `https://karfansa.news.ir/news-sitemap.xml` separately. Check that both show **Success** and that child sitemap files load. See Google's [Sitemaps report instructions](https://support.google.com/webmasters/answer/7451001).
5. In **URL Inspection**, inspect the homepage and one current original editorial article. Review crawlability, user-declared and Google-selected canonical, rendered HTML, and indexing status. After a real fix or new publication, use **Test live URL** and **Request indexing** for a small number of individual URLs; use the sitemap for broad discovery. See [URL Inspection guidance](https://support.google.com/webmasters/answer/12482179).
6. Test a public original article at the [Rich Results Test](https://search.google.com/test/rich-results). Validate the JSON-LD against the visible author, date, image, and source details. Google's [Article documentation](https://developers.google.com/search/docs/appearance/structured-data/article) explains applicable fields; it does not promise an enhanced result.

## Editorial operations

Publish original stories with accurate title, timestamp, actual author when known, appropriate category, and a representative crawlable image. Keep the original `published_at` date when making routine edits; `updated_at` reflects real edits. Link citations and state any external source. Review existing About/Contact copy for current ownership, corrections, editorial policy, and contact details before claiming them publicly. Add verified social profiles only after confirming account control. Avoid entering fake authors, credentials, ratings, addresses, or reviews.
