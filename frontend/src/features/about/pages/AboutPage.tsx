import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { Link } from "react-router";

import { Icon } from "@/components/ui/Icon";
import { useAboutStats } from "@/features/about/hooks/use-about-stats";
import { usePageMeta } from "@/hooks/use-page-meta";
import { formatNumber } from "@/lib/format";

import "../about.css";

const TradeGlobe = lazy(() =>
  import("../TradeGlobe").then((module) => ({ default: module.TradeGlobe })),
);

export function AboutPage() {
  const { headlines, news } = useAboutStats();
  usePageMeta(
    "درباره کارفنسا نیوز",
    "کارفنسا نیوز خبرهای اقتصادی و تجاری را از منابع RSS می‌گیرد، موضوع‌شان را مشخص می‌کند و همان‌ها را منتشر می‌کند.",
  );

  const topicCount = news.data?.topics.length;
  const newsCount = news.data?.count;
  const sourceCount = headlines.data?.source_count;

  return (
    <div className="about-page" dir="rtl">
      <section className="about-hero">
        <div className="about-hero-copy">
          <span className="about-kicker">
            <i />
            تحریریهٔ خبری کارفنسا
          </span>
          <h1>خبر اقتصادی، با منبع و موضوع مشخص</h1>
          <p>
            کارفنسا نیوز یک پایگاه خبری مستقل است. آنچه می‌خوانید از منابع RSS فعال می‌آید، امتیاز
            موضوعی می‌گیرد و فقط موارد تأییدشده در صفحه می‌ماند.
          </p>
          <div className="about-hero-actions">
            <Link className="about-button about-button-primary" to="/news">
              خواندن اخبار <Icon name="arrow" />
            </Link>
            <Link className="about-button about-button-ghost" to="/contact">
              نامه به تحریریه <Icon name="mail" />
            </Link>
          </div>
        </div>
        <div className="about-globe-wrap">
          <div className="about-globe-halo" />
          <div className="about-globe-fallback" aria-hidden="true">
            <span className="about-fallback-orbit orbit-one" />
            <span className="about-fallback-orbit orbit-two" />
            <span className="about-fallback-core">K</span>
          </div>
          <Suspense fallback={null}>
            <LazyGlobe />
          </Suspense>
        </div>
      </section>

      <section className="about-stats" aria-label="آمار زنده اخبار">
        <Stat label="خبرهای در دسترس" value={newsCount} pending={news.isPending} failed={news.isError} />
        <Stat label="موضوع‌های فعال" value={topicCount} pending={news.isPending} failed={news.isError} />
        <Stat
          label="منابع فعال"
          value={sourceCount}
          pending={headlines.isPending}
          failed={headlines.isError}
        />
        <p className="about-stats-note">عددها از سرویس عمومی اخبار خوانده می‌شوند.</p>
      </section>

      <section className="about-story">
        <div className="about-story-index">
          <span>۰۱ / روش کار</span>
          <i />
          <span>منبع ← موضوع ← انتشار</span>
        </div>
        <div className="about-story-copy">
          <span className="about-eyebrow">خبر چطور به صفحه می‌رسد؟</span>
          <h2>دریافت، امتیاز، سپس نمایش</h2>
          <p>
            منابع فعال به‌صورت RSS خوانده می‌شوند. هر خبر اگر با موضوع فعالی جور باشد و امتیاز ارتباط
            بگیرد، در فهرست عمومی می‌آید. خبر آرشیوشده یا بدون موضوع در سایت دیده نمی‌شود.
          </p>
          <p>عنوان، خلاصه، تصویر، منبع و زمان انتشار همان چیزی است که سرویس برمی‌گرداند.</p>
        </div>
      </section>

      <section className="about-purpose">
        <div className="about-section-heading">
          <span className="about-eyebrow">تعهد صفحه</span>
          <h2>خواندن خبر باید به منبع برسد</h2>
        </div>
        <div className="about-purpose-grid">
          <article className="about-purpose-card mission-card">
            <span className="about-card-label">منبع</span>
            <h3>هر کارت، نام رسانه را همراه دارد</h3>
            <p>اصل خبر در سایت منبع است. اینجا گزیده و ارجاع است، نه بازنویسی پنهان.</p>
          </article>
          <article className="about-purpose-card vision-card">
            <span className="about-card-label">موضوع</span>
            <h3>دسته‌ها از سرویس می‌آیند</h3>
            <p>نام موضوع‌ها در پایگاه تعریف می‌شوند. صفحه فقط همان فهرست فعال را نشان می‌دهد.</p>
          </article>
        </div>
      </section>

      <section className="about-principles">
        <div className="about-principles-heading">
          <span className="about-eyebrow">اصول</span>
          <h2>سه قاعده برای همین پایگاه</h2>
        </div>
        <div className="about-principles-list">
          <article>
            <span>01</span>
            <div>
              <h3>بدون خبر ساختگی</h3>
              <p>اگر سرویسی خبری برنگرداند، صفحه خالی می‌ماند.</p>
            </div>
          </article>
          <article>
            <span>02</span>
            <div>
              <h3>امتیاز موضوعی پنهان نیست</h3>
              <p>در فهرست، امتیاز ارتباط هر خبر دیده می‌شود.</p>
            </div>
          </article>
          <article>
            <span>03</span>
            <div>
              <h3>مدیریت در پنل جنگو است</h3>
              <p>منبع، موضوع، سنجاق‌کردن و بایگانی از مدیریت جنگو انجام می‌شود. حساب کاربری وب هنوز سرویس جدا ندارد.</p>
            </div>
          </article>
        </div>
      </section>

      <section className="about-cta">
        <div>
          <span className="about-eyebrow">ادامه</span>
          <h2>از تیتر امروز شروع کنید.</h2>
          <p>فهرست اخبار جست‌وجو و صفحه‌بندی دارد. اگر سوژه‌ای دارید، فرم تماس باز است.</p>
        </div>
        <div className="about-cta-actions">
          <Link className="about-button about-button-white" to="/">
            صفحهٔ اصلی <Icon name="arrow" />
          </Link>
          <Link className="about-button about-button-outline" to="/contact">
            تماس <Icon name="mail" />
          </Link>
        </div>
      </section>
    </div>
  );
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

  return <div className="about-globe-lazy">{visible ? <TradeGlobe /> : null}</div>;
}
