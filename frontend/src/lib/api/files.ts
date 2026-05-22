import { ApiError, apiRequest, getApiBaseUrl } from "@/lib/api/client";
import type { CompanyFile, DraftConfirmResponse, EventDraft, EventDraftListResponse, FileListResponse } from "@/lib/types";

export function listFiles(token: string, departmentId?: string | null): Promise<FileListResponse> {
  const query = new URLSearchParams();
  if (departmentId) {
    query.set("department_id", departmentId);
  }
  return apiRequest<FileListResponse>(
    `/files${query.toString() ? `?${query.toString()}` : ""}`,
    { method: "GET" },
    { token },
  );
}

export async function uploadFile(
  token: string,
  file: File,
  departmentId?: string | null,
): Promise<CompanyFile> {
  const formData = new FormData();
  formData.append("file", file);

  const query = new URLSearchParams();
  if (departmentId) {
    query.set("department_id", departmentId);
  }

  const path = `/files/upload${query.toString() ? `?${query.toString()}` : ""}`;
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    let detail = `Upload failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Keep the safe default detail.
    }
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as CompanyFile;
}

export function getFileDrafts(token: string, fileId: string): Promise<EventDraftListResponse> {
  return apiRequest<EventDraftListResponse>(`/files/${fileId}/event-drafts`, { method: "GET" }, { token });
}

export function confirmDraft(
  token: string,
  fileId: string,
  draftId: string,
  edits: { title?: string; category?: string; priority?: string; summary?: string } = {},
): Promise<DraftConfirmResponse> {
  return apiRequest<DraftConfirmResponse>(
    `/files/${fileId}/event-drafts/${draftId}/confirm`,
    { method: "POST" },
    { token, body: edits },
  );
}

export function rejectDraft(token: string, fileId: string, draftId: string): Promise<EventDraft> {
  return apiRequest<EventDraft>(
    `/files/${fileId}/event-drafts/${draftId}/reject`,
    { method: "POST" },
    { token },
  );
}
