import { Suspense } from "react";
import { createBrowserRouter } from "react-router";

import { AboutPage, ContactPage } from "@/app/lazy-pages";
import { RouteError } from "@/app/RouteError";
import { AppLayout } from "@/components/layout/AppLayout";
import { NewsDetailPage } from "@/features/news/pages/NewsDetailPage";
import { NewsHomePage } from "@/features/news/pages/NewsHomePage";
import { NewsListPage } from "@/features/news/pages/NewsListPage";
import { StatusPage } from "@/features/status/StatusPage";

const pageFallback = (
  <p className="wrap" role="status">
    در حال بارگذاری…
  </p>
);

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    errorElement: <RouteError />,
    children: [
      { index: true, element: <NewsHomePage /> },
      { path: "news", element: <NewsListPage /> },
      { path: "news/:newsId", element: <NewsDetailPage /> },
      {
        path: "about",
        element: (
          <Suspense fallback={pageFallback}>
            <AboutPage />
          </Suspense>
        ),
      },
      {
        path: "contact",
        element: (
          <Suspense fallback={pageFallback}>
            <ContactPage />
          </Suspense>
        ),
      },
      {
        path: "status",
        element: (
          <div className="wrap">
            <StatusPage />
          </div>
        ),
      },
    ],
  },
]);
