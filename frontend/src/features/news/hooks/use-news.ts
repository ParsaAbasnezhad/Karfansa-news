import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { fetchHeadlines, fetchNewsDetail, fetchNewsList } from "@/features/news/api/news";
import type { NewsListParams } from "@/features/news/types/news";

export function useHeadlines() {
  return useQuery({
    queryKey: ["news", "headlines"],
    queryFn: ({ signal }) => fetchHeadlines(signal),
  });
}

export function useNewsList(params: NewsListParams) {
  return useQuery({
    queryKey: ["news", "list", params],
    queryFn: ({ signal }) => fetchNewsList(params, signal),
    placeholderData: keepPreviousData,
  });
}

export function useNewsDetail(id: number, enabled: boolean) {
  return useQuery({
    queryKey: ["news", "detail", id],
    queryFn: ({ signal }) => fetchNewsDetail(id, signal),
    enabled,
  });
}
