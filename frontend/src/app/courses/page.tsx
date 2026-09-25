"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
// Courses: the course of the language being learned - the lesson to do now,
// and every lesson, week by week.

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useLive } from "@/components/live-provider";
import { getJson } from "@/lib/api";
import { usePage } from "@/lib/use-page";
import { CourseCard } from "@/components/course-card";
import { useCatalog } from "@/components/dialogs";
import { Button } from "@/components/ui/button";

export default function CoursesPage() {
  usePage("courses");
  const live = useLive();
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [failed, setFailed] = useState(false);
  const catalog = useCatalog();
  const language = ((live.status.modes || []).find((m: any) => m.active) || {}).name;

  const load = useCallback(async () => {
    const d = await getJson("/api/intensive");
    if (!d || d.error) { setFailed(true); return; }
    setFailed(false);
    setData(d);
  }, []);
  useEffect(() => { load(); }, [load, language]);

  // "Start / Continue the lesson" and the lesson tiles are an explicit start:
  // they open the lesson and begin at once, with the course chosen first.
  const open = (startWith: { track?: string; lesson?: number }) => {
    router.push("/lesson/");
    live.begin(startWith, "lesson");
  };

  return (
    <main className="page doc" id="page-courses">
      <div className="doc-head">
        <h1>Courses</h1>
        <p className="sub">Step-by-step courses for the language you are learning, with a teacher who follows the material.</p>
      </div>
      <div className="cc-grid cc-grid-page">
        {(data?.courses || []).map((c: any) => {
          const full = ((catalog && catalog.courses) || []).find((x: any) => x.key === c.key);
          return (
            <CourseCard key={c.key} course={{ ...c, ...full, key: c.key }} disabled={!c.available}
                        current={c.current && data.available}
                        onClick={() => {
                          if (!c.available) return;
                          live.sendSoon({ type: "track", value: `intensive:${c.key}` });   // only choose it
                          setTimeout(load, 700);
                        }}
                        action={<span className="btn-fake">{!c.available ? "Coming soon"
                          : c.current && data.available ? "Chosen" : "Choose"}</span>} />
          );
        })}
      </div>
      {failed && <p className="sub">The course could not be loaded.</p>}
      {data && !data.available && (
        <section className="card int-now"><p>{`There is no course for ${data.language} yet.`}</p></section>
      )}
      {data && data.available && <CourseMap data={data} open={open} />}
    </main>
  );
}

function CourseMap({ data, open }: { data: any; open: (s: { track?: string; lesson?: number }) => void }) {
  const cur = data.lessons[data.current];
  const going = data.step > 0;
  const pct = Math.round((100 * data.done) / data.total);
  return (
    <>
      <div className="int-course-head">
        <h2>{data.title}</h2>
        <p className="sub">{`${data.done} of ${data.total} lessons done · ${pct}%`}</p>
      </div>
      <section className="card int-now">
        <div className="int-now-kicker">{`Lesson ${cur.index + 1} · week ${cur.week}, day ${cur.day} · ${cur.band}`}</div>
        <h2 className="int-now-title">{cur.title}</h2>
        <p className="int-now-goal">{`After it you can ${cur.goal}.`}</p>
        <div className="int-words">{cur.words.map((w: string) => <span key={w} className="int-word">{w}</span>)}</div>
        {going && (
          <>
            <div className="int-bar"><span style={{ width: `${Math.round((100 * data.step) / Math.max(1, data.steps))}%` }} /></div>
            <p className="int-step">{`Step ${data.step + 1} of ${data.steps}`}</p>
          </>
        )}
        <Button type="button" onClick={() => open({ track: "intensive" })}>
          {going ? "Continue the lesson" : "Start the lesson"}</Button>
      </section>
      <div className="int-weeks">
        {data.weeks.map((wk: any) => (
          <section className="int-week" key={wk.week}>
            <div className="int-week-head">
              <h3>{`Week ${wk.week} · ${wk.title}`}</h3>
              <span className="badge lvl">{wk.band}</span>
            </div>
            <div className="int-grid">
              {data.lessons.filter((l: any) => l.week === wk.week).map((l: any) => (
                <button key={l.index} type="button" className={`int-tile ${l.state}`} disabled={!l.open}
                        title={l.open ? l.goal : "Finish the lessons before it first"}
                        onClick={() => { if (l.open) open({ lesson: l.index }); }}>
                  <span className="int-tile-top">{`${l.index + 1}`}{l.state === "done" && <span className="int-check"> ✓</span>}</span>
                  <span className="int-tile-title">{l.title}</span>
                </button>
              ))}
            </div>
          </section>
        ))}
      </div>
    </>
  );
}
