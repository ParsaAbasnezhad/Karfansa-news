import { useState } from "react";
import { Link, useParams } from "react-router";
import { Icon } from "@/components/ui/Icon";
import { usePageMeta } from "@/hooks/use-page-meta";
import { formatNumber, formatShortDate } from "@/lib/format";
import { isSafeHref } from "@/lib/safe-text";
import { editorialErrorMessage } from "../api/messages";
import { EditorialImage } from "../components/EditorialImage";
import { EditorialNewsGrid } from "../components/EditorialNewsCard";
import { EditorialState } from "../components/EditorialState";
import { useEditorialDetail } from "../hooks/use-editorial";
import { useEditorialStructuredData } from "../hooks/use-editorial-structured-data";
import "../editorial.css";

export function EditorialDetailPage() {
  const { slug = "" } = useParams();
  const detail = useEditorialDetail(slug);
  const item = detail.data?.item;
  const [copied, setCopied] = useState(false);
  usePageMeta(
    item ? `${item.seo_title || item.title} | کارفنسا نیوز` : "خبر اختصاصی | کارفنسا نیوز",
    item?.seo_description || item?.summary || "خبر اختصاصی کارفنسا",
    {
      type: item ? "article" : "website",
      image: item?.featured_image_url
        ? new URL(item.featured_image_url, window.location.origin).href
        : undefined,
      publishedAt: item?.published_at,
      modifiedAt: item?.updated_at,
      author: item?.author_name,
    },
  );
  useEditorialStructuredData(item);

  const share = async () => {
    const url = window.location.href;
    if (navigator.share && item) {
      try {
        await navigator.share({ title: item.title, url });
      } catch {
        /* User cancelled. */
      }
      return;
    }
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 3000);
    } catch {
      setCopied(false);
    }
  };

  if (!slug)
    return (
      <div className="kfe kfe-detail">
        <EditorialState
          title="نشانی خبر معتبر نیست"
          detail="خبر مورد نظر را از فهرست اخبار اختصاصی انتخاب کنید."
        />
      </div>
    );
  if (detail.isError && !item)
    return (
      <div className="kfe kfe-detail">
        <EditorialState
          error
          title="خبر نمایش داده نشد"
          detail={editorialErrorMessage(detail.error)}
          onRetry={() => void detail.refetch()}
        />
        <Link className="kfe-back" to="/editorial">
          بازگشت به اخبار اختصاصی
        </Link>
      </div>
    );
  if (!item)
    return (
      <div
        className="kfe kfe-detail kfe-detail-loading"
        aria-busy="true"
        aria-label="در حال دریافت خبر"
      >
        <span className="kfe-skeleton-line" />
        <span className="kfe-skeleton-line" />
        <span className="kfe-skeleton-image" />
      </div>
    );

  const related = detail.data?.related?.filter((article) => article.id !== item.id) ?? [];
  const sourceUrl = isSafeHref(item.source_url) ? item.source_url : "";
  return (
    <div className="kfe kfe-detail" dir="rtl">
      <nav className="kfe-crumb" aria-label="مسیر صفحه">
        <Link to="/">صفحه اصلی</Link>
        <span aria-hidden="true">/</span>
        <Link to="/editorial">اخبار اختصاصی</Link>
        <span aria-hidden="true">/</span>
        <span aria-current="page">{item.title}</span>
      </nav>
      <article className="kfe-article">
        <header className="kfe-article-head">
          <span className="kfe-exclusive">اختصاصی کارفنسا</span>
          {item.category ? (
            <Link
              className="kfe-article-category"
              to={`/editorial?category=${encodeURIComponent(item.category.slug)}`}
            >
              {item.category.name}
            </Link>
          ) : null}
          <h1>{item.title}</h1>
          {item.summary ? <p className="kfe-article-summary">{item.summary}</p> : null}
          <div className="kfe-article-byline">
            {item.author_name ? <span>نویسنده: {item.author_name}</span> : null}
            <time dateTime={item.published_at}>انتشار: {formatShortDate(item.published_at)}</time>
            {item.updated_at && item.updated_at !== item.published_at ? (
              <time dateTime={item.updated_at}>ویرایش: {formatShortDate(item.updated_at)}</time>
            ) : null}
            <span>{formatNumber(item.reading_time)} دقیقه مطالعه</span>
          </div>
        </header>
        {item.featured_image_url ? (
          <figure className="kfe-article-cover">
            <EditorialImage
              src={item.featured_image_url}
              srcSet={item.featured_image_srcset}
              alt={item.title}
              width={item.featured_image_width}
              height={item.featured_image_height}
              priority
              sizes="(max-width: 900px) 100vw, 900px"
            />
          </figure>
        ) : null}
        <div className="kfe-reading-layout">
          <div className="kfe-article-body">
            <div className="kfe-rich-text" dangerouslySetInnerHTML={{ __html: item.content }} />
            {item.gallery.length > 0 ? (
              <section className="kfe-gallery" aria-labelledby="kfe-gallery-title">
                <h2 id="kfe-gallery-title">تصاویر خبر</h2>
                <div className="kfe-gallery-grid">
                  {item.gallery.map((image) => (
                    <figure key={image.id}>
                      <EditorialImage
                        src={image.image_url}
                        srcSet={image.image_srcset}
                        alt={image.alt_text || image.caption || item.title}
                        width={image.width}
                        height={image.height}
                      />
                      {image.caption ? <figcaption>{image.caption}</figcaption> : null}
                    </figure>
                  ))}
                </div>
              </section>
            ) : null}
            {sourceUrl ? (
              <p className="kfe-source">
                منبع اصلی:{" "}
                <a href={sourceUrl} target="_blank" rel="noopener noreferrer">
                  {item.source_name || sourceUrl}
                </a>
              </p>
            ) : null}
            {item.tags.length > 0 ? (
              <div className="kfe-tags" aria-label="برچسب‌ها">
                {item.tags.map((tag) => (
                  <span key={tag}>{tag}</span>
                ))}
              </div>
            ) : null}
            <div className="kfe-article-actions">
              <button type="button" onClick={() => void share()}>
                <Icon name="send" /> {copied ? "پیوند کپی شد" : "اشتراک‌گذاری خبر"}
              </button>
              <Link to="/editorial">بازگشت به اخبار اختصاصی</Link>
            </div>
          </div>
        </div>
      </article>
      {related.length > 0 ? (
        <section className="kfe-related" aria-labelledby="kfe-related-title">
          <div className="kfe-section-heading">
            <h2 id="kfe-related-title">اخبار مرتبط</h2>
            <Link className="kfe-more" to="/editorial">
              همه اخبار <Icon name="arrow" />
            </Link>
          </div>
          <EditorialNewsGrid articles={related} />
        </section>
      ) : null}
    </div>
  );
}
