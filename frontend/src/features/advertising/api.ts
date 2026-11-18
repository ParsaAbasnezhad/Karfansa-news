import { apiClient } from "@/lib/api-client";
import type { AdvertisementSlideListResponse } from "@/features/advertising/types";

export function fetchAdvertisementSlides(
  signal?: AbortSignal,
): Promise<AdvertisementSlideListResponse> {
  return apiClient.get<AdvertisementSlideListResponse>(
    "advertising/slides/",
    signal ? { signal } : undefined,
  );
}
