import { apiClient } from "@/lib/api-client";
import type {
  EditorialCategoriesResponse,
  EditorialDetailResponse,
  EditorialFeaturedResponse,
  EditorialLatestResponse,
  EditorialListParams,
  EditorialListResponse,
} from "../types/editorial";

export function fetchEditorialList(params: EditorialListParams, signal?: AbortSignal) {
  return apiClient.get<EditorialListResponse>("editorial/", {
    query: {
      category: params.category || undefined,
      q: params.q || undefined,
      ordering: params.ordering ?? "-published_at",
      page: params.page ?? 1,
      page_size: params.pageSize ?? 12,
    },
    signal: signal ?? null,
  });
}

export function fetchEditorialFeatured(signal?: AbortSignal) {
  return apiClient.get<EditorialFeaturedResponse>("editorial/featured/", {
    signal: signal ?? null,
  });
}

export function fetchEditorialLatest(signal?: AbortSignal) {
  return apiClient.get<EditorialLatestResponse>("editorial/latest/", { signal: signal ?? null });
}

export function fetchEditorialCategories(signal?: AbortSignal) {
  return apiClient.get<EditorialCategoriesResponse>("editorial/categories/", {
    signal: signal ?? null,
  });
}

export function fetchEditorialDetail(slug: string, signal?: AbortSignal) {
  return apiClient.get<EditorialDetailResponse>(`editorial/${encodeURIComponent(slug)}/`, {
    signal: signal ?? null,
  });
}
