import { lazy } from "react";

import {
  loadAbout,
  loadContact,
  loadEditorial,
  loadEditorialDetail,
  loadNewsDetail,
  loadNewsList,
} from "@/app/route-prefetch";

export const NewsListPage = lazy(() =>
  loadNewsList().then((module) => ({ default: module.NewsListPage })),
);
export const NewsDetailPage = lazy(() =>
  loadNewsDetail().then((module) => ({ default: module.NewsDetailPage })),
);
export const EditorialPage = lazy(() =>
  loadEditorial().then((module) => ({ default: module.EditorialPage })),
);
export const EditorialDetailPage = lazy(() =>
  loadEditorialDetail().then((module) => ({ default: module.EditorialDetailPage })),
);
export const AboutPage = lazy(() => loadAbout().then((module) => ({ default: module.AboutPage })));
export const ContactPage = lazy(() =>
  loadContact().then((module) => ({ default: module.ContactPage })),
);
