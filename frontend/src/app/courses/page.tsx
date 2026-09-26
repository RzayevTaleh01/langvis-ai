"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
// Courses: the course of the language being learned, laid out like a course
// page - what it is and what you will learn, the whole syllabus week by week
// (every lesson with its parts, words and grammar), and on the right the
// lesson to do now with the way into it.

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckIcon, ChevronDownIcon, LockIcon, PlayIcon } from "lucide-react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
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

  // "Start / Continue the lesson" and a lesson's own button are an explicit
  // start: they open the lesson and begin at once, with the course chosen first.
  const open = (startWith: { track?: string; lesson?: number }) => {
    router.push("/lesson/");
    live.begin(startWith, "lesson");
  };

  return (
    <main className="page course-page" id="page-courses">
      {failed && <div className="doc"><p className="sub">The course could not be loaded.</p></div>}
      {data && !data.available && (
        <div className="doc">
          <h1 className="cp-empty-title">Courses</h1>
          <p className="sub">{`There is no course for ${data.language} yet.`}</p>
        </div>
      )}
      {data && data.available && <Course data={data} open={open} />}
    </main>
  );
}

type Open = (s: { track?: string; lesson?: number }) => void;

function Course({ data, open }: { data: any; open: Open }) {
  const lessons: any[] = data.lessons;
  const cur = lessons[data.current];
  const going = data.step > 0;
  const pct = Math.round((100 * data.done) / Math.max(1, data.total));
  const steps = lessons.reduce((n, l) => n + (l.steps || 0), 0);
  const allWeeks = data.weeks.map((w: any) => `week-${w.week}`);
  const [openWeeks, setOpenWeeks] = useState<string[]>([`week-${cur.week}`]);
  const allOpen = openWeeks.length === allWeeks.length;

  return (
    <>
      <section className="cp-hero">
        <div className="cp-hero-inner">
          <nav className="cp-crumbs" aria-label="Breadcrumb">
            <span>Courses</span><span aria-hidden="true">›</span><span>{data.language}</span>
          </nav>
          <h1>{data.title}</h1>
          {data.about && <p className="cp-about">{data.about}</p>}
          <div className="cp-meta">
            <span className="cp-level">{data.levels}</span>
            <span>{`${data.weeks.length} weeks`}</span>
            <span>{`${data.total} lessons`}</span>
            <span>{`${data.words_total} words and phrases`}</span>
            <span>Explained in simple English · Azerbaijani on the board</span>
          </div>
        </div>
      </section>

      <div className="cp-body">
        <div className="cp-main">
          {data.outcomes?.length > 0 && (
            <section className="cp-learn">
              <h2>What you&apos;ll learn</h2>
              <ul>
                {data.outcomes.map((o: string) => (
                  <li key={o}><CheckIcon className="size-4 shrink-0 text-primary" /><span>{o}</span></li>
                ))}
              </ul>
            </section>
          )}

          <section className="cp-content">
            <div className="cp-content-head">
              <div>
                <h2>Course content</h2>
                <p>{`${data.weeks.length} sections · ${data.total} lessons · ${steps} steps`}</p>
              </div>
              <Button variant="link" size="sm"
                      onClick={() => setOpenWeeks(allOpen ? [] : allWeeks)}>
                {allOpen ? "Collapse all sections" : "Expand all sections"}
              </Button>
            </div>

            <Accordion type="multiple" value={openWeeks} onValueChange={setOpenWeeks} className="cp-sections">
              {data.weeks.map((wk: any) => {
                const inWeek = lessons.filter((l) => l.week === wk.week);
                const done = inWeek.filter((l) => l.state === "done").length;
                return (
                  <AccordionItem key={wk.week} value={`week-${wk.week}`} className="cp-section">
                    <AccordionTrigger className="cp-section-head">
                      <span className="cp-section-title">
                        <strong>{`Week ${wk.week}: ${wk.title}`}</strong>
                        <span className="badge lvl">{wk.band}</span>
                      </span>
                      <span className="cp-section-meta">
                        {`${done}/${inWeek.length} done · ${inWeek.reduce((n, l) => n + (l.steps || 0), 0)} steps`}
                      </span>
                    </AccordionTrigger>
                    <AccordionContent className="cp-section-body">
                      <ol className="cp-lessons">
                        {inWeek.map((l) => <LessonRow key={l.index} l={l} open={open} />)}
                      </ol>
                    </AccordionContent>
                  </AccordionItem>
                );
              })}
            </Accordion>
          </section>
        </div>

        <aside className="cp-side">
          <div className="cp-card">
            <div className="cp-card-kicker">{going ? "Continue where you stopped" : data.done ? "Next lesson" : "Start here"}</div>
            <div className="cp-card-title">{`Lesson ${cur.index + 1}: ${cur.title}`}</div>
            <p className="cp-card-goal">{`After it you can ${cur.goal}.`}</p>
            {going && (
              <>
                <div className="int-bar"><span style={{ width: `${Math.round((100 * data.step) / Math.max(1, data.steps))}%` }} /></div>
                <p className="int-step">{`Step ${data.step + 1} of ${data.steps}`}</p>
              </>
            )}
            <Button size="lg" className="w-full" onClick={() => open({ track: "intensive" })}>
              <PlayIcon />{going ? "Continue the lesson" : "Start the lesson"}
            </Button>
            <div className="cp-progress">
              <div className="cp-progress-row"><span>Your progress</span><strong>{`${pct}%`}</strong></div>
              <div className="int-bar"><span style={{ width: `${pct}%` }} /></div>
              <p>{`${data.done} of ${data.total} lessons done`}</p>
            </div>
            <div className="cp-includes">
              <strong>This course includes</strong>
              <ul>
                <li>{`${data.total} voice lessons with a teacher`}</li>
                <li>{`${data.words_total} words and phrases with translations`}</li>
                <li>Every sentence checked and corrected</li>
                <li>A dialogue, sentence building and questions in every lesson</li>
                <li>Your place kept to the exact step</li>
              </ul>
            </div>
          </div>
        </aside>
      </div>
    </>
  );
}

function LessonRow({ l, open }: { l: any; open: Open }) {
  const [more, setMore] = useState(l.state === "current");
  const icon = l.state === "done" ? <CheckIcon className="size-4" />
    : l.open ? <PlayIcon className="size-3.5" /> : <LockIcon className="size-3.5" />;
  const parts = useMemo(() => (l.parts || []).map((p: any) => `${p.label} (${p.count})`).join(" · "), [l.parts]);
  return (
    <li className={`cp-lesson ${l.state}`}>
      <div className="cp-lesson-row">
        <span className="cp-lesson-icon" aria-hidden="true">{icon}</span>
        <button type="button" className="cp-lesson-main" aria-expanded={more} onClick={() => setMore((m) => !m)}>
          <span className="cp-lesson-title">{`${l.index + 1}. ${l.title}`}</span>
          <span className="cp-lesson-goal">{l.goal}</span>
        </button>
        <span className="cp-lesson-meta">
          {l.state === "current" && <span className="cp-now">Now</span>}
          <span>{`${l.steps} steps`}</span>
          <ChevronDownIcon className={"size-4 transition-transform" + (more ? " rotate-180" : "")} aria-hidden="true" />
        </span>
      </div>
      {more && (
        <div className="cp-lesson-more">
          <dl>
            {l.words?.length > 0 && (<><dt>Words</dt>
              <dd className="int-words">{l.words.map((w: string) => <span key={w} className="int-word">{w}</span>)}</dd></>)}
            {l.grammar && (<><dt>Grammar</dt><dd>{l.grammar}</dd></>)}
            {parts && (<><dt>Parts</dt><dd>{parts}</dd></>)}
            {l.speak && (<><dt>Speaking task</dt><dd>{l.speak}</dd></>)}
          </dl>
          <Button size="sm" variant={l.state === "current" ? "default" : "outline"} disabled={!l.open}
                  title={l.open ? "" : "Finish the lessons before it first"}
                  onClick={() => { if (l.open) open({ lesson: l.index }); }}>
            {l.open ? <PlayIcon /> : <LockIcon />}
            {!l.open ? "Locked" : l.state === "done" ? "Review this lesson" : "Start this lesson"}
          </Button>
        </div>
      )}
    </li>
  );
}
