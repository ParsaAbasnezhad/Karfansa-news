import { useMutation } from "@tanstack/react-query";

import { submitContact } from "@/features/about/api/contact";
import type { ContactPayload } from "@/features/about/types/contact";

export function useContactMutation() {
  return useMutation({
    mutationFn: (payload: ContactPayload) => submitContact(payload),
  });
}
