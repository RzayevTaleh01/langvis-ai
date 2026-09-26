"use client";
/* eslint-disable @typescript-eslint/no-explicit-any, @next/next/no-img-element, @next/next/no-html-link-for-pages */
// The header: the logo, the language being learned and its level on the left;
// the topic and the grammar syllabus (Tutor only), the pages and the account
// menu (settings, sign out) on the right.

import Link from "next/link";
import { ChevronDownIcon, FilePenLine, LogOut, Pencil, Plus, X } from "lucide-react";
import { useState } from "react";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { BookIcon, ChatIcon, GearIcon, GlobeIcon, GrammarIcon, HomeIcon, TopicIcon, UserIcon } from "@/components/icons";
import { useLive } from "@/components/live-provider";
import { firstName, useAuth } from "@/components/auth-provider";
import { CustomTopicDialog, SettingsDialog, UnitsDialog } from "@/components/dialogs";
import { Button } from "@/components/ui/button";

const NAV = [
  { href: "/", page: "home", label: "Home", Icon: HomeIcon },
  { href: "/courses/", page: "courses", label: "Courses", Icon: BookIcon },
  { href: "/tutor/", page: "tutor", label: "Tutor", Icon: ChatIcon },
  { href: "/account/", page: "account", label: "Account", Icon: UserIcon },
] as const;

// Which tab is lit for each page.
const TAB: Record<string, string> = { lesson: "courses", dictionary: "account", grammar: "account" };

export function Header() {
  const live = useLive();
  const { status, page } = live;
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [unitsOpen, setUnitsOpen] = useState(false);
  const [topicDialog, setTopicDialog] = useState<{ open: boolean; topic: any | null }>({ open: false, topic: null });

  const modes = (status.modes || []).filter((m: any) => m.enabled);
  const active = modes.find((m: any) => m.active);
  const g = status.grammar || {};
  const tab = TAB[page] || page;
  // The Tutor is a page of its own: going in or out of it loads the page afresh.
  const hard = (target: string) => page === "tutor" || target === "tutor";

  return (
    <header className="bar">
      <a className="brand" href="/" aria-label="langvis.ai - home">
        <img className="brand-logo" src="/static/logo-bar.png" alt="langvis.ai" />
      </a>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="lang-chip" type="button"
                  title="The language you are learning - each has its own level and progress">
            <GlobeIcon />
            <span id="lang-name">{active ? active.name : "Language"}</span>
            <ChevronDownIcon className="size-3.5 opacity-60" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="min-w-[220px]">
          <DropdownMenuLabel className="text-[11px] tracking-[.08em] uppercase text-muted-foreground">
            Language to learn
          </DropdownMenuLabel>
          {modes.map((m: any) => (
            <DropdownMenuItem key={m.name} className={m.active ? "bg-accent text-accent-foreground" : ""}
                              onSelect={() => { if (!m.active) live.switchLanguage(m.name); }}>
              {m.name}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>

      <div className="chip" id="chip-level" title="Your measured level">
        {status.level ? <><strong>{status.level}</strong>{` → ${status.goal}`}</> : "-"}
      </div>

      <div className="spacer" />

      {page === "tutor" && (
        <>
          <TopicMenu onOwn={(t) => setTopicDialog({ open: true, topic: t })} />
          <Button variant="secondary" size="sm" className="topic-pick grammar-pick" id="chip-unit" type="button"
                  title="The whole grammar syllabus and how well you know each rule"
                  onClick={() => setUnitsOpen(true)}>
            <GrammarIcon />
            <span id="unit-name">{g.total ? `Grammar · ${g.strong}/${g.total} known · ${g.weak} weak` : "Grammar"}</span>
          </Button>
        </>
      )}

      <nav className="nav">
        {NAV.map(({ href, page: p, label, Icon }) => {
          const cls = tab === p ? "active" : "";
          const inner = <><Icon /><span>{label}</span></>;
          return hard(p)
            ? <a key={p} href={href} className={cls} title={label}>{inner}</a>
            : <Link key={p} href={href} className={cls} title={label}>{inner}</Link>;
        })}
      </nav>
      <UserMenu onSettings={() => setSettingsOpen(true)} />

      <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
      <UnitsDialog open={unitsOpen} onOpenChange={setUnitsOpen} />
      <CustomTopicDialog open={topicDialog.open} topic={topicDialog.topic}
                         onOpenChange={(open) => setTopicDialog((d) => ({ ...d, open }))} />
    </header>
  );
}

// The account: who is signed in, Settings, and Log out.
function UserMenu({ onSettings }: { onSettings: () => void }) {
  const { user, logout } = useAuth();
  if (!user) return null;
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="user-btn pl-1" type="button" title={`Signed in as ${user.email}`} aria-label="Your account">
          <span className="user-avatar" aria-hidden="true">{(user.name || "?").charAt(0).toUpperCase()}</span>
          <span className="user-first">{firstName(user)}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-[230px]">
        <div className="px-2 py-1.5">
          <div className="font-semibold text-[var(--ink-strong)] truncate">{user.name}</div>
          <div className="text-xs text-muted-foreground truncate">{user.email}</div>
        </div>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild><Link href="/account/" className="no-underline!"><UserIcon className="nav-icon" />My progress</Link></DropdownMenuItem>
        <DropdownMenuItem onSelect={onSettings}><GearIcon className="nav-icon" />Settings</DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => { logout(); }}><LogOut className="nav-icon" />Log out</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

// The topic: started topics first, then the rest, then "your own".
function TopicMenu({ onOwn }: { onOwn: (topic: any | null) => void }) {
  const { status, send } = useLive();
  const topics: any[] = status.topics || [];
  const started = topics.filter((t) => t.started);
  const rest = topics.filter((t) => !t.started);

  const row = (t: any) => (
    <div key={t.id} className="flex items-center gap-0.5">
      <DropdownMenuItem className={"flex-1 min-w-0 justify-between " + (t.current ? "bg-accent text-accent-foreground" : "")}
                        onSelect={() => { if (!t.current) send({ type: "topic", id: t.id }); }}>
        <span className="truncate">
          {t.started && <span className="inline-block w-[7px] h-[7px] rounded-full bg-[var(--good)] mr-1.5 align-middle" title="started" />}
          {t.name}
        </span>
        <span className="text-xs text-muted-foreground">{t.custom ? "my topic" : ""}</span>
      </DropdownMenuItem>
      <Button variant="ghost" size="icon-sm" type="button" aria-label={`Scenario for ${t.name}`}
              title={t.prompt ? `Scenario: ${t.prompt}` : "Add a scenario for this topic"}
              onClick={(e) => { e.stopPropagation(); onOwn(t); }}>
        {t.prompt ? <FilePenLine /> : <Pencil />}
      </Button>
      {t.started && t.id !== "free" && (
        <Button variant="ghost" size="icon-sm" type="button" className="hover:bg-[var(--bad-ghost)] hover:text-[var(--bad)]!"
                aria-label={`Delete topic ${t.name}`} title={`Delete ${t.name}`}
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm(`Delete the topic "${t.name}"? Its words stay in your dictionary.`)) {
                    send({ type: "delete_topic", id: t.id });
                  }
                }}><X /></Button>
      )}
    </div>
  );

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="secondary" size="sm" className="topic-pick" id="topic-btn" type="button" title="What we talk about">
          <TopicIcon />
          <span id="topic-name">{(status.topic || {}).name || "Topic"}</span>
          <ChevronDownIcon className="size-3.5 opacity-60" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-[290px] max-h-[70vh] overflow-auto">
        {started.length > 0 && (
          <>
            <DropdownMenuLabel className="text-[11px] tracking-[.08em] uppercase text-muted-foreground">My topics</DropdownMenuLabel>
            {started.map(row)}
          </>
        )}
        {rest.length > 0 && (
          <>
            <DropdownMenuLabel className="text-[11px] tracking-[.08em] uppercase text-muted-foreground">More topics</DropdownMenuLabel>
            {rest.map(row)}
          </>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuItem className="text-primary font-semibold" onSelect={() => onOwn(null)}><Plus />My own topic…</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
