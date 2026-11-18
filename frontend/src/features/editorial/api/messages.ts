import { ApiError, getErrorMessage } from "@/lib/errors";

export function editorialErrorMessage(error: unknown) {
  if (error instanceof ApiError && error.status === 404) {
    return "این خبر در فهرست عمومی پیدا نشد.";
  }
  const message = getErrorMessage(error);
  return message && !message.startsWith("Request failed")
    ? message
    : "دریافت اخبار ممکن نشد. اتصال را بررسی کنید و دوباره تلاش کنید.";
}
