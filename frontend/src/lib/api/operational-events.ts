import { apiRequest } from "@/lib/api/client";
import type {
  OperationalEvent,
  OperationalEventCreateRequest,
  OperationalEventListResponse,
} from "@/lib/types";

export function createOperationalEvent(
  token: string,
  payload: OperationalEventCreateRequest,
): Promise<OperationalEvent> {
  return apiRequest<OperationalEvent>(
    "/operational-events",
    { method: "POST" },
    { token, body: payload },
  );
}

export function listOperationalEvents(token: string, limit = 5): Promise<OperationalEventListResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  return apiRequest<OperationalEventListResponse>(
    `/operational-events?${params.toString()}`,
    { method: "GET" },
    { token },
  );
}
