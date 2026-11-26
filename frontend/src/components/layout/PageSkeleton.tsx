/**
 * Lightweight local loading state for lazy-route Suspense and API requests:
 * small skeleton bars instead of the full-screen loader.
 */
export function PageSkeleton() {
  return (
    <div className="page-skeleton" role="status" aria-label="در حال بارگذاری">
      <span className="skel page-skeleton__bar" />
      <span className="skel page-skeleton__bar" />
      <span className="skel page-skeleton__bar" />
    </div>
  );
}
