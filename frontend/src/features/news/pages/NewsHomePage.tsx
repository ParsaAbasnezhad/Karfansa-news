import { useEffect } from "react";
import { Link } from "react-router";

import { prefetchPublicRoutesOnIdle } from "@/app/route-prefetch";
import { Icon } from "@/components/ui/Icon";
import { AdSlider } from "@/features/advertising/components/AdSlider";
import { EditorialHomeSections } from "@/features/editorial/components/EditorialHomeSections";
import { useEditorialFeatured, useEditorialLatest } from "@/features/editorial/hooks/use-editorial";
import { newsErrorMessage, publishedStamp } from "@/features/news/api/messages";
import { NewsImage } from "@/features/news/components/NewsImage";
import { NewsIntro } from "@/features/news/components/NewsIntro";
import { NewsState } from "@/features/news/components/NewsState";
import { useHeadlines } from "@/features/news/hooks/use-news";
import type { NewsItem } from "@/features/news/types/news";
import { usePageMeta } from "@/hooks/use-page-meta";
import { formatNumber, formatShortDate } from "@/lib/format";

import "../news.css";

function StoryMeta({ item }: { item: NewsItem }) {
  const stamp = publishedStamp(item.published_at, item.fetched_at);
  return (
    <p className="news-story-meta">
      {item.source_name ? <span>{item.source_name}</span> : null}
      <time dateTime={stamp}>{formatShortDate(stamp)}</time>
    </p>
  );
}

function RailStory({ item }: { item: NewsItem }) {
  return (
    <article className="news-rail-card">
      <Link className="news-rail-link" to={`/news/${item.id}`}>
        <NewsImage src={item.image_url} alt="" />
        <span className="news-kicker">{item.topic || "اخبار اقتصادی"}</span>
        <h3>{item.title}</h3>
      </Link>
      {item.summary ? <p className="news-summary">{item.summary}</p> : null}
      <StoryMeta item={item} />
    </article>
  );
}

function comparableUrl(value: string): string {
  if (!value) return "";
  try {
    const url = new URL(value);
    url.hash = "";
    url.pathname = url.pathname.replace(/\/+$/, "") || "/";
    for (const key of [...url.searchParams.keys()]) {
      if (key.startsWith("utm_") || key === "fbclid" || key === "gclid") {
        url.searchParams.delete(key);
      }
    }
    url.searchParams.sort();
    return url.toString();
  } catch {
    return value.trim();
  }
}

function comparableTitle(value: string): string {
  return value
    .normalize("NFKC")
    .toLocaleLowerCase("fa")
    .replace(/[\u064b-\u065f\u0670\u200c\u200d]/g, "")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim();
}

export function NewsHomePage() {
  useEffect(prefetchPublicRoutesOnIdle, []);

  const headlines = useHeadlines();
  const editorialFeatured = useEditorialFeatured();
  const editorialLatest = useEditorialLatest();
  usePageMeta(
    "اخبار اختصاصی اقتصاد و کسب‌وکار | کارفنسا نیوز",
    "خبرها و گزارش‌های اختصاصی تحریریهٔ کارفنسا، در کنار تازه‌های اقتصاد و بازار از منابع معتبر.",
  );

  const editorialArticles = [
    editorialFeatured.data?.featured,
    ...(editorialFeatured.data?.secondary ?? []),
    ...(editorialLatest.data?.results ?? []),
  ].filter((article) => article != null);
  const editorialUrls = new Set(
    editorialArticles.map((article) => comparableUrl(article.source_url)).filter(Boolean),
  );
  const editorialTitles = new Set(
    editorialArticles
      .map((article) => comparableTitle(article.title))
      .filter((title) => title.length >= 18),
  );
  const isEditorialDuplicate = (item: NewsItem) =>
    editorialUrls.has(comparableUrl(item.original_url)) ||
    editorialTitles.has(comparableTitle(item.title));

  const featured =
    [
      headlines.data?.featured,
      ...(headlines.data?.minis ?? []),
      ...(headlines.data?.highlights ?? []),
      ...(headlines.data?.latest ?? []),
      ...(headlines.data?.sections.flatMap((section) => section.items) ?? []),
    ].find((item) => item && !isEditorialDuplicate(item)) ?? null;
  const minis = (headlines.data?.minis ?? [])
    .filter((item) => item.id !== featured?.id && !isEditorialDuplicate(item))
    .slice(0, 3);
  const highlights = (headlines.data?.highlights ?? []).filter(
    (item) =>
      !isEditorialDuplicate(item) &&
      item.id !== featured?.id &&
      !minis.some((mini) => mini.id === item.id),
  );
  const latest = (headlines.data?.latest ?? [])
    .filter((item) => item.id !== featured?.id && !isEditorialDuplicate(item))
    .slice(0, 8);
  const sections = (headlines.data?.sections ?? []).map((section) => ({
    ...section,
    items: section.items.filter((item) => !isEditorialDuplicate(item)),
  }));
  const sidebar = [...(headlines.data?.pinned ?? []), ...highlights, ...minis, ...latest]
    .filter(
      (item, index, items) =>
        !isEditorialDuplicate(item) &&
        item.id !== featured?.id &&
        items.findIndex((other) => other.id === item.id) === index,
    )
    .slice(0, 6);

  return (
    <div className="news-page news-home">
      <EditorialHomeSections />

      <AdSlider />

      <NewsIntro
        titleId="home-title"
        headingLevel="h2"
        eyebrow="اخبار گردآوری‌شده"
        title="تازه‌های اقتصاد و کسب‌وکار"
        description="خبرهای منتخب از منابع معتبر، جدا از گزارش‌ها و خبرهای اختصاصی کارفنسا."
        updatedAt={headlines.data?.updated_at ?? null}
        refreshing={headlines.isFetching}
        failed={headlines.isError}
      />

      {headlines.isError && !headlines.data ? (
        <NewsState
          error
          title="خبرها بارگذاری نشدند"
          detail={newsErrorMessage(headlines.error)}
          onRetry={() => void headlines.refetch()}
        />
      ) : headlines.isPending ? (
        <div className="editorial-layout" aria-label="در حال دریافت خبرها" aria-busy="true">
          <div className="news-lead-skeleton">
            <span className="skel news-skel-hero" />
            <span className="skel news-skel-title" />
            <span className="skel news-skel-line" />
          </div>
          <div className="news-lead-skeleton">
            <span className="skel news-skel-title" />
            <span className="skel news-skel-line" />
            <span className="skel news-skel-media" />
          </div>
        </div>
      ) : !featured && latest.length === 0 ? (
        <NewsState
          title="هنوز خبری برای نمایش نیست"
          detail="پس از انتشار خبرهای تأییدشده، تازه‌ترین تیترها در این صفحه نمایش داده می‌شوند."
        />
      ) : (
        <>
          <div className="editorial-layout">
            <div className="editorial-main">
              {featured ? (
                <div className="news-lead">
                  <article className="news-feature">
                    <Link
                      className="news-feature-media"
                      to={`/news/${featured.id}`}
                      aria-label={featured.title}
                    >
                      <NewsImage className="news-cover" src={featured.image_url} alt="" />
                    </Link>
                    <div className="news-feature-copy">
                      <span className="news-kicker">{featured.topic || "خبر شاخص"}</span>
                      <h2>
                        <Link to={`/news/${featured.id}`}>{featured.title}</Link>
                      </h2>
                      {featured.summary ? <p className="news-summary">{featured.summary}</p> : null}
                      <StoryMeta item={featured} />
                    </div>
                  </article>
                  {minis.length > 0 ? (
                    <div className="news-minis" aria-label="خبرهای منتخب">
                      {minis.map((item) => (
                        <article className="news-mini" key={item.id}>
                          <Link to={`/news/${item.id}`}>
                            <NewsImage className="news-mini-image" src={item.image_url} alt="" />
                            <span className="news-kicker">{item.topic || "اخبار اقتصادی"}</span>
                            <h3>{item.title}</h3>
                          </Link>
                          {item.summary ? <p className="news-summary">{item.summary}</p> : null}
                          <StoryMeta item={item} />
                        </article>
                      ))}
                    </div>
                  ) : null}
                </div>
              ) : null}

              {highlights.length > 0 ? (
                <section className="news-section news-home-highlights" aria-labelledby="highlights-title">
                  <div className="news-section-head">
                    <h2 id="highlights-title">خبرهای مهم</h2>
                  </div>
                  <div className="news-rail">
                    {highlights.slice(0, 3).map((item) => (
                      <RailStory item={item} key={item.id} />
                    ))}
                  </div>
                </section>
              ) : null}

              <section className="news-section news-home-latest" aria-labelledby="latest-title">
                <div className="news-section-head">
                  <h2 id="latest-title">تازه‌ترین خبرها</h2>
                  <Link to="/news">
                    همهٔ خبرها <Icon name="arrow" />
                  </Link>
                </div>
                <ol className="news-latest">
                  {latest.map((item, index) => {
                    const stamp = publishedStamp(item.published_at, item.fetched_at);
                    return (
                      <li key={item.id}>
                        <span aria-hidden="true">{formatNumber(index + 1)}</span>
                        <div>
                          <Link to={`/news/${item.id}`}>{item.title}</Link>
                          <small>
                            {item.topic || "اخبار اقتصادی"} · {item.source_name} ·{" "}
                            {formatShortDate(stamp)}
                          </small>
                        </div>
                      </li>
                    );
                  })}
                </ol>
              </section>
            </div>

            {sidebar.length > 0 ? (
              <aside className="editorial-sidebar" aria-labelledby="sidebar-title">
                <div className="news-section-head">
                  <h2 id="sidebar-title">در کانون خبر</h2>
                </div>
                {sidebar.map((item, index) => (
                  <article className="sidebar-story" key={item.id}>
                    <span className="sidebar-number" aria-hidden="true">
                      {formatNumber(index + 1)}
                    </span>
                    <div>
                      <span className="news-kicker">{item.topic || "اخبار اقتصادی"}</span>
                      <h3>
                        <Link to={`/news/${item.id}`}>{item.title}</Link>
                      </h3>
                      <StoryMeta item={item} />
                    </div>
                  </article>
                ))}
              </aside>
            ) : null}
          </div>

          {sections.map((section, index) =>
            section.items.length > 0 ? (
              <section
                className="news-section news-category"
                key={section.topic}
                aria-labelledby={`topic-section-${index}`}
              >
                <div className="news-section-head">
                  <h2 id={`topic-section-${index}`}>{section.topic}</h2>
                  <Link to={`/news?topic=${encodeURIComponent(section.topic)}`}>
                    همهٔ خبرهای این موضوع <Icon name="arrow" />
                  </Link>
                </div>
                <div className="news-rail">
                  {section.items.map((item) => (
                    <RailStory item={item} key={item.id} />
                  ))}
                </div>
              </section>
            ) : null,
          )}
        </>
      )}
    </div>
  );
}
