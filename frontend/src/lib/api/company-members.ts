import { apiRequest } from "@/lib/api/client";
import type { ActionAssignableMember } from "@/lib/types";

// M9 Slice 3 completion pass: the Founder-approved bounded, read-only
// company-member source. No company_id is ever sent - the auth token
// alone carries identity, matching the existing convention in
// lib/api/decisions.ts and lib/api/actions.ts.
export function listCompanyMembers(token: string): Promise<ActionAssignableMember[]> {
  return apiRequest<ActionAssignableMember[]>("/company/members", { method: "GET" }, { token });
}
