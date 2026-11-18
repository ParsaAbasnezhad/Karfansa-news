import { Link } from "react-router";
import { Icon } from "@/components/ui/Icon";
import { editorialErrorMessage } from "../api/messages";
import { BreakingNewsTicker } from "./BreakingNewsTicker";
import { EditorialHero } from "./EditorialHero";
import { EditorialNewsGrid } from "./EditorialNewsCard";
import { EditorialSkeleton, EditorialState } from "./EditorialState";
import { useEditorialFeatured, useEditorialLatest } from "../hooks/use-editorial";
import "../editorial.css";

export function EditorialHomeSections() {
  const featuredQuery = useEditorialFeatured();
  const latestQuery = useEditorialLatest();
  const featured = featuredQuery.data?.featured ?? null;
  const secondary = featuredQuery.data?.secondary ?? [];
  const latest = latestQuery.data?.results ?? [];
  const heroIds = new Set([featured?.id, ...secondary.map((article) => article.id)]);
  const latestDistinct = latest.filter((article) => !heroIds.has(article.id)).slice(0, 4);
  const breaking = latest.filter((article) => article.is_breaking);

  return (
    <div className="kfe kfe-home" dir="rtl">
      {featuredQuery.isPending ? (
        <section
          className="kfe-home-loading"
          aria-label="در حال دریافت اخبار اختصاصی"
          aria-busy="true"
        >
          <div className="kfe-section-heading">
            <h1>اخبار اختصاصی کارفنسا</h1>
          </div>
          <EditorialSkeleton count={3} />
        </section>
      ) : featuredQuery.isError && !featuredQuery.data ? (
        <section aria-labelledby="kfe-home-error-title">
          <div className="kfe-section-heading">
            <h1 id="kfe-home-error-title">اخبار اختصاصی کارفنسا</h1>
          </div>
          <EditorialState
            error
            title="اخبار اختصاصی بارگذاری نشد"
            detail={editorialErrorMessage(featuredQuery.error)}
            onRetry={() => void featuredQuery.refetch()}
          />
        </section>
      ) : featured ? (
        <EditorialHero featured={featured} secondary={secondary} />
      ) : (
        <section aria-labelledby="kfe-home-empty-title">
          <div className="kfe-section-heading">
            <h1 id="kfe-home-empty-title">اخبار اختصاصی کارفنسا</h1>
          </div>
          <EditorialState
            title="هنوز خبر اختصاصی منتشر نشده است"
            detail="گزارش‌های تیم تحریریه پس از انتشار در این بخش نمایش داده می‌شوند."
          />
        </section>
      )}

      <BreakingNewsTicker articles={breaking} />

      <section className="kfe-latest" aria-labelledby="kfe-latest-title">
        <div className="kfe-section-heading">
          <div>
            <span className="kfe-overline">از میز تحریریه</span>
            <h2 id="kfe-latest-title">تازه‌ترین اخبار اختصاصی</h2>
          </div>
          <Link className="kfe-more" to="/editorial">
            آرشیو تحریریه <Icon name="arrow" />
          </Link>
        </div>
        {latestQuery.isPending ? <EditorialSkeleton count={4} /> : null}
        {latestQuery.isError && !latestQuery.data ? (
          <EditorialState
            error
            title="تازه‌ترین اخبار دریافت نشد"
            detail={editorialErrorMessage(latestQuery.error)}
            onRetry={() => void latestQuery.refetch()}
          />
        ) : null}
        {latestDistinct.length > 0 ? <EditorialNewsGrid articles={latestDistinct} /> : null}
        {latestQuery.data && latestDistinct.length === 0 ? (
          <EditorialState
            title={featured ? "خبر تازهٔ دیگری منتشر نشده است" : "هنوز خبر تازه‌ای منتشر نشده است"}
            detail="گزارش‌های تازهٔ تیم تحریریه پس از انتشار در این بخش نمایش داده می‌شوند."
          />
        ) : null}
      </section>
    </div>
  );
}
