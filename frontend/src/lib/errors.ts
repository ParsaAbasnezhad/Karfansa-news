import type { ApiErrorBody } from "@/types/api";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown;

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.code;
    this.details = body.details;
  }
}

const AUTH_ERROR_MESSAGES: Record<string, string> = {
  invalid_credentials: "اطلاعات ورود نادرست است.",
  authentication_required: "برای ادامه وارد حساب شوید.",
  invalid_code: "کد نامعتبر یا منقضی است. کد تازه درخواست کنید.",
  invalid_reset_authorization: "مجوز بازیابی منقضی شده است. دوباره درخواست کنید.",
  delivery_unavailable: "ارسال کد در حال حاضر ممکن نیست. کمی بعد دوباره تلاش کنید.",
  rate_limited: "تعداد تلاش‌ها زیاد است. لطفاً کمی بعد دوباره تلاش کنید.",
  validation_error: "اطلاعات واردشده معتبر نیست.",
};

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return AUTH_ERROR_MESSAGES[error.code] ?? error.message;
  }
  if (error instanceof Error) return error.message;
  return "خطای غیرمنتظره‌ای رخ داد.";
}

/** Single place for error reporting; swap in a real monitoring client here later. */
export function reportError(error: unknown): void {
  // API errors can contain identifiers or validation details. Forms display them in the UI.
  if (error instanceof ApiError) return;
  console.error("[app-error]", error);
}
