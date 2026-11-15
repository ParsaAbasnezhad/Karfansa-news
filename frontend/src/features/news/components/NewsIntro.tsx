import { formatNumber, formatShortDate } from "@/lib/format";

interface NewsIntroProps {
  titleId: string;
  eyebrow: string;
  title: string;
  description: string;
  updatedAt: string | null;
  refreshing: boolean;
  failed?: boolean;
  count?: number | null;
}

export function NewsIntro({
  titleId,
  eyebrow,
  title,
  description,
  updatedAt,
  refreshing,
  failed = false,
  count = null,
}: NewsIntroProps) {
  const stamp = updatedAt ? formatShortDate(updatedAt) : "";
  let status = "در انتظار به‌روزرسانی";
  if (failed) status = "به‌روزرسانی ناموفق";
  else if (refreshing) status = "در حال به‌روزرسانی";
  else if (stamp) status = "به‌روز";

  return (
    <header className="news-mast">
      <div className="news-mast-copy">
        <span className="news-eyebrow">
          <span className={refreshing ? "news-live-dot is-busy" : "news-live-dot"} />
          {eyebrow}
        </span>
        <h1 id={titleId}>{title}</h1>
        <p>{description}</p>
      </div>
      <div className="news-mast-aside">
        <p className="news-status" aria-live="polite">
          <span className={failed ? "is-bad" : refreshing ? "is-busy" : "is-ok"} />
          {status}
        </p>
        {stamp ? <time dateTime={updatedAt ?? undefined}>آخرین به‌روزرسانی: {stamp}</time> : null}
        {typeof count === "number" ? (
          <p className="news-mast-count">
            <strong>{formatNumber(count)}</strong>
            <span>خبر تأییدشده</span>
          </p>
        ) : null}
      </div>
    </header>
  );
}
