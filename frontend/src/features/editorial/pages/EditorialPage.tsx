import { useState, type FormEvent } from "react";
import { Link, useParams, useSearchParams } from "react-router";
import { Icon } from "@/components/ui/Icon";
import { usePageMeta } from "@/hooks/use-page-meta";
import { formatNumber } from "@/lib/format";
import { editorialErrorMessage } from "../api/messages";
import { EditorialHero } from "../components/EditorialHero";
import { EditorialNewsGrid } from "../components/EditorialNewsCard";
import { EditorialSkeleton, EditorialState } from "../components/EditorialState";
import {
  useEditorialCategories,
  useEditorialFeatured,
  useEditorialList,
} from "../hooks/use-editorial";
import type { EditorialOrdering } from "../types/editorial";
import "../editorial.css";

function validPage(value: string | null) {
  const page = Number(value);
  return Number.isInteger(page) && page > 0 ? page : 1;
}

function validOrdering(value: string | null): EditorialOrdering {
  return value === "published_at" || value === "priority" ? value : "-published_at";
}

function SearchForm({ query, onSearch }: { query: string; onSearch: (value: string) => void }) {
  const [value, setValue] = useState(query);
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSearch(value.trim());
  };
  return (
    <form className="kfe-search" role="search" onSubmit={submit}>
      <label className="sr-only" htmlFor="editorial-search">
        جست‌وجو در اخبار اختصاصی
      </label>
      <Icon name="search" />
      <input
        id="editorial-search"
        type="search"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="جست‌وجو در عنوان، خلاصه و متن خبر"
      />
      <button type="submit">جست‌وجو</button>
    </form>
  );
}

export function EditorialPage() {
  const { slug: categorySlug } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const category = categorySlug || searchParams.get("category") || "";
  const q = searchParams.get("q") ?? "";
  const ordering = validOrdering(searchParams.get("ordering"));
  const page = validPage(searchParams.get("page"));
  const list = useEditorialList({ category, q, ordering, page, pageSize: 12 });
  const categoriesQuery = useEditorialCategories();
  const featuredQuery = useEditorialFeatured();
  const showFeatured = page === 1 && !category && !q && ordering === "-published_at";
  const featured = showFeatured ? featuredQuery.data?.featured : null;
  const secondary = showFeatured ? (featuredQuery.data?.secondary ?? []) : [];
  const results = list.data?.results ?? [];
  const categories = categoriesQuery.data?.results ?? list.data?.categories ?? [];
  const activeCategory = categories.find((item) => item.slug === category);
  const categoryPath = category
    ? `/editorial/category/${encodeURIComponent(category)}`
    : "/editorial";
  const filteredView = Boolean(q || page > 1 || ordering !== "-published_at" || searchParams.has("category"));

  usePageMeta(
    activeCategory?.seo_title ||
      (activeCategory
        ? `${activeCategory.name} | کارفنسا نیوز`
        : "اخبار اختصاصی کارفنسا | کارفنسا نیوز"),
    activeCategory?.seo_description ||
      (activeCategory
        ? `تازه‌ترین گزارش‌ها و خبرهای اختصاصی ${activeCategory.name} از تحریریه کارفنسا نیوز.`
        : "آخرین گزارش‌ها، تحلیل‌ها و خبرهای اختصاصی تیم تحریریه کارفنسا در حوزه اقتصاد و کسب‌وکار."),
    {
      canonicalPath: categoryPath,
      canonicalUrl: activeCategory?.seo_canonical_url,
      image: activeCategory?.seo_social_image_url,
      robots:
        filteredView ||
        activeCategory?.seo_noindex ||
        (Boolean(category) && !activeCategory) ||
        list.data?.count === 0
          ? "noindex,follow"
          : "index,follow",
    },
  );

  const updateParams = (next: {
    q?: string;
    ordering?: EditorialOrdering;
    page?: number;
  }) => {
    const params = new URLSearchParams();
    const nextQuery = next.q ?? q;
    const nextOrdering = next.ordering ?? ordering;
    const nextPage = next.page ?? page;
    if (nextQuery) params.set("q", nextQuery);
    if (nextOrdering !== "-published_at") params.set("ordering", nextOrdering);
    if (nextPage > 1) params.set("page", String(nextPage));
    setSearchParams(params);
  };

  return (
    <div className="kfe kfe-page" dir="rtl">
      <nav className="kfe-crumb" aria-label="مسیر صفحه">
        <Link to="/">صفحه اصلی</Link>
        <span aria-hidden="true">/</span>
        {activeCategory ? (
          <>
            <Link to="/editorial">اخبار اختصاصی</Link>
            <span aria-hidden="true">/</span>
            <span aria-current="page">{activeCategory.name}</span>
          </>
        ) : (
          <span aria-current="page">اخبار اختصاصی</span>
        )}
      </nav>
      <header className="kfe-page-header">
        <span className="kfe-overline">میز تحریریه کارفنسا</span>
        <h1>{activeCategory ? activeCategory.name : "اخبار اختصاصی کارفنسا"}</h1>
        <p>
          {activeCategory
            ? activeCategory.seo_description || `خبرها و گزارش‌های اختصاصی ${activeCategory.name} از تحریریه کارفنسا نیوز.`
            : "روایت دقیق رویدادهای اقتصادی و کسب‌وکار، از تیم تحریریه کارفنسا."}
        </p>
      </header>

      {showFeatured && featured ? (
        <div className="kfe-list-featured">
          <EditorialHero featured={featured} secondary={secondary} headingLevel="h2" />
        </div>
      ) : null}

      <section className="kfe-list" aria-labelledby="kfe-list-title">
        <div className="kfe-section-heading">
          <div>
            <span className="kfe-overline">آرشیو تحریریه</span>
            <h2 id="kfe-list-title">تازه‌ترین اخبار</h2>
          </div>
          {list.data ? (
            <span className="kfe-count">{formatNumber(list.data.count)} خبر</span>
          ) : null}
        </div>
        <div className="kfe-toolbar">
          <SearchForm key={q} query={q} onSearch={(value) => updateParams({ q: value, page: 1 })} />
          <label className="kfe-sort">
            <span>مرتب‌سازی</span>
            <select
              value={ordering}
              onChange={(event) =>
                updateParams({ ordering: validOrdering(event.target.value), page: 1 })
              }
            >
              <option value="-published_at">جدیدترین</option>
              <option value="published_at">قدیمی‌ترین</option>
              <option value="priority">اولویت تحریریه</option>
            </select>
          </label>
        </div>
        <nav className="kfe-categories" aria-label="فیلتر دسته‌بندی اخبار اختصاصی">
          <Link
            to="/editorial"
            className={!category ? "active" : ""}
            aria-current={!category ? "page" : undefined}
          >
            همه
          </Link>
          {categories.map((item) => (
            <Link
              key={item.id}
              to={`/editorial/category/${encodeURIComponent(item.slug)}`}
              className={category === item.slug ? "active" : ""}
              aria-current={category === item.slug ? "page" : undefined}
            >
              {item.name}
            </Link>
          ))}
        </nav>
        {list.isError && !list.data ? (
          <EditorialState
            error
            title="اخبار اختصاصی دریافت نشد"
            detail={editorialErrorMessage(list.error)}
            onRetry={() => void list.refetch()}
          />
        ) : null}
        {!list.data && !list.isError ? <EditorialSkeleton count={6} /> : null}
        {list.data && results.length === 0 ? (
          <EditorialState
            title={
              q || category ? "خبری با این جست‌وجو پیدا نشد" : "هنوز خبر اختصاصی منتشر نشده است"
            }
            detail={
              q || category
                ? "عبارت جست‌وجو یا دسته‌بندی دیگری را امتحان کنید."
                : "نخستین گزارش‌های تحریریه پس از انتشار در اینجا نمایش داده می‌شوند."
            }
          />
        ) : null}
        {results.length > 0 ? (
          <div aria-live="polite" aria-busy={list.isFetching}>
            <EditorialNewsGrid articles={results} />
          </div>
        ) : null}
        {list.data && list.data.total_pages > 1 ? (
          <nav className="kfe-pagination" aria-label="صفحه‌بندی اخبار اختصاصی">
            <button
              type="button"
              disabled={page <= 1 || list.isFetching}
              onClick={() => updateParams({ page: page - 1 })}
            >
              قبلی
            </button>
            <span>
              صفحه {formatNumber(list.data.page)} از {formatNumber(list.data.total_pages)}
            </span>
            <button
              type="button"
              disabled={page >= list.data.total_pages || list.isFetching}
              onClick={() => updateParams({ page: page + 1 })}
            >
              بعدی
            </button>
          </nav>
        ) : null}
      </section>
    </div>
  );
}
