import { apiClient } from "@/lib/api-client";
import type { AboutPageContent, ContactPageContent } from "@/features/about/types/pages";

export function fetchAboutPage(signal?: AbortSignal): Promise<AboutPageContent> {
  return apiClient.get<AboutPageContent>("pages/about/", signal ? { signal } : undefined);
}

export function fetchContactPage(signal?: AbortSignal): Promise<ContactPageContent> {
  return apiClient.get<ContactPageContent>("pages/contact/", signal ? { signal } : undefined);
}
