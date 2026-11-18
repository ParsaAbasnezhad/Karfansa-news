import { Link } from "react-router";
import { Icon } from "@/components/ui/Icon";
import { EditorialImage } from "./EditorialImage";
import { EditorialMeta, EditorialNewsCard } from "./EditorialNewsCard";
import type { EditorialArticle } from "../types/editorial";

export function EditorialHero({
  featured,
  secondary,
  headingLevel = "h1",
}: {
  featured: EditorialArticle;
  secondary: EditorialArticle[];
  headingLevel?: "h1" | "h2";
}) {
  const Heading = headingLevel;
  return (
    <section className="kfe-hero" aria-labelledby="kfe-hero-title">
      <div className="kfe-section-heading kfe-hero-heading">
        <div>
          <span className="kfe-overline">گزارش‌ها و تحلیل‌های تحریریه</span>
          <Heading id="kfe-hero-title">اخبار اختصاصی کارفنسا</Heading>
        </div>
        <Link className="kfe-more" to="/editorial">
          مشاهده همه اخبار اختصاصی <Icon name="arrow" />
        </Link>
      </div>
      <div className="kfe-hero-grid">
        <article className="kfe-lead">
          <Link
            className="kfe-lead-image-link"
            to={`/editorial/${featured.slug}`}
            tabIndex={-1}
            aria-hidden="true"
          >
            <EditorialImage
              src={featured.featured_image_url}
              srcSet={featured.featured_image_srcset}
              alt=""
              width={featured.featured_image_width}
              height={featured.featured_image_height}
              priority
              sizes="(max-width: 900px) 100vw, 65vw"
            />
          </Link>
          <div className="kfe-lead-copy">
            <span className="kfe-exclusive">اختصاصی کارفنسا</span>
            <h2>
              <Link to={`/editorial/${featured.slug}`}>{featured.title}</Link>
            </h2>
            {featured.summary ? <p className="kfe-lead-summary">{featured.summary}</p> : null}
            <EditorialMeta article={featured} />
          </div>
        </article>
        {secondary.length > 0 ? (
          <div className="kfe-hero-rail" aria-label="دیگر خبرهای مهم تحریریه">
            {secondary.slice(0, 3).map((article) => (
              <EditorialNewsCard key={article.id} article={article} compact />
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}
