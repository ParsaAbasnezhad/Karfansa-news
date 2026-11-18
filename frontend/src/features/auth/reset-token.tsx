import { useState, type ReactNode } from "react";

import { ResetTokenContext } from "@/features/auth/reset-token-context";

export function ResetTokenProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  return (
    <ResetTokenContext.Provider value={{ token, setToken }}>{children}</ResetTokenContext.Provider>
  );
}
