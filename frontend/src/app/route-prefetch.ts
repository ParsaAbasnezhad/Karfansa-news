function once<T>(load: () => Promise<T>) {
  let promise: Promise<T> | undefined;
  return () => {
    promise ??= load().catch((error: unknown) => {
      promise = undefined;
      throw error;
    });
    return promise;
  };
}

export const loadNewsList = once(() => import("@/features/news/pages/NewsListPage"));
export const loadNewsDetail = once(() => import("@/features/news/pages/NewsDetailPage"));
export const loadEditorial = once(() => import("@/features/editorial/pages/EditorialPage"));
export const loadEditorialDetail = once(
  () => import("@/features/editorial/pages/EditorialDetailPage"),
);
export const loadAbout = once(() => import("@/features/about/pages/AboutPage"));
export const loadContact = once(() => import("@/features/about/pages/ContactPage"));

const publicRoutes: Record<string, () => Promise<unknown>> = {
  "/news": loadNewsList,
  "/news/:newsId": loadNewsDetail,
  "/editorial": loadEditorial,
  "/editorial/:slug": loadEditorialDetail,
  "/about": loadAbout,
  "/contact": loadContact,
};

function canPrefetch() {
  const connection = (
    navigator as Navigator & { connection?: { saveData?: boolean; effectiveType?: string } }
  ).connection;
  return (
    !connection?.saveData && !["slow-2g", "2g", "3g"].includes(connection?.effectiveType ?? "")
  );
}

const loaded = new Set<string>();
const queued = new Map<string, Promise<void>>();
let tail = Promise.resolve();

export function prefetchRoute(path: string): Promise<void> {
  const load = publicRoutes[path];
  if (!load || !canPrefetch() || loaded.has(path)) return Promise.resolve();
  const existing = queued.get(path);
  if (existing) return existing;

  const task = tail
    .then(() => {
      if (!canPrefetch()) return;
      return load().then(() => {
        loaded.add(path);
      });
    })
    .catch(() => {
      // A failed background download should not affect navigation.
    })
    .finally(() => {
      queued.delete(path);
    });
  queued.set(path, task);
  tail = task;
  return task;
}

export function prefetchPublicRoutesOnIdle(): () => void {
  if (!canPrefetch()) return () => {};

  const routes = ["/news", "/news/:newsId", "/editorial", "/editorial/:slug", "/about", "/contact"];
  let active = true;
  let idleId: number | undefined;
  let timerId: number | undefined;

  const schedule = () => {
    if (!active || routes.length === 0) return;
    const run = () => {
      if (!active || !canPrefetch()) return;
      const path = routes.shift();
      if (path) void prefetchRoute(path).then(schedule);
    };
    if (typeof window.requestIdleCallback === "function") {
      idleId = window.requestIdleCallback(run);
    } else {
      timerId = window.setTimeout(run, 1000);
    }
  };

  if (document.readyState === "complete") schedule();
  else window.addEventListener("load", schedule, { once: true });

  return () => {
    active = false;
    window.removeEventListener("load", schedule);
    if (idleId !== undefined) window.cancelIdleCallback(idleId);
    if (timerId !== undefined) window.clearTimeout(timerId);
  };
}
