import { apiRequest } from "@/lib/api/client";
import type { OperationalInputRequest, OperationalInputResponse } from "@/lib/types";

export function submitOperationalInput(
  token: string,
  payload: OperationalInputRequest,
): Promise<OperationalInputResponse> {
  return apiRequest<OperationalInputResponse>(
    "/operational-inputs",
    { method: "POST" },
    { token, body: payload },
  );
}
