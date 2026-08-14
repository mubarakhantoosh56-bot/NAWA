import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "@/components/auth/AuthProvider";
import { getMe, login } from "@/lib/api/auth";
import { chatStorageKey } from "@/lib/chat/storage";
import type { AuthResponse, MeResponse } from "@/lib/types";

const replaceMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock, push: vi.fn() }),
}));

const fakeMe: MeResponse = {
  company: { id: "company-123", slug: "acme", name: "Acme", status: "active", plan: "pro" },
  user: { id: "user-1", email: "owner@acme.test", full_name: "Owner", status: "active", auth_provider: "password" },
  membership: { id: "mem-1", company_id: "company-123", user_id: "user-1", role_id: "role-1", department_id: null, status: "active" },
  role: { id: "role-1", slug: "owner", name: "Owner", permissions: ["*"], is_system_role: true },
};

const fakeAuth: AuthResponse = {
  access_token: "a-freshly-issued-jwt",
  refresh_token: "a-refresh-token",
  token_type: "bearer",
  company: fakeMe.company,
  user: fakeMe.user,
  membership: fakeMe.membership,
};

vi.mock("@/lib/api/auth", () => ({
  getMe: vi.fn(async () => fakeMe),
  login: vi.fn(),
}));

// M7 Slice 2A privacy contract tests (Section 17, P6/P7 end-to-end): proves
// the REAL AuthProvider.logout() wiring - not just the underlying
// clearStoredChat helper (see lib/chat/storage.test.ts for that layer).
// Correction Round 1 (2A-F3): F3-A below proves the REAL auth-bootstrap-
// failure wiring; the existing logout tests already satisfy F3-B (targeted
// clear survives explicit logout) and F3-C (anonymous logout is a no-op).
// Correction Round 2 (2A-F5): F5-A/F5-B below prove the shared fail-closed
// cleanup also fires for a post-login identity-validation failure and a
// refreshMe() identity-validation failure - the two paths Codex found were
// still inconsistent. F5-C is the existing bootstrap-failure test above
// (unchanged, must still pass); F5-D is the existing targeted-logout test
// above (unchanged, must still pass).

function LogoutProbe() {
  const { status, logout } = useAuth();
  return (
    <div>
      <span data-testid="status">{status}</span>
      <button onClick={logout}>Log out</button>
    </div>
  );
}

function LoginProbe() {
  const { status, loginUser } = useAuth();
  const [error, setError] = useState<string | null>(null);
  return (
    <div>
      <span data-testid="status">{status}</span>
      <span data-testid="login-error">{error ?? ""}</span>
      <button
        onClick={() => {
          setError(null);
          loginUser({ email: "owner@acme.test", password: "secret", company_slug: "acme" }).catch((err) => {
            setError(err instanceof Error ? err.message : "login failed");
          });
        }}
      >
        Log in
      </button>
    </div>
  );
}

function RefreshProbe() {
  const { status, refreshMe } = useAuth();
  const [error, setError] = useState<string | null>(null);
  return (
    <div>
      <span data-testid="status">{status}</span>
      <span data-testid="refresh-error">{error ?? ""}</span>
      <button
        onClick={() => {
          setError(null);
          refreshMe().catch((err) => {
            setError(err instanceof Error ? err.message : "refresh failed");
          });
        }}
      >
        Refresh
      </button>
    </div>
  );
}

describe("AuthProvider.logout()", () => {
  beforeEach(() => {
    window.localStorage.clear();
    replaceMock.mockClear();
  });

  it("P6/P7: clears the authenticated company's NAWA chat cache and the auth token, but preserves unrelated keys", async () => {
    window.localStorage.setItem("aimx.access_token", "a-real-jwt");
    window.localStorage.setItem(chatStorageKey("company-123"), JSON.stringify({ ceo: [{ id: "t1" }] }));
    window.localStorage.setItem(chatStorageKey("some-other-company"), JSON.stringify({ ceo: [] }));
    window.localStorage.setItem("unrelated.app.preference", "kept");

    const user = userEvent.setup();
    render(
      <AuthProvider>
        <LogoutProbe />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("authenticated"));

    await user.click(screen.getByText("Log out"));

    expect(window.localStorage.getItem("aimx.access_token")).toBeNull();
    expect(window.localStorage.getItem(chatStorageKey("company-123"))).toBeNull();
    // P7: a different company's chat cache and unrelated keys survive.
    expect(window.localStorage.getItem(chatStorageKey("some-other-company"))).not.toBeNull();
    expect(window.localStorage.getItem("unrelated.app.preference")).toBe("kept");

    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("anonymous"));
    expect(replaceMock).toHaveBeenCalledWith("/login");
  });

  it("F3-C: does not throw or clear chat caches when logging out from an anonymous (no me) state", async () => {
    render(
      <AuthProvider>
        <LogoutProbe />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("anonymous"));

    window.localStorage.setItem(chatStorageKey("company-123"), JSON.stringify({ ceo: [] }));

    const user = userEvent.setup();
    await user.click(screen.getByText("Log out"));

    expect(window.localStorage.getItem(chatStorageKey("company-123"))).not.toBeNull();
  });

  it("F3-A: auth-bootstrap failure (stored token rejected by getMe) clears ALL nawa.chat.* caches, the token, but not unrelated keys", async () => {
    window.localStorage.setItem("aimx.access_token", "a-stale-jwt");
    window.localStorage.setItem(chatStorageKey("company-123"), JSON.stringify({ ceo: [{ id: "t1" }] }));
    window.localStorage.setItem(chatStorageKey("some-other-company"), JSON.stringify({ ceo: [] }));
    window.localStorage.setItem("unrelated.app.preference", "kept");

    vi.mocked(getMe).mockRejectedValueOnce(new Error("token invalid or expired"));

    render(
      <AuthProvider>
        <LogoutProbe />
      </AuthProvider>,
    );

    // No trusted `me`/company_id was ever established this session - a
    // targeted per-company clear is not possible, so every chat cache must
    // go, not just one.
    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("anonymous"));

    expect(window.localStorage.getItem("aimx.access_token")).toBeNull();
    expect(window.localStorage.getItem(chatStorageKey("company-123"))).toBeNull();
    expect(window.localStorage.getItem(chatStorageKey("some-other-company"))).toBeNull();
    expect(window.localStorage.getItem("unrelated.app.preference")).toBe("kept");
  });

  it("F5-A: login identity-validation failure clears the just-stored token and ALL nawa.chat.* caches, never reaches authenticated", async () => {
    window.localStorage.setItem(chatStorageKey("company-123"), JSON.stringify({ ceo: [{ id: "t1" }] }));
    window.localStorage.setItem(chatStorageKey("some-other-company"), JSON.stringify({ ceo: [] }));
    window.localStorage.setItem("unrelated.app.preference", "kept");

    // Credential exchange succeeds (a token is returned)...
    vi.mocked(login).mockResolvedValueOnce(fakeAuth);
    // ...but the subsequent server-side identity fetch fails.
    vi.mocked(getMe).mockRejectedValueOnce(new Error("identity validation failed"));

    const user = userEvent.setup();
    render(
      <AuthProvider>
        <LoginProbe />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("anonymous"));

    await user.click(screen.getByText("Log in"));

    await waitFor(() => expect(screen.getByTestId("login-error")).toHaveTextContent("identity validation failed"));

    // Never reached /workspace as authenticated.
    expect(replaceMock).not.toHaveBeenCalledWith("/workspace");
    expect(screen.getByTestId("status")).toHaveTextContent("anonymous");

    // The just-stored token must not survive.
    expect(window.localStorage.getItem("aimx.access_token")).toBeNull();
    // No trusted identity was ever established - every chat cache is cleared.
    expect(window.localStorage.getItem(chatStorageKey("company-123"))).toBeNull();
    expect(window.localStorage.getItem(chatStorageKey("some-other-company"))).toBeNull();
    // Unrelated storage survives.
    expect(window.localStorage.getItem("unrelated.app.preference")).toBe("kept");
  });

  it("F5-B: refreshMe() identity-validation failure clears the token, all nawa.chat.* caches, and me, while preserving the reject contract", async () => {
    window.localStorage.setItem("aimx.access_token", "a-real-jwt");
    window.localStorage.setItem(chatStorageKey("company-123"), JSON.stringify({ ceo: [{ id: "t1" }] }));
    window.localStorage.setItem(chatStorageKey("some-other-company"), JSON.stringify({ ceo: [] }));
    window.localStorage.setItem("unrelated.app.preference", "kept");

    const user = userEvent.setup();
    render(
      <AuthProvider>
        <LogoutProbe />
        <RefreshProbe />
      </AuthProvider>,
    );

    // Initial bootstrap succeeds (default getMe mock) - authenticated.
    await waitFor(() => expect(screen.getAllByTestId("status")[0]).toHaveTextContent("authenticated"));

    // The NEXT identity call (triggered by refreshMe) fails.
    vi.mocked(getMe).mockRejectedValueOnce(new Error("refresh identity validation failed"));

    await user.click(screen.getByText("Refresh"));

    // refreshMe's reject contract is preserved - the caller still observes
    // the failure (not silently swallowed).
    await waitFor(() =>
      expect(screen.getByTestId("refresh-error")).toHaveTextContent("refresh identity validation failed"),
    );

    await waitFor(() => expect(screen.getAllByTestId("status")[0]).toHaveTextContent("anonymous"));

    expect(window.localStorage.getItem("aimx.access_token")).toBeNull();
    expect(window.localStorage.getItem(chatStorageKey("company-123"))).toBeNull();
    expect(window.localStorage.getItem(chatStorageKey("some-other-company"))).toBeNull();
    expect(window.localStorage.getItem("unrelated.app.preference")).toBe("kept");
  });
});
