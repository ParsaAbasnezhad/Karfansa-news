import { Icon } from "@/components/ui/Icon";

interface NewsStateProps {
  title: string;
  detail: string;
  error?: boolean;
  onRetry?: () => void;
}

export function NewsState({ title, detail, error = false, onRetry }: NewsStateProps) {
  return (
    <div className={error ? "news-state news-error" : "news-state"} role={error ? "alert" : "status"}>
      <Icon name="news" />
      <strong>{title}</strong>
      <span>{detail}</span>
      {onRetry ? (
        <button type="button" onClick={onRetry}>
          تلاش دوباره
        </button>
      ) : null}
    </div>
  );
}

export function NewsSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="news-grid" aria-label="در حال دریافت خبرها">
      {Array.from({ length: count }, (_, index) => (
        <div className="news-card news-card-skeleton" key={index}>
          <span className="skel news-skel-media" />
          <span className="skel news-skel-label" />
          <span className="skel news-skel-title" />
          <span className="skel news-skel-line" />
          <span className="skel news-skel-line short" />
        </div>
      ))}
    </div>
  );
}
