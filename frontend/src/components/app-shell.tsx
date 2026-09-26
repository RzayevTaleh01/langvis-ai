"use client";
// Two layouts. Signed out: a quiet header (logo, Log in, Sign up) and only the
// start page, Log in and Sign up - no connection to the tutor at all. Signed
// in: the whole app with its live connection, header and dialogs.

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/components/auth-provider";
import { LiveProvider, useLive } from "@/components/live-provider";
import { Header } from "@/components/header";
import { Button } from "@/components/ui/button";
import { ContentDialog, KeyDialog } from "@/components/dialogs";

const GUEST_PAGES = ["/", "/login/", "/register/"];
const AUTH_PAGES = ["/login/", "/register/"];

function normal(path: string): string {
  return path.endsWith("/") ? path : path + "/";
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const path = normal(usePathname() || "/");
  const guestPage = GUEST_PAGES.includes(path);
  const authPage = AUTH_PAGES.includes(path);

  // A page of the app, signed out: to Log in, and back here afterwards.
  // Log in or Sign up, signed in: to the start page.
  useEffect(() => {
    if (loading) return;
    if (!user && !guestPage) window.location.replace(`/login/?next=${encodeURIComponent(path)}`);
    if (user && authPage) window.location.replace("/");
  }, [loading, user, guestPage, authPage, path]);

  if (loading || (!user && !guestPage) || (user && authPage)) {
    return <div className="auth-wait" aria-busy="true" />;
  }

  if (!user) {
    return (
      <>
        <GuestHeader authPage={authPage} path={path} />
        {children}
      </>
    );
  }

  return (
    <LiveProvider>
      <Header />
      {children}
      <div className="chart-tip hidden" id="tooltip" role="status" />
      <KeyDialog />
      <ContentDialog />
      <SeatNotice />
    </LiveProvider>
  );
}

function GuestHeader({ authPage, path }: { authPage: boolean; path: string }) {
  return (
    <header className="bar guest-bar">
      {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
      <a className="brand" href="/" aria-label="langvis.ai - home">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img className="brand-logo" src="/static/logo-bar.png" alt="langvis.ai" />
      </a>
      <div className="spacer" />
      {!authPage && (
        <nav className="guest-links">
          <a href="#how">How it works</a>
          <a href="#courses">Courses</a>
        </nav>
      )}
      {path !== "/login/" && <Button asChild variant="ghost"><Link href="/login/">Log in</Link></Button>}
      {path !== "/register/" && <Button asChild><Link href="/register/">Sign up free</Link></Button>}
    </header>
  );
}

// Another account signed in on this computer: one microphone, one lesson.
function SeatNotice() {
  const { seatTakenBy } = useLive();
  if (!seatTakenBy) return null;
  return (
    <div className="seat-cover" role="alertdialog" aria-labelledby="seat-title">
      <div className="seat-card">
        <h2 id="seat-title">LangVis is in use</h2>
        <p><strong>{seatTakenBy}</strong> signed in on this computer, so your lesson was stopped.
          Your progress is saved.</p>
        <div className="seat-actions">
          <Button onClick={() => window.location.reload()}>Use it here again</Button>
        </div>
      </div>
    </div>
  );
}
