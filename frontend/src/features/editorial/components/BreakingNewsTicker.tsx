import { Link } from "react-router";
import type { EditorialArticle } from "../types/editorial";

export function BreakingNewsTicker({ articles }: { articles: EditorialArticle[] }) {
  if (articles.length === 0) return null;
  return (
    <section className="kfe-breaking" aria-label="اخبار فوری اختصاصی کارفنسا">
      <span className="kfe-breaking-label">
        <i aria-hidden="true" /> فوری کارفنسا
      </span>
      <div className="kfe-breaking-items">
        {articles.slice(0, 5).map((article) => (
          <Link key={article.id} to={`/editorial/${article.slug}`}>
            {article.title}
          </Link>
        ))}
      </div>
    </section>
  );
}
