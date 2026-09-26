"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
// The course beside the board: the lesson, its parts with the step you are on,
// and every lesson of the course, week by week.

import Link from "next/link";
import { useEffect, useRef } from "react";
import { Check } from "lucide-react";
import { useLive } from "@/components/live-provider";

export function CourseSide() {
  const live = useLive();
  const it = live.status.intensive;
  const list = useRef<HTMLDivElement>(null);
  const sig = it ? JSON.stringify(it.lessons.map((l: any) => l.state)) : "";

  // The current lesson is kept in view.
  useEffect(() => {
    list.current?.querySelector(".cs-lesson.current")?.scrollIntoView({ block: "center" });
  }, [sig]);

  if (!it) return <aside className="course-side" id="course-side" aria-label="Course syllabus" />;
  const pct = Math.round((100 * it.step) / Math.max(1, it.steps));

  return (
    <aside className="course-side" id="course-side" aria-label="Course syllabus">
      <div className="course-side-head">
        <Link className="course-side-title" href="/courses/">{it.course}</Link>
        <div className="course-side-now">
          <span className="cs-kicker">{`Lesson ${it.lesson} of ${it.total} · ${it.band}`}</span>
          <strong>{it.title}</strong>
        </div>
        <div className="int-bar"><span style={{ width: `${pct}%` }} /></div>
        <ol className="cs-sections">
          {it.sections.map((sec: any) => {
            const here = it.step >= sec.start && it.step < sec.start + sec.count;
            const past = it.step >= sec.start + sec.count;
            return (
              <li key={sec.kind} className={here ? "here" : past ? "past" : ""}>
                <span>{sec.label}</span>
                <span className="cs-count">{here ? `${it.step - sec.start + 1}/${sec.count}` : past ? <Check className="size-3.5" aria-label="done" /> : `${sec.count}`}</span>
              </li>
            );
          })}
        </ol>
      </div>
      <div className="course-side-list" ref={list}>
        {it.weeks.map((wk: any) => (
          <div key={wk.week}>
            <div className="cs-week">{`Week ${wk.week} · ${wk.band}`}</div>
            {it.lessons.filter((l: any) => l.week === wk.week).map((l: any) => (
              <button key={l.index} type="button" className={`cs-lesson ${l.state}`} disabled={!l.open}
                      onClick={() => {
                        if (!l.open || l.state === "current") return;
                        // During a lesson: the server opens the other one and stops -
                        // it waits for Start. Before one: it starts right away.
                        if (live.started) live.send({ type: "intensive_lesson", index: l.index });
                        else live.begin({ lesson: l.index });
                      }}>
                <span className="cs-num">{l.state === "done" ? <Check className="size-3.5" aria-label="done" /> : `${l.index + 1}`}</span>
                <span>{l.title}</span>
              </button>
            ))}
          </div>
        ))}
      </div>
    </aside>
  );
}
