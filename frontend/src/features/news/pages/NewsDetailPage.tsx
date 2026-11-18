import { Link, useParams } from "react-router";

import { Icon } from "@/components/ui/Icon";
import { newsErrorMessage, publishedStamp } from "@/features/news/api/messages";
import { NewsImage } from "@/features/news/components/NewsImage";
import { NewsState } from "@/features/news/components/NewsState";
import { useNewsDetail } from "@/features/news/hooks/use-news";
import { usePageMeta } from "@/hooks/use-page-meta";
import { formatShortDate } from "@/lib/format";
import { isSafeHref } from "@/lib/safe-text-utils";

import "../news.css";

export function NewsDetailPage() {
  const rawId = useParams().newsId;
  const newsId = Number(rawId);
  const valid = Number.isInteger(newsId) && newsId > 0;
  const detail = useNewsDetail(newsId, valid);
  const item = detail.data?.item;

  usePageMeta(
    item ? `${item.title} | کارفنسا نیوز` : "خبر | کارفنسا نیوز",
    item?.summary || "جزئیات خبر در کارفنسا نیوز",
    { type: item ? "article" : "website", image: item?.image_url },
  );

  if (!valid) {
    return (
      <section className="news-page news-detail">
        <NewsState title="نشانی خبر معتبر نیست" detail="از فهرست خبرها یک خبر را انتخاب کنید." />
      </section>
    );
  }

  if (detail.isError && !item) {
    return (
      <section className="news-page news-detail">
        <NewsState
          error
          title="خبر نمایش داده نشد"
          detail={newsErrorMessage(detail.error)}
          onRetry={() => void detail.refetch()}
        />
      </section>
    );
  }

  if (!item) {
    return (
      <section className="news-page news-detail" aria-label="در حال دریافت خبر" aria-busy="true">
        <span className="skel news-skel-title" />
        <span className="skel news-skel-line" />
        <span className="skel news-skel-hero" />
      </section>
    );
  }

  const stamp = publishedStamp(item.published_at, item.fetched_at);
  const related = detail.data?.related ?? [];

  return (
    <section className="news-page news-detail">
      <nav className="news-crumb" aria-label="مسیر صفحه">
        <Link to="/">صفحهٔ اصلی</Link>
        <span aria-hidden="true">/</span>
        <Link to="/news">خبرها</Link>
        {item.topic ? (
          <>
            <span aria-hidden="true">/</span>
            <Link to={`/news?topic=${encodeURIComponent(item.topic)}`}>{item.topic}</Link>
          </>
        ) : null}
      </nav>

      <article className="news-article">
        <header className="news-article-header">
          <p className="news-kicker">
            {item.topic || "اخبار اقتصادی"}
            {item.is_pinned ? <span className="news-pin">ویژه</span> : null}
          </p>
          <h1>{item.title}</h1>
          <div className="news-story-meta">
            <span>
              <Icon name="building" />
              {item.source_website && isSafeHref(item.source_website) ? (
                <a href={item.source_website} target="_blank" rel="noopener noreferrer">
                  {item.source_name}
                </a>
              ) : (
                item.source_name
              )}
            </span>
            <time dateTime={stamp}>
              <Icon name="clock" />
              {formatShortDate(stamp)}
            </time>
          </div>
        </header>

        {item.image_url ? (
          <NewsImage className="news-cover" src={item.image_url} alt="" priority />
        ) : null}

        <div className="news-article-body">
          {item.summary ? (
            <section aria-labelledby="summary-title">
              <h2 id="summary-title">خلاصهٔ خبر</h2>
              <p>{item.summary}</p>
            </section>
          ) : (
            <p>خلاصه‌ای برای این خبر در دسترس نیست. متن کامل را در وب‌سایت منبع بخوانید.</p>
          )}
        </div>

        <footer className="news-article-source">
          <p>
            این خبر از {item.source_name} دریافت شده است. برای مطالعهٔ متن کامل و جزئیات بیشتر به
            منبع اصلی مراجعه کنید.
          </p>
          {isSafeHref(item.original_url) ? (
            <a
              className="news-origin"
              href={item.original_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              مطالعه در {item.source_name}
              <Icon name="arrow" />
            </a>
          ) : null}
        </footer>
      </article>

      {related.length > 0 ? (
        <section className="news-section news-related" aria-labelledby="related-title">
          <div className="news-section-head">
            <h2 id="related-title">خبرهای مرتبط</h2>
            {item.topic ? (
              <Link to={`/news?topic=${encodeURIComponent(item.topic)}`}>
                بیشتر از {item.topic}
                <Icon name="arrow" />
              </Link>
            ) : null}
          </div>
          <div className="news-rail">
            {related.map((relatedItem) => {
              const relatedStamp = publishedStamp(relatedItem.published_at, relatedItem.fetched_at);
              return (
                <article className="news-rail-card" key={relatedItem.id}>
                  <Link className="news-rail-link" to={`/news/${relatedItem.id}`}>
                    <NewsImage src={relatedItem.image_url} alt="" />
                    <span className="news-kicker">{relatedItem.topic || "اخبار اقتصادی"}</span>
                    <h3>{relatedItem.title}</h3>
                  </Link>
                  {relatedItem.summary ? (
                    <p className="news-summary">{relatedItem.summary}</p>
                  ) : null}
                  <p className="news-story-meta">
                    <span>{relatedItem.source_name}</span>
                    <time dateTime={relatedStamp}>{formatShortDate(relatedStamp)}</time>
                  </p>
                </article>
              );
            })}
          </div>
        </section>
      ) : null}
    </section>
  );
}
