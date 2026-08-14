"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

import { getMe, login, type LoginPayload } from "@/lib/api/auth";
import { clearStoredToken, readStoredToken, storeToken } from "@/lib/auth/storage";
import { clearAllStoredChats, clearStoredChat } from "@/lib/chat/storage";
import type { MeResponse } from "@/lib/types";

type AuthStatus = "loading" | "authenticated" | "anonymous";

type AuthContextValue = {
  status: AuthStatus;
  token: string | null;
  me: MeResponse | null;
  loginUser: (payload: LoginPayload) => Promise<void>;
  logout: () => void;
  refreshMe: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [token, setToken] = useState<string | null>(null);
  const [me, setMe] = useState<MeResponse | null>(null);

  const loadMe = useCallback(async (nextToken: string) => {
    const currentUser = await getMe(nextToken);
    setMe(currentUser);
    setToken(nextToken);
    setStatus("authenticated");
  }, []);

  // 2A-F5 (Correction Round 2): the ONE shared fail-closed cleanup policy
  // for every path where server-side identity validation fails and a
  // trusted company/user identity cannot be established - initial
  // bootstrap, a post-login identity fetch, and a refresh. In every one of
  // these cases there is no CURRENTLY trusted `me`/company_id to scope a
  // targeted clear to (even if a stale `me` exists in React state from
  // before the failed refresh, it is exactly what just failed validation
  // and must not be trusted to pick a scope) - clear every nawa.chat.*
  // cache, never just one company's. Explicit logout is deliberately
  // different (known, currently-trusted identity) and keeps its own
  // narrower, targeted cleanup - see logout() below.
  const handleAuthValidationFailure = useCallback(() => {
    clearAllStoredChats();
    clearStoredToken();
    setToken(null);
    setMe(null);
    setStatus("anonymous");
  }, []);

  useEffect(() => {
    const storedToken = readStoredToken();
    if (!storedToken) {
      setStatus("anonymous");
      return;
    }

    loadMe(storedToken).catch(handleAuthValidationFailure);
  }, [handleAuthValidationFailure, loadMe]);

  const loginUser = useCallback(
    async (payload: LoginPayload) => {
      setStatus("loading");
      try {
        const auth = await login(payload);
        storeToken(auth.access_token);
        try {
          await loadMe(auth.access_token);
        } catch (identityError) {
          // 2A-F5: credential exchange succeeded (a token was returned and
          // stored), but server-side identity validation then failed - the
          // just-stored token must not survive, and authenticated state
          // must never be reached. Never navigate to /workspace here.
          handleAuthValidationFailure();
          throw identityError;
        }
        router.replace("/workspace");
      } catch (error) {
        // If login() itself failed (e.g. invalid credentials), no token was
        // ever stored - handleAuthValidationFailure has either already run
        // above (identity validation failure) or there is nothing new to
        // clean up; either way, existing anonymous-state + rethrow
        // behavior is preserved so the caller's error handling contract is
        // unchanged.
        setStatus("anonymous");
        throw error;
      }
    },
    [handleAuthValidationFailure, loadMe, router],
  );

  const logout = useCallback(() => {
    // Shared-machine privacy boundary (M7 Slice 2A): the authenticated
    // company's NAWA chat cache (including cited-evidence explainability)
    // must not survive logout. Scoped to exactly this session's own
    // company id only - never a blanket "clear every nawa.chat.* key",
    // since a shared browser may hold cached chat for other companies the
    // current user is not currently authenticated as.
    if (me) {
      clearStoredChat(me.company.id);
    }
    clearStoredToken();
    setToken(null);
    setMe(null);
    setStatus("anonymous");
    router.replace("/login");
  }, [me, router]);

  const refreshMe = useCallback(async () => {
    if (!token) {
      return;
    }
    try {
      await loadMe(token);
    } catch (error) {
      // 2A-F5: the existing token/identity just failed re-validation and
      // can no longer be trusted - fail closed before propagating, so a
      // caller that expects refreshMe to reject still observes that
      // contract, but never with stale token/chat state left behind.
      handleAuthValidationFailure();
      throw error;
    }
  }, [handleAuthValidationFailure, loadMe, token]);

  const value = useMemo<AuthContextValue>(
    () => ({
      status,
      token,
      me,
      loginUser,
      logout,
      refreshMe,
    }),
    [loginUser, logout, me, refreshMe, status, token],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
