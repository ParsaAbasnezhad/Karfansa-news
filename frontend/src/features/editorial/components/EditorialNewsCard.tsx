import { Link } from "react-router";
import { formatShortDate } from "@/lib/format";
import { EditorialImage } from "./EditorialImage";
import type { EditorialArticle } from "../types/editorial";

export function EditorialMeta({ article }: { article: EditorialArticle }) {
  return (
    <p className="kfe-meta">
      {article.category ? (
        <Link to={`/editorial/category/${encodeURIComponent(article.category.slug)}`}>
          {article.category.name}
        </Link>
      ) : null}
      {article.published_at ? (
        <time dateTime={article.published_at}>{formatShortDate(article.published_at)}</time>
      ) : null}
    </p>
  );
}

export function EditorialNewsCard({
  article,
  compact = false,
}: {
  article: EditorialArticle;
  compact?: boolean;
}) {
  const url = `/editorial/${article.slug}`;
  return (
    <article className={`kfe-card${compact ? " kfe-card-compact" : ""}`}>
      <Link className="kfe-card-image-link" to={url} tabIndex={-1} aria-hidden="true">
        <EditorialImage
          src={article.featured_image_url}
          srcSet={article.featured_image_srcset}
          alt=""
          width={article.featured_image_width}
          height={article.featured_image_height}
        />
      </Link>
      <div className="kfe-card-copy">
        <span className="kfe-exclusive">اختصاصی کارفنسا</span>
        <h3>
          <Link to={url}>{article.title}</Link>
        </h3>
        {!compact && article.summary ? <p className="kfe-card-summary">{article.summary}</p> : null}
        <EditorialMeta article={article} />
      </div>
    </article>
  );
}

export function EditorialNewsGrid({ articles }: { articles: EditorialArticle[] }) {
  return (
    <div className="kfe-grid">
      {articles.map((article) => (
        <EditorialNewsCard key={article.id} article={article} />
      ))}
    </div>
  );
}
