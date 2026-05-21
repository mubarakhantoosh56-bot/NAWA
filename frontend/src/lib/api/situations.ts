import { apiRequest } from "@/lib/api/client";
import type { OperationalSituationListResponse } from "@/lib/types";

export function listSituations(token: string, limit = 5): Promise<OperationalSituationListResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  return apiRequest<OperationalSituationListResponse>(
    `/situations?${params.toString()}`,
    { method: "GET" },
    { token },
  );
}
