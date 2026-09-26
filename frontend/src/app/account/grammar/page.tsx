"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
// Grammar: every rule from A1 to B2 and how well you know it, measured from
// what you say. Click a rule for its explanation and your own mistakes.

import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useEffect, useState } from "react";
import { useLive } from "@/components/live-provider";
import { getJson } from "@/lib/api";
import { fmtDate } from "@/lib/charts";
import { usePage } from "@/lib/use-page";

function Meter({ value }: { value: number | null }) {
  const tone = value === null ? "none" : value < 40 ? "weak" : value < 70 ? "mid" : "strong";
  return <span className="meter"><span className={"meter-fill " + tone} style={{ width: `${value ?? 0}%` }} /></span>;
}

export default function GrammarPage() {
  usePage("grammar");
  const live = useLive();
  const language = ((live.status.modes || []).find((m: any) => m.active) || {}).name;
  const [res, setRes] = useState<any>(null);
  const [open, setOpen] = useState<string>("");

  useEffect(() => { getJson("/api/account").then((r) => { if (r && !r.error) setRes(r); }); }, [language]);

  return (
    <main className="page doc" id="page-grammar">
      <div className="doc-head doc-head-row">
        <div>
          <Link className="back-link" href="/account/"><ArrowLeft className="size-4" />Account</Link>
          <h1>Grammar</h1>
          <p className="sub">Every grammar rule from A1 to B2 and how well you know it - measured from what you say. Click one to see your own mistakes and the rule.</p>
        </div>
      </div>
      <div className="syllabus">
        {res && ["A1", "A2", "B1", "B2"].map((b) => {
          const skills = res.skills.filter((s: any) => s.band === b);
          const strong = skills.filter((s: any) => s.status === "strong").length;
          return (
            <div className="band-group" key={b}>
              <h3>{`${b}  ·  ${strong}/${skills.length} known`}</h3>
              {skills.map((s: any) => (
                <div className="skill-row" key={s.id}>
                  <div className="skill-head" onClick={() => setOpen(open === s.id ? "" : s.id)}>
                    <span className="skill-name">{s.name}</span>
                    <Meter value={s.mastery} />
                    <span className="skill-num">{s.mastery === null ? "-" : String(s.mastery)}</span>
                    <span className={"status " + s.status}>{s.status === "new" ? "not used yet" : s.status}</span>
                    <span className="skill-counts">{`${s.correct}✓ ${s.errors}✗`}</span>
                  </div>
                  <div className={"skill-body" + (open === s.id ? "" : " hidden")}>
                    <p className="muted">{s.hint}</p>
                    {s.rule && <p>{s.rule}</p>}
                    {s.examples.length > 0 && (
                      <>
                        <div className="label">Your mistakes</div>
                        <ul className="quotes">
                          {s.examples.map((e: any, i: number) => (
                            <li key={i}><span className="strike">{e.wrong}</span>{" → "}<strong>{e.right}</strong></li>
                          ))}
                        </ul>
                      </>
                    )}
                    {s.next_review && <p className="muted">{`Review on ${fmtDate(s.next_review)}`}</p>}
                  </div>
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </main>
  );
}
