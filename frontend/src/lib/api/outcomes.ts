import { apiRequest } from "@/lib/api/client";
import type { OutcomeCreateRequest, OutcomeResponse } from "@/lib/types";

// M8 Slice 3C-2: no company_id field exists on OutcomeCreateRequest at all
// (unlike sendChatMessage's ChatRequest) - the auth token alone carries
// identity, matching the existing convention in lib/api/decisions.ts.
export function recordOutcome(token: string, payload: OutcomeCreateRequest): Promise<OutcomeResponse> {
  return apiRequest<OutcomeResponse>("/outcomes", { method: "POST" }, { token, body: payload });
}
