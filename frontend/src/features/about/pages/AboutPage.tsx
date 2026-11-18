import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { Link } from "react-router";

import { Icon } from "@/components/ui/Icon";
import { useAboutPage } from "@/features/about/hooks/use-pages";
import { useAboutStats } from "@/features/about/hooks/use-about-stats";
import { usePageMeta } from "@/hooks/use-page-meta";
import { formatNumber } from "@/lib/format";
import { isSafeHref, SafeMultiline, sanitizePlainText } from "@/lib/safe-text";

import "../about.css";

const TradeGlobe = lazy(() =>
  import("../TradeGlobe").then((module) => ({ default: module.TradeGlobe })),
);

function ActionLink({
  to,
  label,
  className,
  icon,
}: {
  to: string;
  label: string;
  className: string;
  icon: "arrow" | "mail";
}) {
  if (!label || !isSafeHref(to)) return null;
  if (to.startsWith("http")) {
    return (
      <a className={className} href={to} target="_blank" rel="noopener noreferrer">
        {label} <Icon name={icon} />
      </a>
    );
  }
  return (
    <Link className={className} to={to}>
      {label} <Icon name={icon} />
    </Link>
  );
}

export function AboutPage() {
  const pageQuery = useAboutPage();
  const { headlines, news } = useAboutStats();
  const page = pageQuery.data;

  usePageMeta(
    page?.seo_title || "درباره کارفنسا نیوز",
    page?.seo_description ||
      "کارفنسا نیوز خبرهای اقتصادی و تجاری را از منابع RSS می‌گیرد، موضوع‌شان را مشخص می‌کند و همان‌ها را منتشر می‌کند.",
    page?.hero_image ? { image: page.hero_image } : undefined,
  );

  if (pageQuery.isPending) {
    return (
      <div className="about-page" dir="rtl" aria-busy="true">
        <div className="about-loading" role="status">
          در حال بارگذاری صفحه درباره ما…
        </div>
      </div>
    );
  }

  if (pageQuery.isError || !page) {
    return (
      <div className="about-page" dir="rtl">
        <div className="about-error" role="alert">
          <p>محتوای صفحه درباره ما بارگذاری نشد.</p>
          <button type="button" className="about-button about-button-primary" onClick={() => void pageQuery.refetch()}>
            تلاش دوباره
          </button>
        </div>
      </div>
    );
  }

  const cmsStats = page.statistics;
  const liveStats = [
    {
      label: "خبرهای در دسترس",
      value: news.data?.count,
      pending: news.isPending,
      failed: news.isError,
    },
    {
      label: "موضوع‌های فعال",
      value: news.data?.topics.length,
      pending: news.isPending,
      failed: news.isError,
    },
    {
      label: "منابع فعال",
      value: headlines.data?.source_count,
      pending: headlines.isPending,
      failed: headlines.isError,
    },
  ];
  const purposeFeatures = page.features.filter((item) => item.kind === "purpose");
  const principleFeatures = page.features.filter((item) => item.kind === "principle");
  const showGlobe = page.show_globe;

  return (
    <div className="about-page" dir="rtl">
      <section className="about-hero" aria-labelledby="about-hero-title">
        <div className="about-hero-copy">
          {page.hero_kicker ? (
            <span className="about-kicker">
              <i />
              {sanitizePlainText(page.hero_kicker)}
            </span>
          ) : null}
          <h1 id="about-hero-title">{sanitizePlainText(page.title)}</h1>
          {page.subtitle ? <p className="about-hero-subtitle">{sanitizePlainText(page.subtitle)}</p> : null}
          <SafeMultiline value={page.intro} />
          <div className="about-hero-actions">
            <ActionLink
              className="about-button about-button-primary"
              to={page.primary_cta_url || "/news"}
              label={page.primary_cta_label || "خواندن اخبار"}
              icon="arrow"
            />
            <ActionLink
              className="about-button about-button-ghost"
              to={page.secondary_cta_url || "/contact"}
              label={page.secondary_cta_label || "نامه به تحریریه"}
              icon="mail"
            />
          </div>
        </div>
        {showGlobe ? (
          <div className="about-globe-wrap" aria-hidden="true">
            <div className="about-globe-halo" />
            <div className="about-globe-fallback">
              <span className="about-fallback-orbit orbit-one" />
              <span className="about-fallback-orbit orbit-two" />
              <span className="about-fallback-core">K</span>
            </div>
            <Suspense fallback={null}>
              <LazyGlobe />
            </Suspense>
          </div>
        ) : page.hero_image ? (
          <div className="about-hero-media">
            <img src={page.hero_image} alt="" loading="eager" decoding="async" />
          </div>
        ) : null}
      </section>

      <section className="about-stats" aria-label="آمار">
        {cmsStats.length > 0
          ? cmsStats.map((stat) => (
              <div className="about-stat" key={stat.id}>
                <strong>{sanitizePlainText(stat.value)}</strong>
                <span>{sanitizePlainText(stat.label)}</span>
              </div>
            ))
          : liveStats.map((stat) => (
              <Stat
                key={stat.label}
                label={stat.label}
                value={stat.value}
                pending={stat.pending}
                failed={stat.failed}
              />
            ))}
        <p className="about-stats-note">
          {cmsStats.length > 0
            ? "آمار از پنل مدیریت محتوا خوانده می‌شود."
            : "عددها از سرویس عمومی اخبار خوانده می‌شوند."}
        </p>
      </section>

      {(page.story_title || page.story_body) && (
        <section className="about-story" aria-labelledby="about-story-title">
          <div className="about-story-index">
            <span>۰۱ / روش کار</span>
            <i />
            <span>منبع ← موضوع ← انتشار</span>
          </div>
          <div className="about-story-copy">
            {page.story_eyebrow ? (
              <span className="about-eyebrow">{sanitizePlainText(page.story_eyebrow)}</span>
            ) : null}
            {page.story_title ? (
              <h2 id="about-story-title">{sanitizePlainText(page.story_title)}</h2>
            ) : null}
            <SafeMultiline value={page.story_body} />
          </div>
        </section>
      )}

      {(purposeFeatures.length > 0 || page.mission || page.vision) && (
        <section className="about-purpose" aria-labelledby="about-purpose-title">
          <div className="about-section-heading">
            <span className="about-eyebrow">تعهد صفحه</span>
            <h2 id="about-purpose-title">خواندن خبر باید به منبع برسد</h2>
          </div>
          <div className="about-purpose-grid">
            {purposeFeatures.length > 0
              ? purposeFeatures.map((feature) => (
                  <article className="about-purpose-card" key={feature.id}>
                    {feature.label ? (
                      <span className="about-card-label">{sanitizePlainText(feature.label)}</span>
                    ) : null}
                    <h3>{sanitizePlainText(feature.title)}</h3>
                    <SafeTextParagraph value={feature.body} />
                  </article>
                ))
              : (
                  <>
                    {page.mission ? (
                      <article className="about-purpose-card mission-card">
                        <span className="about-card-label">
                          {sanitizePlainText(page.mission_title || "مأموریت")}
                        </span>
                        <SafeTextParagraph value={page.mission} />
                        {page.mission_image ? (
                          <img className="about-mission-image" src={page.mission_image} alt="" loading="lazy" />
                        ) : null}
                      </article>
                    ) : null}
                    {page.vision ? (
                      <article className="about-purpose-card vision-card">
                        <span className="about-card-label">
                          {sanitizePlainText(page.vision_title || "چشم‌انداز")}
                        </span>
                        <SafeTextParagraph value={page.vision} />
                      </article>
                    ) : null}
                  </>
                )}
          </div>
        </section>
      )}

      {principleFeatures.length > 0 ? (
        <section className="about-principles" aria-labelledby="about-principles-title">
          <div className="about-principles-heading">
            <span className="about-eyebrow">{sanitizePlainText(page.values_title || "اصول")}</span>
            <h2 id="about-principles-title">سه قاعده برای همین پایگاه</h2>
          </div>
          <div className="about-principles-list">
            {principleFeatures.map((feature) => (
              <article key={feature.id}>
                <span>{sanitizePlainText(feature.label || String(feature.sort_order))}</span>
                <div>
                  <h3>{sanitizePlainText(feature.title)}</h3>
                  <SafeTextParagraph value={feature.body} />
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {page.team_members.length > 0 ? (
        <section className="about-team" aria-labelledby="about-team-title">
          <div className="about-section-heading">
            <span className="about-eyebrow">تیم</span>
            <h2 id="about-team-title">اعضای تحریریه</h2>
          </div>
          <div className="about-team-grid">
            {page.team_members.map((member) => (
              <article className="about-team-card" key={member.id}>
                {member.photo ? (
                  <img src={member.photo} alt="" loading="lazy" className="about-team-photo" />
                ) : (
                  <span className="about-team-photo about-team-photo-fallback" aria-hidden="true">
                    <Icon name="user" />
                  </span>
                )}
                <h3>{sanitizePlainText(member.name)}</h3>
                {member.role ? <p className="about-team-role">{sanitizePlainText(member.role)}</p> : null}
                <SafeTextParagraph value={member.bio} />
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {(page.cta_title || page.closing_text) && (
        <section className="about-cta" aria-labelledby="about-cta-title">
          <div>
            {page.cta_eyebrow ? (
              <span className="about-eyebrow">{sanitizePlainText(page.cta_eyebrow)}</span>
            ) : null}
            {page.cta_title ? (
              <h2 id="about-cta-title">{sanitizePlainText(page.cta_title)}</h2>
            ) : null}
            <SafeMultiline value={page.closing_text} />
          </div>
          <div className="about-cta-actions">
            <ActionLink
              className="about-button about-button-white"
              to="/"
              label="صفحهٔ اصلی"
              icon="arrow"
            />
            <ActionLink
              className="about-button about-button-outline"
              to="/contact"
              label="تماس"
              icon="mail"
            />
          </div>
        </section>
      )}
    </div>
  );
}

function SafeTextParagraph({ value }: { value: string }) {
  const text = sanitizePlainText(value);
  if (!text) return null;
  return <p>{text}</p>;
}

function Stat({
  label,
  value,
  pending,
  failed,
}: {
  label: string;
  value: number | undefined;
  pending: boolean;
  failed: boolean;
}) {
  const text = failed ? "—" : pending || value === undefined ? "…" : formatNumber(value);
  return (
    <div className="about-stat">
      <strong aria-label={failed ? `${label}: در دسترس نیست` : `${label}: ${text}`}>{text}</strong>
      <span>{label}</span>
    </div>
  );
}

function LazyGlobe() {
  const hostRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(
    () => typeof window !== "undefined" && !("IntersectionObserver" in window),
  );

  useEffect(() => {
    const host = hostRef.current;
    if (!host || !("IntersectionObserver" in window)) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: "120px" },
    );
    observer.observe(host);
    return () => observer.disconnect();
  }, []);

  return (
    <div className="about-globe-lazy" ref={hostRef}>
      {visible ? <TradeGlobe /> : null}
    </div>
  );
}
