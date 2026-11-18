# Karfansa editorial news

The `editorial` Django app stores reporting written by the Karfansa team. It has its own articles, categories, tags, and images. RSS intake remains in the `news` app and continues to run on its existing schedule.

## Publishing in Django Admin

1. Sign in to `/admin/` with a staff account that has editorial article permissions.
2. Create categories and tags as needed, then add an editorial article. Upload a main image and optional gallery images. Add useful alt text for gallery images.
3. Write the title, summary, and article body with the rich-text toolbar. Save as **Draft** and use the **Preview** link on the saved article.
4. Send the article for review by changing its status to **Pending review** or using the bulk action.
5. An editor with `editorial.publish_editorialarticle` may publish or archive it, set a future publication time, and mark it featured, breaking, or pinned.

Only articles with status **Published** and `published_at` at or before the current time appear in public API responses, the homepage, and the sitemap. The admin preview requires staff access and never uses a public detail endpoint.

The schema is introduced by `backend/apps/editorial/migrations/0001_initial.py`. The development Compose backend runs `migrate --noinput` at startup. For a separately deployed backend, apply migrations with `python manage.py migrate` before serving requests.

## Homepage priority

The main editorial story is selected by `is_pinned` first, then descending `priority`, then newest `published_at`. The remaining stories fill the smaller hero cards in that order. The editorial hero, breaking strip, and latest editorial stories appear before RSS news. When no editorial article is public, the hero displays an empty state and the RSS section remains independent.

## Public endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /api/v1/editorial/` | Paginated list with `category`, `q`, `ordering`, `page`, and `page_size` |
| `GET /api/v1/editorial/featured/` | Main and secondary stories ordered by editorial priority |
| `GET /api/v1/editorial/latest/` | Most recently published stories |
| `GET /api/v1/editorial/categories/` | Categories with public stories |
| `GET /api/v1/editorial/{slug}/` | Public article and related stories |
| `GET /sitemap.xml` | Public editorial page URLs |

Uploaded images live in the existing Docker media volume. Uploading an image also generates WebP variants up to 480, 960, and 1600 pixels wide; the API returns `srcset` values and original image dimensions for responsive loading. The Vite development proxy and production Nginx configuration expose them under `/media/`. Keep that volume mounted when deploying the production frontend. No sample editorial content is loaded into the main database.

## SEO deployment note

The React pages update the title, description, canonical link, social metadata, and NewsArticle structured data after loading the article API response. The current Vite application is client rendered. Social crawlers that do not execute JavaScript may not see per-article metadata; server rendering or prerendering is required for guaranteed link previews.
