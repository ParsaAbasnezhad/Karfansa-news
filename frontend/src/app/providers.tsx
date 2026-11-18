import { QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";

import { ErrorBoundary } from "@/app/ErrorBoundary";
import { queryClient } from "@/app/query-client";
import { ResetTokenProvider } from "@/features/auth/reset-token";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ResetTokenProvider>{children}</ResetTokenProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
