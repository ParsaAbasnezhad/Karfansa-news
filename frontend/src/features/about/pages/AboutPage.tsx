import { Link } from "react-router";

import { Icon } from "@/components/ui/Icon";
import { useAboutPage } from "@/features/about/hooks/use-pages";
import { useAboutStats } from "@/features/about/hooks/use-about-stats";
import { usePageMeta } from "@/hooks/use-page-meta";
import { formatNumber } from "@/lib/format";
import { SafeMultiline } from "@/lib/safe-text";
import { isSafeHref, sanitizePlainText } from "@/lib/safe-text-utils";

import "../about-page.css";

function ActionLink({ to, label, className }: { to: string; label: string; className: string }) {
  if (!label || !isSafeHref(to)) return null;
  if (to.startsWith("http")) {
    return (
      <a className={className} href={to} target="_blank" rel="noopener noreferrer">
        {label} <Icon name="arrow" />
      </a>
    );
  }
  return (
    <Link className={className} to={to}>
      {label} <Icon name="arrow" />
    </Link>
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
    <div className="ab-stat">
      <dd aria-label={failed ? `${label}: در دسترس نیست` : `${label}: ${text}`}>{text}</dd>
      <dt>{label}</dt>
    </div>
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
      <div className="ab" dir="rtl" aria-busy="true">
        <div className="ab-state" role="status">
          در حال بارگذاری صفحه درباره ما…
        </div>
      </div>
    );
  }

  if (pageQuery.isError || !page) {
    return (
      <div className="ab" dir="rtl">
        <div className="ab-state" role="alert">
          <p>محتوای صفحه درباره ما بارگذاری نشد.</p>
          <button type="button" className="ab-link" onClick={() => void pageQuery.refetch()}>
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

  return (
    <div className="ab" dir="rtl">
      <header className="ab-head">
        {page.hero_kicker ? (
          <span className="ab-kicker">{sanitizePlainText(page.hero_kicker)}</span>
        ) : null}
        <h1>{sanitizePlainText(page.title)}</h1>
        {page.subtitle ? <p className="ab-subtitle">{sanitizePlainText(page.subtitle)}</p> : null}
        <div className="ab-prose">
          <SafeMultiline value={page.intro} />
        </div>
        <div className="ab-actions">
          <ActionLink
            className="ab-button"
            to={page.primary_cta_url || "/news"}
            label={page.primary_cta_label || "خواندن اخبار"}
          />
          <ActionLink
            className="ab-link"
            to={page.secondary_cta_url || "/contact"}
            label={page.secondary_cta_label || "نامه به تحریریه"}
          />
        </div>
      </header>

      {page.hero_image ? (
        <figure className="ab-figure">
          <img src={page.hero_image} alt="" loading="eager" decoding="async" />
        </figure>
      ) : null}

      <dl className="ab-stats" aria-label="آمار">
        {cmsStats.length > 0
          ? cmsStats.map((stat) => (
              <div className="ab-stat" key={stat.id}>
                <dd>{sanitizePlainText(stat.value)}</dd>
                <dt>{sanitizePlainText(stat.label)}</dt>
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
      </dl>

      {(page.story_title || page.story_body) && (
        <section className="ab-row" aria-labelledby="ab-story">
          <h2 className="ab-label" id="ab-story">
            {sanitizePlainText(page.story_eyebrow || "روش کار")}
          </h2>
          <div className="ab-body">
            {page.story_title ? <h3>{sanitizePlainText(page.story_title)}</h3> : null}
            <div className="ab-prose">
              <SafeMultiline value={page.story_body} />
            </div>
          </div>
        </section>
      )}

      {(purposeFeatures.length > 0 || page.mission || page.vision) && (
        <section className="ab-row" aria-labelledby="ab-purpose">
          <h2 className="ab-label" id="ab-purpose">
            تعهد صفحه
          </h2>
          <div className="ab-body">
            <h3>خواندن خبر باید به منبع برسد</h3>
            <div className="ab-pairs">
              {purposeFeatures.length > 0 ? (
                purposeFeatures.map((feature) => (
                  <article key={feature.id}>
                    <h4>{sanitizePlainText(feature.title)}</h4>
                    <SafeTextParagraph value={feature.body} />
                  </article>
                ))
              ) : (
                <>
                  {page.mission ? (
                    <article>
                      <h4>{sanitizePlainText(page.mission_title || "مأموریت")}</h4>
                      <SafeTextParagraph value={page.mission} />
                    </article>
                  ) : null}
                  {page.vision ? (
                    <article>
                      <h4>{sanitizePlainText(page.vision_title || "چشم‌انداز")}</h4>
                      <SafeTextParagraph value={page.vision} />
                    </article>
                  ) : null}
                </>
              )}
            </div>
          </div>
        </section>
      )}

      {principleFeatures.length > 0 ? (
        <section className="ab-row" aria-labelledby="ab-principles">
          <h2 className="ab-label" id="ab-principles">
            {sanitizePlainText(page.values_title || "اصول")}
          </h2>
          <ol className="ab-body ab-principles">
            {principleFeatures.map((feature, index) => (
              <li key={feature.id}>
                <span aria-hidden="true">
                  {sanitizePlainText(feature.label || `۰${index + 1}`)}
                </span>
                <div>
                  <h4>{sanitizePlainText(feature.title)}</h4>
                  <SafeTextParagraph value={feature.body} />
                </div>
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      {page.team_members.length > 0 ? (
        <section className="ab-row" aria-labelledby="ab-team">
          <h2 className="ab-label" id="ab-team">
            تیم
          </h2>
          <div className="ab-body ab-team">
            {page.team_members.map((member) => (
              <article key={member.id}>
                {member.photo ? <img src={member.photo} alt="" loading="lazy" /> : null}
                <div>
                  <h4>{sanitizePlainText(member.name)}</h4>
                  {member.role ? <span>{sanitizePlainText(member.role)}</span> : null}
                  <SafeTextParagraph value={member.bio} />
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {(page.cta_title || page.closing_text) && (
        <section className="ab-row ab-closing" aria-labelledby="ab-closing">
          <h2 className="ab-label" id="ab-closing">
            {sanitizePlainText(page.cta_eyebrow || "ارتباط")}
          </h2>
          <div className="ab-body">
            {page.cta_title ? <h3>{sanitizePlainText(page.cta_title)}</h3> : null}
            <div className="ab-prose">
              <SafeMultiline value={page.closing_text} />
            </div>
            <div className="ab-actions">
              <ActionLink className="ab-button" to="/contact" label="تماس با تحریریه" />
              <ActionLink className="ab-link" to="/" label="صفحهٔ اصلی" />
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
