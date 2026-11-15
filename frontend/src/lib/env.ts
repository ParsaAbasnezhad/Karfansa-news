/** Typed access to build-time environment variables (see `.env.example`). */
export const env = {
  apiUrl: import.meta.env.VITE_API_URL ?? "/api/v1",
} as const;
