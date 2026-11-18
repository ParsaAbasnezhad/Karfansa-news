import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";

import { useSession } from "@/features/auth/session";

export function RequireAuth({ children }: { children: ReactNode }) {
  const location = useLocation();
  const { user, isPending, isError, refetch } = useSession({ refreshOnMount: true });
  // Only block on the initial session load; background refetches must not unmount the page.
  if (isPending && !user)
    return (
      <p className="wrap auth-route-status" role="status">
        در حال بررسی حساب…
      </p>
    );
  if (isError)
    return (
      <div className="wrap auth-route-status" role="alert">
        ارتباط با حساب برقرار نشد.{" "}
        <button type="button" onClick={refetch}>
          تلاش دوباره
        </button>
      </div>
    );
  if (!user) {
    const next = encodeURIComponent(`${location.pathname}${location.search}`);
    return <Navigate to={`/login?next=${next}`} replace />;
  }
  return <>{children}</>;
}
