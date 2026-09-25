"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
// Dictionary: every word and phrase met, with how often and on how many
// different days it was used. Click a row for your own sentences with it.

import Link from "next/link";
import { Fragment, useEffect, useMemo, useState } from "react";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useLive } from "@/components/live-provider";
import { Stat } from "@/components/stat";
import { getJson } from "@/lib/api";
import { fmtDate } from "@/lib/charts";
import { usePage } from "@/lib/use-page";

const STATUS_TEXT: Record<string, string> = { new: "New", learning: "Learning", learned: "Learned", strong: "Strong" };
const KIND: Record<string, string> = { phrasal: "phrasal verb", collocation: "collocation", word: "word", expression: "expression" };

function Dots({ stage }: { stage: number }) {
  return (
    <span className="dots" title={`${stage} of 4`}>
      {[1, 2, 3, 4].map((i) => <span key={i} className={"d" + (i <= stage ? " on" : "")} />)}
    </span>
  );
}

function Pick({ value, onChange, label, options }:
  { value: string; onChange: (v: string) => void; label: string; options: [string, string][] }) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[200px] bg-[var(--panel)]" aria-label={label}><SelectValue /></SelectTrigger>
      <SelectContent>{options.map(([v, t]) => <SelectItem key={v} value={v}>{t}</SelectItem>)}</SelectContent>
    </Select>
  );
}

export default function DictionaryPage() {
  usePage("dictionary");
  const live = useLive();
  const language = ((live.status.modes || []).find((m: any) => m.active) || {}).name;
  const [data, setData] = useState<any>(null);
  const [failed, setFailed] = useState(false);
  const [q, setQ] = useState("");
  const [topic, setTopic] = useState("all");
  const [kind, setKind] = useState("all");
  const [status, setStatus] = useState("all");
  const [open, setOpen] = useState<string>("");

  useEffect(() => {
    getJson("/api/dictionary").then((r) => {
      if (!r || r.error) { setFailed(true); return; }
      setFailed(false);
      setData(r);
    });
  }, [language]);

  const rows = useMemo(() => {
    if (!data) return [];
    const today = new Date().toISOString().slice(0, 10);
    const ql = q.trim().toLowerCase();
    return data.items.filter((r: any) =>
      (!ql || r.text.includes(ql) || (r.meaning || "").toLowerCase().includes(ql) || (r.native || "").toLowerCase().includes(ql))
      && (topic === "all" || r.topic_name === topic) && (kind === "all" || r.kind === kind)
      && (status === "all" || (status === "used" ? r.uses > 0
          : status === "mine" ? r.source === "mine"
          : status === "suggested" ? r.source !== "mine" && r.uses === 0
          : status === "due" ? r.uses > 0 && r.next_review && r.next_review <= today
          : r.status === status))).slice(0, 800);
  }, [data, q, topic, kind, status]);

  const c = data?.counts;
  return (
    <main className="page doc" id="page-dictionary">
      <div className="doc-head">
        <Link className="back-link" href="/account/">← Account</Link>
        <h1>Dictionary</h1>
        <p className="sub">{failed ? "The dictionary could not be loaded."
          : "Every word and phrase you met. Nothing is forgotten: each one comes back on its review day, in whatever topic you are in."}</p>
      </div>
      {c && (
        <div className="stats">
          <Stat label="Learned" value={String(c.learned + c.strong)} sub={`${c.strong} strong`} />
          <Stat label="On the way" value={String(c.learning)} sub="used on 1-2 days" />
          <Stat label="Used" value={String(c.used)} sub={`of ${c.total} items`} />
          <Stat label="Due today" value={String(c.due)} sub="come back in the lesson" />
        </div>
      )}
      <div className="filters">
        <Input className="w-[240px] bg-[var(--panel)]" type="search" placeholder="Search…" aria-label="Search the dictionary"
               value={q} onChange={(e) => setQ(e.target.value)} />
        <Pick value={topic} onChange={setTopic} label="Topic"
              options={[["all", "All topics"], ...((data?.topics || []) as string[]).map((t) => [t, t] as [string, string])]} />
        <Pick value={kind} onChange={setKind} label="Kind"
              options={[["all", "All kinds"], ["phrasal", "Phrasal verbs"], ["collocation", "Collocations"], ["word", "Words"], ["expression", "Expressions"]]} />
        <Pick value={status} onChange={setStatus} label="Status"
              options={[["all", "Any status"], ["mine", "Words I use"], ["suggested", "Suggested to learn"], ["used", "Used at least once"],
                        ["new", "New"], ["learning", "Learning"], ["learned", "Learned"], ["strong", "Strong"], ["due", "Due for review"]]} />
      </div>
      <div className="table-wrap">
        <Table className="table" id="dict-table">
          <TableHeader>
            <TableRow>
              <TableHead>Item</TableHead><TableHead>Kind</TableHead><TableHead>Level</TableHead><TableHead>From</TableHead>
              <TableHead>Topic</TableHead><TableHead className="num">Used</TableHead><TableHead className="num">Days</TableHead>
              <TableHead className="num">Heard</TableHead><TableHead>Last used</TableHead><TableHead>Status</TableHead><TableHead>Back on</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data && !rows.length && <TableRow><TableCell colSpan={11} className="empty">Nothing matches.</TableCell></TableRow>}
            {rows.map((r: any) => {
              const from = ({ mine: "you", topic: "topic list", board: "tutor" } as Record<string, string>)[r.source] || "earlier";
              const isOpen = open === r.text;
              return (
                <Fragment key={r.text}>
                  <TableRow className="dict-row cursor-pointer" onClick={() => setOpen(isOpen ? "" : r.text)}>
                    <TableCell className="whitespace-normal">
                      <strong>{r.text}</strong>
                      {(r.meaning || r.native) && <div className="muted">{[r.meaning, r.native && `· ${r.native}`].filter(Boolean).join(" ")}</div>}
                    </TableCell>
                    <TableCell>{KIND[r.kind] || r.kind}</TableCell>
                    <TableCell>{r.level || "-"}</TableCell>
                    <TableCell>{from}</TableCell>
                    <TableCell>{r.topic_name || "-"}</TableCell>
                    <TableCell className="num">{r.wrong ? `${r.uses} (${r.wrong}✗)` : String(r.uses)}</TableCell>
                    <TableCell className="num">{r.days}</TableCell>
                    <TableCell className="num">{r.heard || 0}</TableCell>
                    <TableCell>{fmtDate(r.last)}</TableCell>
                    <TableCell><Dots stage={r.stage} />{" "}<span className={"status " + r.status}>{STATUS_TEXT[r.status] || r.status}</span></TableCell>
                    <TableCell>{r.uses ? fmtDate(r.next_review) : "-"}</TableCell>
                  </TableRow>
                  {isOpen && (
                    <TableRow className="detail">
                      <TableCell colSpan={11} className="whitespace-normal">
                        {r.sentences.length > 0 && <><div className="label">Your sentences</div>
                          <ul className="quotes">{r.sentences.map((s: string, i: number) => <li key={i}>{s}</li>)}</ul></>}
                        {r.wrong_sentences.length > 0 && <><div className="label">Used wrongly</div>
                          <ul className="quotes bad">{r.wrong_sentences.map((s: string, i: number) => <li key={i}>{s}</li>)}</ul></>}
                        {r.example && <><div className="label">Example</div><p className="quote">{r.example}</p></>}
                        {!r.sentences.length && !r.wrong_sentences.length && !r.example &&
                          <p className="muted">Not used yet - the tutor will ask for it.</p>}
                      </TableCell>
                    </TableRow>
                  )}
                </Fragment>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </main>
  );
}
