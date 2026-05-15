import { ApiError, apiRequest, getApiBaseUrl } from "@/lib/api/client";
import type { CompanyFile, FileListResponse } from "@/lib/types";

export function listFiles(token: string): Promise<FileListResponse> {
  return apiRequest<FileListResponse>("/files", { method: "GET" }, { token });
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
