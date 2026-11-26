import { usePageMeta } from "@/hooks/use-page-meta";

import styles from "./ErrorPage.module.css";

type ErrorKind = "not-found" | "server";

export function ErrorPage({ kind, onRetry }: { kind: ErrorKind; onRetry?: () => void }) {
  const notFound = kind === "not-found";

  usePageMeta(
    `${notFound ? "صفحه پیدا نشد" : "خطای سرور"} | کارفنسا نیوز`,
    undefined,
    { robots: "noindex,nofollow" },
  );

  return (
    <div className={styles.page} dir="rtl">
      <a className={styles.skip} href="#error-content">
        رفتن به محتوا
      </a>
      <header className={styles.header}>
        <a className={styles.brand} href="/" aria-label="کارفنسا نیوز، صفحهٔ اصلی">
          <span className={styles.brandMark} aria-hidden="true">
            ک
          </span>
          <span>
            کارفنسا <strong>نیوز</strong>
          </span>
        </a>
        <span className={styles.headerNote}>پایگاه خبری اقتصادی و تجاری</span>
      </header>

      <main id="error-content" className={styles.main}>
        <div className={styles.illustration} aria-hidden="true">
          <div className={styles.paperBack} />
          <div className={styles.paper}>
            <span className={styles.paperTitle} />
            <span className={styles.paperLine} />
            <span className={styles.paperLine} />
            <span className={styles.paperLine} />
            <span className={styles.paperPhoto} />
            <span className={styles.paperLine} />
            <span className={styles.paperLine} />
          </div>
          <span className={styles.illustrationBadge}>{notFound ? "؟" : "!"}</span>
        </div>

        <div className={styles.copy}>
          <p className={styles.eyebrow}>
            کارفنسا نیوز / {notFound ? "صفحه پیدا نشد" : "اختلال موقت"}
          </p>
          <h1>
            <span className={styles.code}>{notFound ? "۴۰۴" : "۵۰۰"}</span> —{" "}
            {notFound ? "صفحهٔ موردنظر پیدا نشد" : "مشکلی در سرور رخ داده است"}
          </h1>
          <p className={styles.description}>
            {notFound
              ? "ممکن است آدرس تغییر کرده باشد یا این صفحه دیگر در دسترس نباشد."
              : "در حال حاضر امکان پردازش درخواست شما وجود ندارد. لطفاً کمی بعد دوباره تلاش کنید."}
          </p>
          <div className={styles.actions}>
            <a className={styles.primary} href="/">
              بازگشت به صفحهٔ اصلی
            </a>
            {notFound ? (
              <a className={styles.secondary} href="/news">
                مشاهدهٔ آخرین اخبار
              </a>
            ) : (
              <button
                className={styles.secondary}
                type="button"
                onClick={onRetry ?? (() => window.location.reload())}
              >
                تلاش دوباره
              </button>
            )}
          </div>
        </div>
      </main>

      <footer className={styles.footer}>
        کارفنسا نیوز <span aria-hidden="true">·</span> خبر، با دقت و مسئولیت
      </footer>
    </div>
  );
}
