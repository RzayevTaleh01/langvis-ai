"use client";
/* eslint-disable @typescript-eslint/no-explicit-any, @next/next/no-img-element */
// Home. Signed out: what LangVis is, the courses, and "Sign up". Signed in:
// a welcome with the learner's own level and the way back into their course,
// then every course as tabs.

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LanguageChoiceDialog, useCatalog } from "@/components/dialogs";
import { useLive } from "@/components/live-provider";
import { firstName, useAuth } from "@/components/auth-provider";
import { usePage } from "@/lib/use-page";

export default function HomePage() {
  const { user } = useAuth();
  return user ? <UserHome /> : <GuestHome />;
}

// ── Signed out ───────────────────────────────────────────────────────────────

function GuestHome() {
  const catalog = useCatalog();
  const router = useRouter();
  return (
    <main className="page home" id="page-home">
      <section className="home-hero">
        <img className="home-logo" src="/img/logo-full.png" alt="langvis.ai" />
        <h1>A speaking language teacher in your browser</h1>
        <p className="home-lead">LangVis talks with you by voice and checks every sentence before it answers.
          Learn a language step by step in a <strong>course</strong>, or talk freely with your{" "}
          <strong>tutor</strong> - about anything, whenever you want.</p>
        <div className="home-cta">
          <Button asChild size="lg"><Link href="/register/">Create a free account</Link></Button>
          <Button asChild size="lg" variant="outline"><Link href="/login/">I already have an account</Link></Button>
        </div>
        <Facts catalog={catalog} />
      </section>

      <div id="how">
        <TwoWays />
      </div>
      <Courses catalog={catalog} button={(c) => (
        <Button onClick={() => router.push(`/register/?learn=${c.name}`)}>{`Learn ${c.name}`}</Button>
      )} />
      <HowChecked />
      <Beginners />
      <Progress />

      <section className="home-final">
        <h2>Ready to speak?</h2>
        <p className="home-sub">Your own account keeps your level, course, words and mistakes - only yours.</p>
        <Button asChild size="lg"><Link href="/register/">Create a free account</Link></Button>
        <p className="home-author">langvis.ai · designed and built by Taleh Rzayev</p>
      </section>
    </main>
  );
}

// ── Signed in ────────────────────────────────────────────────────────────────

function UserHome() {
  usePage("home");
  const { user } = useAuth();
  const live = useLive();
  const router = useRouter();
  const catalog = useCatalog();
  const [ask, setAsk] = useState(false);
  const { status } = live;
  const current = catalog?.current;
  const language = ((status.modes || []).find((m: any) => m.active) || {}).name || user?.learning;
  const g = status.grammar || {};

  const openCourse = (name: string, key: string) => {
    if (key === current) router.push("/courses/");
    else live.switchLanguage(name, "/courses/");
  };

  return (
    <main className="page home" id="page-home">
      <section className="welcome">
        <div className="welcome-text">
          <div className="home-card-kicker">Welcome back</div>
          <h1>{`Hi, ${firstName(user)}!`}</h1>
          <p className="home-lead">{language ? `You are learning ${language}.` : "Choose a language to begin."}
            {" "}Continue your course, or just talk with your tutor.</p>
          <div className="home-cta welcome-cta">
            <Button asChild size="lg"><Link href="/courses/">Continue my course</Link></Button>
            {/* The Tutor is a page of its own: it is loaded afresh. */}
            <Button asChild size="lg" variant="outline"><a href="/tutor/">Talk with the Tutor</a></Button>
            <Button size="lg" variant="ghost" onClick={() => setAsk(true)}>Learn another language</Button>
          </div>
        </div>
        <ul className="welcome-stats">
          <li><span>Level</span><strong>{status.level || "-"}</strong>
            <em>{status.level ? `${status.score}/100 → ${status.goal}` : "measured as you speak"}</em></li>
          <li><span>Grammar known</span><strong>{g.total ? `${g.strong}/${g.total}` : "-"}</strong>
            <em>{g.total ? `${g.weak} rules to practise` : "rules from A1 to B2"}</em></li>
          <li><span>Your progress</span><strong><Link href="/account/">Open</Link></strong>
            <em>level history, words, mistakes</em></li>
        </ul>
      </section>

      <Courses catalog={catalog} button={(c) => (
        <Button onClick={() => openCourse(c.name, c.key)}>
          {c.key === current ? "Open my course" : `Learn ${c.name}`}</Button>
      )} />

      <LanguageChoiceDialog open={ask} onOpenChange={setAsk} />
    </main>
  );
}

// ── Sections ─────────────────────────────────────────────────────────────────

// The numbers under the title: counted from the courses themselves.
function Facts({ catalog }: { catalog: any }) {
  const courses: any[] = (catalog && catalog.courses) || [];
  if (!courses.length) return null;
  const lessons = courses.reduce((n, c) => n + c.lessons, 0);
  return (
    <ul className="home-facts">
      <li><strong>{courses.length}</strong><span>{`languages · ${courses.map((c) => c.name).join(", ")}`}</span></li>
      <li><strong>{lessons}</strong><span>course lessons, taught step by step</span></li>
      <li><strong>{catalog.topics}</strong><span>conversation topics, and your own</span></li>
      <li><strong>Live</strong><span>two-way voice, corrected as you speak</span></li>
    </ul>
  );
}

function Courses({ catalog, button }: { catalog: any; button: (c: any) => React.ReactNode }) {
  const courses: any[] = (catalog && catalog.courses) || [];
  const current = catalog?.current;
  return (
    <section className="home-section" id="courses">
      <h2>Our courses</h2>
      <p className="home-sub">Every course is written for real speaking. Pick a language to see its lessons.</p>
      {courses.length > 0 && (
        <Tabs defaultValue={(courses.find((c) => c.key === current) || courses[0]).key}>
          <TabsList variant="line" className="home-tabs h-auto! w-full justify-start rounded-none p-0">
            {courses.map((c) => (
              <TabsTrigger key={c.key} value={c.key}
                           className="home-tab flex-none after:bg-primary data-active:text-primary">{c.name}</TabsTrigger>
            ))}
          </TabsList>
          {courses.map((c) => (
            <TabsContent key={c.key} value={c.key} className="home-course">
              <div className="home-course-head">
                <div>
                  <h3>{c.title}</h3>
                  <p>{c.learner}</p>
                </div>
                {button(c)}
              </div>
              <div className="home-course-meta">{`${c.levels} · ${c.lessons} lessons · ${c.weeks.length} weeks`}</div>
              <div className="home-weeks">
                {c.weeks.map((w: any) => (
                  <div className="home-week" key={w.week}>
                    <div className="home-week-head">
                      <strong>{`Week ${w.week} · ${w.title}`}</strong>
                      <span className="badge lvl">{w.band}</span>
                    </div>
                    <ol>{w.lessons.map((t: string) => <li key={t}>{t}</li>)}</ol>
                  </div>
                ))}
              </div>
            </TabsContent>
          ))}
        </Tabs>
      )}
    </section>
  );
}

function TwoWays() {
  return (
    <section className="home-section">
      <h2>Two ways to learn</h2>
      <p className="home-sub">Choose the side that fits the moment - and switch any time from the header.</p>
      <div className="home-two">
        <article className="home-card">
          <div className="home-card-kicker">Courses</div>
          <h3>Step by step, from zero</h3>
          <p>A course is fixed, hand-written material. The teacher follows it exactly, never skips
            and never jumps ahead, and remembers the step where you stopped.</p>
          <ul>
            <li>Review, new words, ready phrases, one grammar point</li>
            <li>A dialogue line by line, translation or sentence building</li>
            <li>Questions about your own life, then a speaking task</li>
            <li>The syllabus stays open on the left while you learn</li>
          </ul>
          <img src="/img/03-course-words.png" alt="A course lesson on the board" loading="lazy" />
        </article>
        <article className="home-card">
          <div className="home-card-kicker">Tutor</div>
          <h3>Free conversation, gentle help</h3>
          <p>A friendly conversation partner, not a drill. Pick a topic or just talk, and ask for
            any grammar rule, word or role play at any moment.</p>
          <ul>
            <li>A mistake is corrected once, kindly - no forced repeats</li>
            <li>Now and then: one more natural way to say it</li>
            <li>Grammar drawn on the board whenever you ask</li>
            <li>Follow-up questions that keep you speaking</li>
          </ul>
          <img src="/img/07-topic-correction.png" alt="A correction in the Tutor" loading="lazy" />
        </article>
      </div>
    </section>
  );
}

function HowChecked() {
  return (
    <section className="home-section">
      <h2>How one sentence is checked</h2>
      <p className="home-sub">LangVis thinks before it answers. Your own voice is written down with its
        mistakes kept, checked, and only then does the teacher speak.</p>
      <ol className="home-steps">
        <li><strong>You speak</strong><span>The server hears the end of your sentence - it waits
          longer for beginners who pause to find a word.</span></li>
        <li><strong>It thinks</strong><span>Your words are transcribed exactly as said and analysed:
          mistakes, the grammar behind them, a richer version.</span></li>
        <li><strong>It answers</strong><span>The board shows the mistakes in red and why; the teacher
          corrects you, offers a better way, and the talk goes on.</span></li>
      </ol>
      <div className="home-two">
        <img src="/img/09-grammar-board.png" alt="Grammar on the board" loading="lazy" />
        <img src="/img/08-topic-better.png" alt="A better way to say it" loading="lazy" />
      </div>
    </section>
  );
}

function Beginners() {
  return (
    <section className="home-section">
      <h2>Made for beginners</h2>
      <div className="home-three">
        <div className="home-mini"><h3>Explained simply</h3><p>Slovak A1 is explained in simple English,
          later levels in simple Slovak - with the Azerbaijani translation of every word on the board.</p></div>
        <div className="home-mini"><h3>Heard correctly</h3><p>A slow sentence is not cut off, names are
          written as you say them, and repeating after the teacher is never mistaken for its echo.</p></div>
        <div className="home-mini"><h3>Nothing starts by itself</h3><p>The teacher begins only when you
          press Start, and stops when you leave the page or change the topic, language or lesson.</p></div>
      </div>
    </section>
  );
}

function Progress() {
  return (
    <section className="home-section">
      <h2>Your progress, always kept</h2>
      <p className="home-sub">Each language keeps its own level, course position, words and history.</p>
      <div className="home-two">
        <div className="home-list">
          <div><h3>Account</h3><p>Your level over time, mistakes per day and where they are, every
            correction ever made.</p></div>
          <div><h3>Dictionary</h3><p>Every word and phrase you met, with how often and on how many
            different days you used it - it comes back until it is yours.</p></div>
          <div><h3>Grammar</h3><p>Every rule from A1 to B2 with how well you know it, measured from
            what you actually say.</p></div>
        </div>
        <img src="/img/12-account.png" alt="Your account" loading="lazy" />
      </div>
    </section>
  );
}
