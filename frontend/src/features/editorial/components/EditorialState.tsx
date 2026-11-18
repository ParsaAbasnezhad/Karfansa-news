import { Icon } from "@/components/ui/Icon";

export function EditorialState({
  title,
  detail,
  error = false,
  onRetry,
}: {
  title: string;
  detail: string;
  error?: boolean;
  onRetry?: () => void;
}) {
  return (
    <div
      className={`kfe-state${error ? " kfe-state-error" : ""}`}
      role={error ? "alert" : "status"}
    >
      <Icon name="news" />
      <strong>{title}</strong>
      <p>{detail}</p>
      {onRetry ? (
        <button type="button" onClick={onRetry}>
          تلاش دوباره
        </button>
      ) : null}
    </div>
  );
}

export function EditorialSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="kfe-grid" aria-label="در حال دریافت اخبار اختصاصی" aria-busy="true">
      {Array.from({ length: count }, (_, index) => (
        <div className="kfe-card kfe-skeleton" key={index}>
          <span className="kfe-skeleton-image" />
          <span className="kfe-skeleton-line kfe-skeleton-short" />
          <span className="kfe-skeleton-line" />
          <span className="kfe-skeleton-line" />
        </div>
      ))}
    </div>
  );
}
