import { apiClient } from "@/lib/api-client";

import type {
  HeadlinesResponse,
  NewsDetailResponse,
  NewsListParams,
  NewsListResponse,
} from "@/features/news/types/news";

function listQuery(params: NewsListParams) {
  return {
    topic: params.topic || undefined,
    q: params.q || undefined,
    page: params.page ?? 1,
    page_size: params.pageSize ?? 12,
    ordering: params.ordering ?? "-published_at",
  };
}

export function fetchHeadlines(signal?: AbortSignal): Promise<HeadlinesResponse> {
  return apiClient.get<HeadlinesResponse>("news/headlines/", signal ? { signal } : undefined);
}

export function fetchNewsList(
  params: NewsListParams,
  signal?: AbortSignal,
): Promise<NewsListResponse> {
  return apiClient.get<NewsListResponse>("news/", {
    query: listQuery(params),
    ...(signal ? { signal } : {}),
  });
}

export function fetchNewsDetail(id: number, signal?: AbortSignal): Promise<NewsDetailResponse> {
  return apiClient.get<NewsDetailResponse>(`news/${id}/`, signal ? { signal } : undefined);
}
