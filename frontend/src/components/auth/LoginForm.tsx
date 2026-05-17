"use client";

import { FormEvent, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { useAuth } from "@/components/auth/AuthProvider";

export function LoginForm() {
  const { loginUser, status } = useAuth();
  const [companySlug, setCompanySlug] = useState("northstar-commercial");
  const [email, setEmail] = useState("owner@northstar-demo.local");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    try {
      await loginUser({
        company_slug: companySlug,
        email,
        password,
      });
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.detail);
        return;
      }
      setError("Unable to sign in. Check the backend and try again.");
    }
  }

  const isLoading = status === "loading";

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <label className="block">
        <span className="field-label">Company slug</span>
        <input
          className="input"
          value={companySlug}
          onChange={(event) => setCompanySlug(event.target.value)}
          autoComplete="organization"
          required
        />
      </label>

      <label className="block">
        <span className="field-label">Email</span>
        <input
          className="input"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          autoComplete="email"
          required
        />
      </label>

      <label className="block">
        <span className="field-label">Password</span>
        <input
          className="input"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          required
        />
      </label>

      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <button className="button-primary w-full" type="submit" disabled={isLoading}>
        {isLoading ? "Signing in..." : "Sign in"}
      </button>
    </form>
  );
}
