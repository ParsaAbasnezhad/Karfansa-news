import { useState } from "react";

import { LOGO } from "@/components/layout/logo";

/**
 * Full-screen boot loader: centered official logo, thin animated bar and Persian label.
 * Unmounts itself when the app is ready (see App); uses CSS-only animations.
 */
export function AppLoader({ loading }: { loading: boolean }) {
  const [ready, setReady] = useState(false);
  // Read the preference during render: no state updates, no cascading renders.
  const [reduced] = useState(() =>
    window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );

  if (ready || (!loading && reduced)) {
    return null;
  }

  return (
    <div
      className={loading ? "app-loader" : "app-loader fade-out"}
      role="status"
      onTransitionEnd={() => setReady(true)}
    >
      <img className="app-loader__logo" src={LOGO} alt="Karfansa" />
      <span className="app-loader__label">در حال بارگذاری</span>
      <span className="app-loader__bar" aria-hidden="true" />
    </div>
  );
}
