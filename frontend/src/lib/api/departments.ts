import { apiRequest } from "@/lib/api/client";
import type { DepartmentListResponse } from "@/lib/types";

export function listDepartments(token: string): Promise<DepartmentListResponse> {
  return apiRequest<DepartmentListResponse>("/departments", { method: "GET" }, { token });
}
