import { apiRequest } from "@/lib/api/client";
import type { AuthResponse, MeResponse } from "@/lib/types";

export type LoginPayload = {
  email: string;
  password: string;
  company_slug: string;
};

export function login(payload: LoginPayload): Promise<AuthResponse> {
  return apiRequest<AuthResponse>("/auth/login", { method: "POST" }, { body: payload });
}

export function getMe(token: string): Promise<MeResponse> {
  return apiRequest<MeResponse>("/auth/me", { method: "GET" }, { token });
}
