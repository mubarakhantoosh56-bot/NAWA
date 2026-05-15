"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth/AuthProvider";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { status } = useAuth();

  useEffect(() => {
    if (status === "anonymous") {
      router.replace("/login");
    }
  }, [router, status]);

  if (status === "loading") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-surface px-4">
        <div className="panel px-5 py-4 text-sm text-muted">Loading AIMX workspace...</div>
      </main>
    );
  }

  if (status === "anonymous") {
    return null;
  }

  return <>{children}</>;
}
