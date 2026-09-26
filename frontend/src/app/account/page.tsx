"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
// Account: your level over time, the dictionary's growth, mistakes per day and
// where they are, and every correction ever made. Dictionary and Grammar are
// its own pages, opened from the buttons at the top right.

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useLive } from "@/components/live-provider";
import { getJson } from "@/lib/api";
import { barChart, fmtDate, hideTip, lineChart, showTip } from "@/lib/charts";
import { usePage } from "@/lib/use-page";
import { Stat } from "@/components/stat";
import { Button } from "@/components/ui/button";

export default function AccountPage() {
  usePage("account");
  const live = useLive();
  const language = ((live.status.modes || []).find((m: any) => m.active) || {}).name;
  const [res, setRes] = useState<any>(null);
  const [failed, setFailed] = useState(false);
  const [skill, setSkill] = useState("all");
  const level = useRef<HTMLDivElement>(null);
  const growth = useRef<HTMLDivElement>(null);
  const mistakes = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getJson("/api/account").then((r) => {
      if (!r || r.error) { setFailed(true); return; }
      setFailed(false);
      setRes(r);
    });
  }, [language]);

  // The charts are drawn into their boxes once the numbers are in.
  useEffect(() => {
    if (!res || !level.current || !growth.current || !mistakes.current) return;
    const guides = [{ v: res.bands.A2, label: "A2" }, { v: res.bands.B1, label: "B1" }, { v: res.bands.B2, label: "B2" }];
    lineChart(level.current, res.history.map((h: any) => ({ x: h.date, y: h.score,
      extra: [`${h.sentences} sentences`, `${h.mistakes} mistakes`] })),
      { min: 0, max: 75, guides, fmt: (v) => Math.round(v), unit: " / 100" });
    lineChart(growth.current, res.growth.map((g: any) => ({ x: g.date, y: g.learned })), { min: 0, area: true, unit: " learned" });
    barChart(mistakes.current, res.history.map((h: any) => ({ x: h.date, y: h.mistakes,
      extra: [`${h.sentences} sentences`] })), { unit: " mistakes" });
  }, [res]);

  const t = res?.totals;
  const strong = res ? res.skills.filter((s: any) => s.status === "strong").length : 0;
  const weak = res ? res.skills.filter((s: any) => s.status === "weak").length : 0;
  const bySkill = res ? res.skills.map((s: any) => ({ label: s.name, value: s.logged_errors || s.errors }))
    .filter((r: any) => r.value > 0).sort((a: any, b: any) => b.value - a.value).slice(0, 10) : [];
  const top = Math.max(1, ...bySkill.map((r: any) => r.value));
  const names: Record<string, string> = res ? Object.fromEntries(res.skills.map((s: any) => [s.id, s.name])) : {};
  const skillIds: string[] = res ? [...new Set<string>(res.mistakes.map((m: any) => m.skill))] : [];
  const rows = res ? res.mistakes.filter((m: any) => skill === "all" || m.skill === skill) : [];

  return (
    <main className="page doc" id="page-account">
      <div className="doc-head doc-head-row">
        <div>
          <h1>Account</h1>
          <p className="sub">{failed ? "The account could not be loaded."
            : res ? `Level ${res.level} → goal ${res.goal}` : ""}</p>
        </div>
        <div className="head-actions">
          <Button asChild variant="outline"><Link href="/account/dictionary/">Dictionary</Link></Button>
          <Button asChild variant="outline"><Link href="/account/grammar/">Grammar</Link></Button>
        </div>
      </div>
      {res && (
        <div className="stats">
          <Stat label="Level" value={res.level} sub={`${Math.round(res.score)} / 100`} />
          <Stat label="Sentences" value={String(t.sentences)} sub={`${t.words} words · ${t.days} days`} />
          <Stat label="Words learned" value={String(res.lexis.learned + res.lexis.strong)} sub={`${res.lexis.learning} on the way`} />
          <Stat label="Mistakes" value={String(t.mistakes)} sub="all recorded" />
          <Stat label="Grammar" value={`${strong} strong`} sub={`${weak} weak · ${res.skills.length} in total`} />
        </div>
      )}

      <div className="grid2">
        <section className="card">
          <h2>Level over time</h2>
          <p className="card-sub">Your measured level at the end of each day, 0-100. The lines are where A2, B1 and B2 start.</p>
          <div className="chart" ref={level} />
        </section>
        <section className="card">
          <h2>Dictionary growth</h2>
          <p className="card-sub">Items learned (used on 3 different days), in total.</p>
          <div className="chart" ref={growth} />
        </section>
        <section className="card">
          <h2>Mistakes per day</h2>
          <p className="card-sub">Corrections made on each practice day.</p>
          <div className="chart" ref={mistakes} />
        </section>
        <section className="card">
          <h2>Where the mistakes are</h2>
          <p className="card-sub">All corrections so far, by grammar.</p>
          <div className="hbars">
            {res && !bySkill.length && <p className="empty">No mistakes recorded yet.</p>}
            {bySkill.map((r: any) => (
              <div key={r.label} className="hbar"
                   onMouseMove={(e) => showTip(e.nativeEvent, [r.label, `${r.value} mistakes`])} onMouseLeave={hideTip}>
                <span className="hbar-label">{r.label}</span>
                <span className="hbar-track"><span className="hbar-fill" style={{ width: `${Math.max(2, (100 * r.value) / top)}%` }} /></span>
                <span className="hbar-value">{r.value}</span>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="card">
        <h2>All my mistakes</h2>
        <div className="filters">
          <Select value={skill} onValueChange={setSkill}>
            <SelectTrigger className="w-[240px] bg-[var(--panel)]" aria-label="Grammar"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All grammar</SelectItem>
              {skillIds.map((sid) => <SelectItem key={sid} value={sid}>{names[sid] || sid}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="table-wrap">
          <Table className="table">
            <TableHeader><TableRow><TableHead>Date</TableHead><TableHead>I said</TableHead><TableHead>Correct</TableHead>
              <TableHead>Grammar</TableHead><TableHead>Why</TableHead></TableRow></TableHeader>
            <TableBody>
              {res && !rows.length && <TableRow><TableCell colSpan={5} className="empty">No mistakes recorded yet.</TableCell></TableRow>}
              {rows.map((m: any, i: number) => (
                <TableRow key={i}>
                  <TableCell>{fmtDate(m.ts)}</TableCell>
                  <TableCell className="whitespace-normal"><span className="strike">{m.wrong}</span><div className="muted">{m.said}</div></TableCell>
                  <TableCell className="good-text whitespace-normal">{m.right}</TableCell>
                  <TableCell className="whitespace-normal">{names[m.skill] || m.skill}</TableCell>
                  <TableCell className="muted whitespace-normal">{m.why}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </section>
    </main>
  );
}
