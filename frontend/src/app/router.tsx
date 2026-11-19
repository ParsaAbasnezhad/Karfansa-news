import { Suspense } from "react";
import { createBrowserRouter } from "react-router";

import {
  AboutPage,
  ContactPage,
  EditorialDetailPage,
  EditorialPage,
  NewsDetailPage,
  NewsListPage,
} from "@/app/lazy-pages";
import { RouteError } from "@/app/RouteError";
import { AppLayout } from "@/components/layout/AppLayout";
import { NewsHomePage } from "@/features/news/pages/NewsHomePage";
import { StatusPage } from "@/features/status/StatusPage";
import { ErrorPage } from "@/features/error/ErrorPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { VerifyPage } from "@/features/auth/VerifyPage";
import { ForgotPasswordPage, ResetPasswordPage } from "@/features/auth/RecoveryPages";
import { SecurityPage } from "@/features/auth/SecurityPage";
import { RequireAuth } from "@/features/auth/RequireAuth";
import { ProfilePage } from "@/features/profile/ProfilePage";

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
      {
        path: "news",
        element: (
          <Suspense fallback={pageFallback}>
            <NewsListPage />
          </Suspense>
        ),
      },
      {
        path: "news/:newsId",
        element: (
          <Suspense fallback={pageFallback}>
            <NewsDetailPage />
          </Suspense>
        ),
      },
      {
        path: "editorial",
        element: (
          <Suspense fallback={pageFallback}>
            <EditorialPage />
          </Suspense>
        ),
      },
      {
        path: "editorial/:slug",
        element: (
          <Suspense fallback={pageFallback}>
            <EditorialDetailPage />
          </Suspense>
        ),
      },
      { path: "login", element: <LoginPage /> },
      { path: "register", element: <RegisterPage /> },
      { path: "verify", element: <VerifyPage /> },
      { path: "forgot-password", element: <ForgotPasswordPage /> },
      { path: "reset-password", element: <ResetPasswordPage /> },
      {
        path: "account",
        element: (
          <RequireAuth>
            <ProfilePage />
          </RequireAuth>
        ),
      },
      {
        path: "account/security",
        element: (
          <RequireAuth>
            <SecurityPage />
          </RequireAuth>
        ),
      },
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
  { path: "*", element: <ErrorPage kind="not-found" /> },
]);
