import { apiRequest } from "@/lib/api/client";
import type {
  ActionAssigneeUpdateRequest,
  ActionCreateRequest,
  ActionDetailResponse,
  ActionResponse,
  ActionStatus,
  ActionStatusUpdateRequest,
} from "@/lib/types";

// M9 Slice 3: no company_id/created_by_user_id/changed_by_user_id field
// exists on any of these request types - the auth token alone carries
// identity, matching the existing convention in lib/api/decisions.ts and
// lib/api/outcomes.ts.
export function createAction(token: string, payload: ActionCreateRequest): Promise<ActionResponse> {
  return apiRequest<ActionResponse>("/actions", { method: "POST" }, { token, body: payload });
}

export function listActionsForDecision(token: string, decisionMemoryId: string): Promise<ActionResponse[]> {
  const query = new URLSearchParams({ decision_memory_id: decisionMemoryId }).toString();
  return apiRequest<ActionResponse[]>(`/actions?${query}`, { method: "GET" }, { token });
}

export function getAction(token: string, actionId: string): Promise<ActionDetailResponse> {
  return apiRequest<ActionDetailResponse>(`/actions/${actionId}`, { method: "GET" }, { token });
}

export function changeActionStatus(token: string, actionId: string, status: ActionStatus): Promise<ActionResponse> {
  const payload: ActionStatusUpdateRequest = { status };
  return apiRequest<ActionResponse>(`/actions/${actionId}/status`, { method: "PATCH" }, { token, body: payload });
}

// assignedUserId is required (not optional) here too: callers must pass
// `null` explicitly to unassign, mirroring the backend's own required-
// nullable field - there is no "omit to unassign" shorthand anywhere in
// this call chain.
export function changeActionAssignee(
  token: string,
  actionId: string,
  assignedUserId: string | null,
): Promise<ActionResponse> {
  const payload: ActionAssigneeUpdateRequest = { assigned_user_id: assignedUserId };
  return apiRequest<ActionResponse>(`/actions/${actionId}/assignee`, { method: "PATCH" }, { token, body: payload });
}
