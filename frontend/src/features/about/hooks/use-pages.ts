import { useQuery } from "@tanstack/react-query";

import { fetchAboutPage, fetchContactPage } from "@/features/about/api/pages";

export const aboutPageKey = ["pages", "about"] as const;
export const contactPageKey = ["pages", "contact"] as const;

export function useAboutPage() {
  return useQuery({
    queryKey: aboutPageKey,
    queryFn: ({ signal }) => fetchAboutPage(signal),
    staleTime: 60_000,
  });
}

export function useContactPage() {
  return useQuery({
    queryKey: contactPageKey,
    queryFn: ({ signal }) => fetchContactPage(signal),
    staleTime: 60_000,
  });
}
