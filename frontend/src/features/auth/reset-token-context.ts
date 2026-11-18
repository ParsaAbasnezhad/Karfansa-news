import { createContext, useContext } from "react";

export const ResetTokenContext = createContext<{
  token: string | null;
  setToken: (token: string | null) => void;
} | null>(null);

export function useResetToken() {
  const context = useContext(ResetTokenContext);
  if (!context) throw new Error("ResetTokenProvider is required");
  return context;
}
