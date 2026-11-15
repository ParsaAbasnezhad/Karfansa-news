import { QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { ErrorBoundary } from "@/app/ErrorBoundary";
import { queryClient } from "@/app/query-client";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </ErrorBoundary>
  );
}
