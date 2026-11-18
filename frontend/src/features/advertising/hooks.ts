import { useQuery } from "@tanstack/react-query";

import { fetchAdvertisementSlides } from "@/features/advertising/api";

export const advertisingSlidesKey = ["advertising", "slides"] as const;

export function useAdvertisementSlides() {
  return useQuery({
    queryKey: advertisingSlidesKey,
    queryFn: ({ signal }) => fetchAdvertisementSlides(signal),
    staleTime: 60_000,
  });
}
