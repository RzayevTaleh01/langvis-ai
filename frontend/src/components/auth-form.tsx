"use client";
// Log in and Sign up: one card, two forms. On success the page is loaded
// afresh, so the signed-in layout and its connection start clean. The mascot
// on top of the card reacts to each field: hello to your name, a careful look
// at your email, eyes shut for your password.

import Link from "next/link";
import { useEffect, useState } from "react";
import { postJson } from "@/lib/api";
import { AuthMascot, type MascotMood } from "@/components/auth-mascot";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

// The language to learn comes from the course card ("Learn Slovak" opens
// /register/?learn=Slovak); it can be changed later from the header.
const LANGUAGES = ["English", "Slovak"];

type Field = "name" | "email" | "password" | null;
const EMAIL_OK = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

// Where the mascot looks: at the text cursor of the field being typed in.
function lookAt(input: HTMLInputElement | null): { x: number; y: number } | null {
  const face = input?.closest("form")?.querySelector(".auth-mascot-face");
  if (!input || !face) return null;
  const box = input.getBoundingClientRect();
  const at = face.getBoundingClientRect();
  const style = getComputedStyle(input);
  const ctx = document.createElement("canvas").getContext("2d");
  let caret = 0;
  if (ctx) {
    ctx.font = `${style.fontSize} ${style.fontFamily}`;
    caret = ctx.measureText(input.value.slice(0, input.selectionStart ?? input.value.length)).width;
  }
  const x = box.left + parseFloat(style.paddingLeft || "12") + Math.min(caret, box.width - 24);
  const y = box.top + box.height / 2;
  const clamp = (v: number) => Math.max(-1, Math.min(1, v));
  return { x: clamp((x - (at.left + at.width / 2)) / 160), y: clamp((y - (at.top + at.height / 2)) / 160) };
}

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
  const [learning] = useState(() => {
    const learn = new URLSearchParams(window.location.search).get("learn");
    return learn && LANGUAGES.includes(learn) ? learn : "English";
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [joy, setJoy] = useState("");          // signed in: the mascot is glad for a moment
  const [field, setField] = useState<Field>(null);
  const [look, setLook] = useState<{ x: number; y: number } | null>(null);

  // Following the text cursor while they type.
  const follow = (e: React.SyntheticEvent<HTMLInputElement>) => setLook(lookAt(e.currentTarget));
  const on = (f: Field) => ({
    onFocus: (e: React.FocusEvent<HTMLInputElement>) => { setField(f); follow(e); },
    onBlur: () => { setField(null); setLook(null); },
    onKeyUp: follow, onClick: follow, onSelect: follow,
  });

  // What the mascot says and how it looks, field by field.
  const first = name.trim().split(/\s+/)[0];
  let say = register ? "Hi! Let's make your account." : "Welcome back!";
  let mood: MascotMood = "smile";
  if (joy) { say = joy; mood = "laugh"; }
  else if (busy) { say = "One moment…"; mood = "search"; }
  else if (error) {
    // Wrong password (or anything that failed): it is sad with you.
    say = register ? "Oh no… please check it again." : "Oh no… wrong email or password. Try again?";
    mood = "sad";
  }
  else if (field === "name") say = first ? `Hello, ${first}!` : "What's your name?";
  else if (field === "email") {
    mood = "focus";
    say = !email ? "What's your email?" : EMAIL_OK.test(email) ? "Looks good!" : "Let me look…";
  } else if (field === "password") {
    say = register && password.length < 8 ? "I'm not looking! At least 8 characters." : "I'm not looking!";
  } else if (register && first) say = `Hello, ${first}!`;

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
      // It worked: the mascot is glad - then on to the page.
      const who = String(res.user?.name || name || "").trim().split(/\s+/)[0];
      setJoy(register ? `Yay! Welcome, ${who}!` : `Yay! Welcome back${who ? `, ${who}` : ""}!`);
      setTimeout(() => { window.location.href = register ? "/" : nextPage(); }, 1300);
      return;
    }
    setBusy(false);
    setError((res && res.error) || "The server does not answer. Is LangVis running?");
  };

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={submit} noValidate>
        <div className="auth-mascot-slot">
          <AuthMascot say={say} mood={mood} shut={field === "password" && !busy && !joy}
                      look={field === "password" || joy ? null : look} />
        </div>
        <h1>{register ? "Create your account" : "Welcome back"}</h1>
        <p className="auth-sub">{register
          ? "Your level, course, words and mistakes are kept for you alone."
          : "Log in to continue where you stopped."}</p>

        {register && (
          <label className="auth-field">
            <span>Your name</span>
            <Input className="h-10" type="text" autoComplete="name" required maxLength={40}
                   value={name} onChange={(e) => { setName(e.target.value); setError(""); }} placeholder="The tutor calls you by it"
                   {...on("name")} />
          </label>
        )}
        <label className="auth-field">
          <span>Email</span>
          <Input className="h-10" type="email" autoComplete="email" required
                 value={email} onChange={(e) => { setEmail(e.target.value); setError(""); follow(e); }} {...on("email")} />
        </label>
        <label className="auth-field">
          <span>Password</span>
          <Input className="h-10" type="password" required minLength={register ? 8 : undefined}
                 autoComplete={register ? "new-password" : "current-password"}
                 value={password} onChange={(e) => { setPassword(e.target.value); setError(""); }}
                 placeholder={register ? "At least 8 characters" : ""} {...on("password")} />
        </label>

        {error && <p className="auth-error" role="alert">{error}</p>}

        <Button className="auth-submit" type="submit" disabled={busy}>
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
