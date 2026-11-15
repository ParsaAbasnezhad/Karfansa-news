import { apiClient } from "@/lib/api-client";
import { ApiError } from "@/lib/errors";

import type { ContactPayload, ContactResponse } from "@/features/about/types/contact";

function readCookie(name: string): string | undefined {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return match?.[1] ? decodeURIComponent(match[1]) : undefined;
}

export async function submitContact(payload: ContactPayload): Promise<ContactResponse> {
  await apiClient.get<{ message: string }>("contact/csrf/");
  const token = readCookie("csrftoken");
  return apiClient.post<ContactResponse>("contact/", payload, {
    headers: token ? { "X-CSRFToken": token } : {},
  });
}

export function contactErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 422) return "برخی فیلدها معتبر نیستند. آن‌ها را بررسی کنید.";
    if (error.message.trim()) return error.message;
  }
  return "ارسال پیام انجام نشد. دوباره تلاش کنید.";
}
