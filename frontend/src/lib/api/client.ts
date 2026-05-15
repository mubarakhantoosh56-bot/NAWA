const DEFAULT_API_URL = "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_AIMX_API_URL || DEFAULT_API_URL).replace(/\/$/, "");
}

type RequestOptions = {
  token?: string | null;
  body?: unknown;
  headers?: HeadersInit;
};

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  options: RequestOptions = {},
): Promise<T> {
  const headers = new Headers(options.headers || init.headers);
  headers.set("Accept", "application/json");

  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }

  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : init.body,
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
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

  return (await response.json()) as T;
}
