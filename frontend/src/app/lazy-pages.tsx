import { lazy } from "react";

export const AboutPage = lazy(() =>
  import("@/features/about/pages/AboutPage").then((module) => ({ default: module.AboutPage })),
);

export const ContactPage = lazy(() =>
  import("@/features/about/pages/ContactPage").then((module) => ({ default: module.ContactPage })),
);

export const EditorialPage = lazy(() =>
  import("@/features/editorial/pages/EditorialPage").then((module) => ({
    default: module.EditorialPage,
  })),
);

export const EditorialDetailPage = lazy(() =>
  import("@/features/editorial/pages/EditorialDetailPage").then((module) => ({
    default: module.EditorialDetailPage,
  })),
);
