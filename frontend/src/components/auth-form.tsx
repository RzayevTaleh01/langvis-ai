"use client";
// Log in and Sign up: one card, two forms. On success the page is loaded
// afresh, so the signed-in layout and its connection start clean.

import Link from "next/link";
import { useEffect, useState } from "react";
import { postJson } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const LANGUAGES = [
  { name: "English", note: "A2 → B1 · explained simply" },
  { name: "Slovak", note: "A1 → B1 · from zero" },
];

// Only a page of this site: never an address from outside.
function nextPage(): string {
  const next = new URLSearchParams(window.location.search).get("next") || "/";
  return next.startsWith("/") && !next.startsWith("//") ? next : "/";
}

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const register = mode === "register";
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  // Only ever rendered in the browser (the shell waits for the account first).
  const [learning, setLearning] = useState(() => {
    const learn = new URLSearchParams(window.location.search).get("learn");
    return LANGUAGES.some((l) => l.name === learn) ? (learn as string) : "English";
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    document.body.dataset.page = mode;
  }, [mode]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    const res = register
      ? await postJson("/api/auth/register", { name, email, password, learning })
      : await postJson("/api/auth/login", { email, password });
    if (res && res.ok) {
      window.location.href = register ? "/" : nextPage();
      return;
    }
    setBusy(false);
    setError((res && res.error) || "The server does not answer. Is LangVis running?");
  };

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={submit} noValidate>
        <h1>{register ? "Create your account" : "Welcome back"}</h1>
        <p className="auth-sub">{register
          ? "Your level, course, words and mistakes are kept for you alone."
          : "Log in to continue where you stopped."}</p>

        {register && (
          <label className="auth-field">
            <span>Your name</span>
            <Input type="text" autoComplete="name" required maxLength={40}
                   value={name} onChange={(e) => setName(e.target.value)} placeholder="The tutor calls you by it" />
          </label>
        )}
        <label className="auth-field">
          <span>Email</span>
          <Input type="email" autoComplete="email" required
                 value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="auth-field">
          <span>Password</span>
          <Input type="password" required minLength={register ? 8 : undefined}
                 autoComplete={register ? "new-password" : "current-password"}
                 value={password} onChange={(e) => setPassword(e.target.value)}
                 placeholder={register ? "At least 8 characters" : ""} />
        </label>

        {register && (
          <fieldset className="auth-field">
            <span>I want to learn</span>
            <div className="auth-langs">
              {LANGUAGES.map((l) => (
                <Button key={l.name} aria-pressed={learning === l.name}
                        variant={learning === l.name ? "soft" : "outline"}
                        className={"choice-btn" + (learning === l.name ? " border-primary" : "")}
                        onClick={() => setLearning(l.name)}>
                  <strong>{l.name}</strong>
                  <span className="choice-note">{l.note}</span>
                </Button>
              ))}
            </div>
          </fieldset>
        )}

        {error && <p className="auth-error" role="alert">{error}</p>}

        <Button className="auth-submit w-full" size="lg" type="submit" disabled={busy}>
          {busy ? "One moment…" : register ? "Create account" : "Log in"}
        </Button>

        <p className="auth-switch">
          {register ? "Already have an account? " : "New to LangVis? "}
          <Link href={register ? "/login/" : "/register/"}>{register ? "Log in" : "Create an account"}</Link>
        </p>
      </form>
    </main>
  );
}
