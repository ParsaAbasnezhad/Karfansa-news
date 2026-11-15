import { lazy } from "react";

export const AboutPage = lazy(() =>
  import("@/features/about/pages/AboutPage").then((module) => ({ default: module.AboutPage })),
);

export const ContactPage = lazy(() =>
  import("@/features/about/pages/ContactPage").then((module) => ({ default: module.ContactPage })),
);
