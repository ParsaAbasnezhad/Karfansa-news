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

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  return "An unexpected error occurred.";
}

/** Single place for error reporting; swap in a real monitoring client here later. */
export function reportError(error: unknown): void {
  console.error("[app-error]", error);
}
