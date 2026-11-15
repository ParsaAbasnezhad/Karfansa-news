import { ApiError, getErrorMessage } from "@/lib/errors";

export function newsErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) return "این خبر در فهرست عمومی پیدا نشد.";
    if (error.code === "validation_error") return "فیلترها معتبر نیستند. دوباره انتخاب کنید.";
    if (error.message.trim()) return error.message;
  }
  const message = getErrorMessage(error);
  if (message && !message.startsWith("Request failed")) return message;
  return "دریافت خبرها ممکن نشد. اتصال را بررسی کنید و دوباره تلاش کنید.";
}

export function publishedStamp(publishedAt: string | null, fetchedAt: string): string {
  return publishedAt ?? fetchedAt;
}
