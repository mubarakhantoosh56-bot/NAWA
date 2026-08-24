import { apiRequest } from "@/lib/api/client";
import type { DecisionCreateRequest, DecisionResponse } from "@/lib/types";

// M8 Slice 3B-2: no company_id field exists on DecisionCreateRequest at
// all (unlike sendChatMessage's ChatRequest, which re-validates a client-
// echoed company_id server-side) - the auth token alone carries identity,
// matching the existing convention in lib/api/situations.ts.
export function recordDecision(token: string, payload: DecisionCreateRequest): Promise<DecisionResponse> {
  return apiRequest<DecisionResponse>("/decisions", { method: "POST" }, { token, body: payload });
}
