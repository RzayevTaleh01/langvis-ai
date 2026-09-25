"use client";
// Who is signed in. Asked once when the page opens, and again whenever the
// backend answers "auth" (the session ended or another tab signed out).

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { AUTH_EVENT, getJson, postJson } from "@/lib/api";

export type User = { id: number; name: string; email: string; learning: string; created_at: string | null };

type Auth = {
  user: User | null;
  loading: boolean;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
};

const Ctx = createContext<Auth | null>(null);

export function useAuth(): Auth {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth outside AuthProvider");
  return v;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const res = await getJson<{ user: User | null }>("/api/auth/me");
    // No answer at all (the server is restarting): keep what we know.
    if (res) setUser(res.user);
    setLoading(false);
  }, []);

  const logout = useCallback(async () => {
    await postJson("/api/auth/logout", {});
    window.location.href = "/";
  }, []);

  useEffect(() => {
    getJson<{ user: User | null }>("/api/auth/me").then((res) => {
      if (res) setUser(res.user);
      setLoading(false);
    });
    const again = () => { refresh(); };
    window.addEventListener(AUTH_EVENT, again);
    return () => window.removeEventListener(AUTH_EVENT, again);
  }, [refresh]);

  const value = useMemo(() => ({ user, loading, refresh, logout }), [user, loading, refresh, logout]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function firstName(user: User | null): string {
  return (user?.name || "").split(" ")[0];
}
