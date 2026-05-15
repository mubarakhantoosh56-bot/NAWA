import { apiRequest } from "@/lib/api/client";
import type { ChatRequest, ChatResponse } from "@/lib/types";

export function sendChatMessage(token: string, payload: ChatRequest): Promise<ChatResponse> {
  return apiRequest<ChatResponse>("/ai/chat", { method: "POST" }, { token, body: payload });
}
