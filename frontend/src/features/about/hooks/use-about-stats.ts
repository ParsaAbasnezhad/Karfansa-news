import { useHeadlines, useNewsList } from "@/features/news/hooks/use-news";

export function useAboutStats() {
  const headlines = useHeadlines();
  const news = useNewsList({ page: 1, pageSize: 1 });
  return { headlines, news };
}
