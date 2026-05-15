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

  useEffect(() => {
    const storedToken = readStoredToken();
    if (!storedToken) {
      setStatus("anonymous");
      return;
    }

    loadMe(storedToken).catch(() => {
      clearStoredToken();
      setToken(null);
      setMe(null);
      setStatus("anonymous");
    });
  }, [loadMe]);

  const loginUser = useCallback(
    async (payload: LoginPayload) => {
      setStatus("loading");
      try {
        const auth = await login(payload);
        storeToken(auth.access_token);
        await loadMe(auth.access_token);
        router.replace("/workspace");
      } catch (error) {
        setStatus("anonymous");
        throw error;
      }
    },
    [loadMe, router],
  );

  const logout = useCallback(() => {
    clearStoredToken();
    setToken(null);
    setMe(null);
    setStatus("anonymous");
    router.replace("/login");
  }, [router]);

  const refreshMe = useCallback(async () => {
    if (!token) {
      return;
    }
    await loadMe(token);
  }, [loadMe, token]);

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
