import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router";

import { Icon } from "@/components/ui/Icon";
import { newsErrorMessage, publishedStamp } from "@/features/news/api/messages";
import { NewsCard } from "@/features/news/components/NewsCard";
import { NewsImage } from "@/features/news/components/NewsImage";
import { NewsIntro } from "@/features/news/components/NewsIntro";
import { NewsSkeleton, NewsState } from "@/features/news/components/NewsState";
import { useHeadlines, useNewsList } from "@/features/news/hooks/use-news";
import type { NewsItem, NewsOrdering } from "@/features/news/types/news";
import { usePageMeta } from "@/hooks/use-page-meta";
import { formatNumber, formatShortDate } from "@/lib/format";

import "../news.css";

function readOrdering(value: string | null): NewsOrdering {
  return value === "published_at" ? "published_at" : "-published_at";
}

function readPage(value: string | null): number {
  const page = Number(value ?? "1");
  return Number.isInteger(page) && page > 0 ? page : 1;
}

function StoryMeta({ item }: { item: NewsItem }) {
  const stamp = publishedStamp(item.published_at, item.fetched_at);
  return (
    <p className="news-story-meta">
      <span>{item.source_name}</span>
      <time dateTime={stamp}>{formatShortDate(stamp)}</time>
      {item.topic ? <span>{item.topic}</span> : null}
    </p>
  );
}

function NewsSearchForm({
  initialQuery,
  onSearch,
}: {
  initialQuery: string;
  onSearch: (value: string) => void;
}) {
  const [searchInput, setSearchInput] = useState(initialQuery);

  const search = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSearch(searchInput.trim());
  };

  return (
    <form className="news-search" onSubmit={search} role="search">
      <Icon name="search" />
      <label className="sr-only" htmlFor="news-search">
        جست‌وجو در اخبار
      </label>
      <input
        id="news-search"
        type="search"
        value={searchInput}
        onChange={(event) => setSearchInput(event.target.value)}
        placeholder="جست‌وجو در عنوان و خلاصه خبرها"
      />
      <button type="submit">جست‌وجو</button>
    </form>
  );
}

export function NewsListPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const topic = searchParams.get("topic") ?? "";
  const query = searchParams.get("q") ?? "";
  const page = readPage(searchParams.get("page"));
  const ordering = readOrdering(searchParams.get("ordering"));
  const news = useNewsList({ topic, q: query, page, pageSize: 12, ordering });
  const headlines = useHeadlines();
  const showDesk = !topic && !query && page === 1;

  usePageMeta(
    topic ? `${topic} | کارفنسا نیوز` : "آخرین اخبار اقتصاد و تجارت | کارفنسا نیوز",
    topic
      ? `آخرین خبرهای ${topic} از منابع خبری، همراه با نام منبع و زمان انتشار.`
      : "آخرین خبرهای اقتصادی، تجاری و صنعتی، همراه با نام منبع و زمان انتشار.",
    {
      canonicalPath: "/news",
      robots: topic || query || page > 1 || ordering !== "-published_at" ? "noindex,follow" : "index,follow",
    },
  );

  const replaceParams = (next: {
    topic?: string;
    q?: string;
    page?: number;
    ordering?: NewsOrdering;
  }) => {
    const params = new URLSearchParams();
    const nextTopic = next.topic ?? topic;
    const nextQuery = next.q ?? query;
    const nextPage = next.page ?? page;
    const nextOrdering = next.ordering ?? ordering;
    if (nextTopic) params.set("topic", nextTopic);
    if (nextQuery) params.set("q", nextQuery);
    if (nextPage > 1) params.set("page", String(nextPage));
    if (nextOrdering !== "-published_at") params.set("ordering", nextOrdering);
    setSearchParams(params);
  };

  const featured = headlines.data?.featured ?? null;
  const highlights = (headlines.data?.highlights ?? []).filter((item) => item.id !== featured?.id);
  const updatedAt = news.data?.updated_at ?? headlines.data?.updated_at ?? null;
  const topics = news.data?.topics ?? [];

  return (
    <section className="news-page" aria-labelledby="news-title">
      <NewsIntro
        titleId="news-title"
        eyebrow="کارفنسا نیوز"
        title="اخبار تجارت و اقتصاد"
        description="گزیدهٔ خبرهای اقتصادی، تجاری و صنعتی که پس از دریافت از منابع و بررسی موضوعی منتشر می‌شوند."
        updatedAt={updatedAt}
        refreshing={news.isFetching || headlines.isFetching}
        failed={news.isError && !news.data}
        count={news.data?.count ?? null}
      />

      {showDesk && headlines.isPending ? (
        <div className="news-feature-solo" aria-label="در حال دریافت خبر شاخص">
          <span className="skel news-skel-hero" />
          <span className="skel news-skel-title" />
          <span className="skel news-skel-line" />
        </div>
      ) : null}

      {showDesk && featured ? (
        <article className="news-feature news-feature-solo">
          <div className="news-feature-copy">
            <span className="news-kicker">{featured.topic || "خبر شاخص"}</span>
            <h2>
              <Link to={`/news/${featured.id}`}>{featured.title}</Link>
            </h2>
            {featured.summary ? <p>{featured.summary}</p> : null}
            <StoryMeta item={featured} />
            <Link className="news-read-link" to={`/news/${featured.id}`}>
              مشاهده جزئیات
              <Icon name="arrow" />
            </Link>
          </div>
          <Link
            className="news-feature-media"
            to={`/news/${featured.id}`}
            tabIndex={-1}
            aria-hidden="true"
          >
            <NewsImage className="news-cover" src={featured.image_url} alt="" priority />
          </Link>
        </article>
      ) : null}

      {showDesk && highlights.length > 0 ? (
        <section className="news-section" aria-labelledby="highlights-title">
          <div className="news-section-head">
            <h2 id="highlights-title">اخبار مهم و منتخب</h2>
          </div>
          <div className="news-rail">
            {highlights.slice(0, 3).map((item) => (
              <article className="news-rail-card" key={item.id}>
                <Link to={`/news/${item.id}`}>
                  <NewsImage src={item.image_url} alt="" />
                  <span className="news-kicker">{item.topic}</span>
                  <h3>{item.title}</h3>
                </Link>
                {item.summary ? <p className="news-summary">{item.summary}</p> : null}
                <StoryMeta item={item} />
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <div className="news-toolbar">
        <NewsSearchForm
          key={query}
          initialQuery={query}
          onSearch={(value) => replaceParams({ q: value, page: 1 })}
        />
        <label className="news-sort">
          <span className="sr-only" id="news-sort-label">
            مرتب‌سازی بر اساس تاریخ انتشار
          </span>
          <select
            aria-labelledby="news-sort-label"
            value={ordering}
            onChange={(event) =>
              replaceParams({ ordering: readOrdering(event.target.value), page: 1 })
            }
          >
            <option value="-published_at">جدیدترین</option>
            <option value="published_at">قدیمی‌ترین</option>
          </select>
        </label>
      </div>

      <nav className="news-topics" aria-label="دسته‌بندی موضوعی اخبار">
        <button
          type="button"
          className={!topic ? "active" : ""}
          aria-pressed={!topic}
          onClick={() => replaceParams({ topic: "", page: 1 })}
        >
          همه
        </button>
        {topics.map((item) => (
          <button
            type="button"
            className={topic === item ? "active" : ""}
            aria-pressed={topic === item}
            key={item}
            onClick={() => replaceParams({ topic: item, page: 1 })}
          >
            {item}
          </button>
        ))}
      </nav>

      <section aria-labelledby="latest-feed-title">
        <div className="news-section-head">
          <h2 id="latest-feed-title">آخرین اخبار</h2>
        </div>

        {news.isError && !news.data ? (
          <NewsState
            error
            title="دریافت خبرها ممکن نشد"
            detail={newsErrorMessage(news.error)}
            onRetry={() => void news.refetch()}
          />
        ) : !news.data ? (
          <NewsSkeleton />
        ) : news.data.results.length === 0 ? (
          <NewsState
            title={query || topic ? "خبری با این فیلتر پیدا نشد" : "هنوز خبر تأییدشده‌ای نیست"}
            detail={
              query || topic
                ? "عبارت جست‌وجو یا موضوع دیگری را امتحان کنید."
                : "خبرهای مرتبط پس از دریافت از منابع و تأیید موضوعی اینجا نمایش داده می‌شوند."
            }
          />
        ) : (
          <>
            <div className="news-grid" aria-live="polite" aria-busy={news.isFetching}>
              {news.data.results.map((item) => (
                <NewsCard item={item} key={item.id} />
              ))}
            </div>
            {news.data.total_pages > 1 ? (
              <nav className="news-pagination" aria-label="صفحه‌بندی خبرها">
                <button
                  type="button"
                  disabled={page <= 1 || news.isFetching}
                  onClick={() => replaceParams({ page: page - 1 })}
                >
                  <Icon name="chevron-right" />
                  قبلی
                </button>
                <span>
                  صفحهٔ {formatNumber(news.data.page)} از {formatNumber(news.data.total_pages)}
                </span>
                <button
                  type="button"
                  disabled={page >= news.data.total_pages || news.isFetching}
                  onClick={() => replaceParams({ page: page + 1 })}
                >
                  بعدی
                  <Icon name="chevron-left" />
                </button>
              </nav>
            ) : null}
          </>
        )}
      </section>
    </section>
  );
}
