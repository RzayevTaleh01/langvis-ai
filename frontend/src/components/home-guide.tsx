"use client";
// The mascot beside a page - only a picture, it never speaks aloud. It stands
// beside the page's headings (its title and every section heading) and walks
// down with them as the page scrolls, crossing to the other side only now and
// then - at a big part of the page, after at least two parts on one side. It
// does not jump: its feelings are in its face - a friendly smile, now and then
// a surprised "wow", "wow" when it reaches a new part, and while the page
// scrolls it searches (eyes scanning, "hmm", dots above its head).
//
// On the home page it also walks to and fro beside the big heading by itself.
// On other pages it first says what the page is about (`hello`), beside the
// title. On a phone only the home page shows it, small, at the top.

import { useEffect, useRef, useState } from "react";
import { TutorFace } from "@/legacy/tutor.js";

const SILENT = { outputLevel: () => 0, inputLevel: () => 0 };
const WIDE = "(min-width: 900px)";
const BIG = 0.75;             // a part this share of the screen high is worth crossing for
const STAY = 2;               // parts it stays on one side at least
const HERO_FIRST = 3;         // s on the left of the home heading before its first walk across
const HERO_STAY = 6;          // s on each side after that
const HELLO_FOR = 6000;       // ms its word about the page stays
// No laughing and no winking here: its smile, and now and then a surprised "wow".
const MOODS = ["smile", "wow", "smile"] as const;

type Stop = { head: HTMLElement; top: number; bottom: number };

// The parts of the page, one per heading: from its heading to the next one.
function stopsOf(page: HTMLElement): Stop[] {
  const heads = Array.from(page.querySelectorAll<HTMLElement>("h1, h2"))
    .filter((h) => h.offsetParent !== null && !h.closest("[role=dialog], .home-guide"));
  const rects = heads.map((h) => h.getBoundingClientRect());
  const end = page.getBoundingClientRect().top + page.scrollHeight;
  const stops: Stop[] = [];
  heads.forEach((h, n) => {
    // Headings side by side (cards in a row) are one part of the page.
    if (stops.length && Math.abs(rects[n].top - stops[stops.length - 1].top) < 30) return;
    stops.push({ head: h, top: rects[n].top, bottom: 0 });
  });
  stops.forEach((s, n) => { s.bottom = n + 1 < stops.length ? stops[n + 1].top - 12 : end; });
  return stops;
}

// Which side it stands on, part by part: left first; the side changes only at
// a big part after STAY parts on the same side.
function sidesFor(stops: Stop[], vh: number): boolean[] {
  const left: boolean[] = [];
  let run = 0;
  stops.forEach((s, n) => {
    const big = s.bottom - s.top >= vh * BIG;
    if (n === 0) left.push(true);
    else if (big && run >= STAY) { left.push(!left[n - 1]); run = 0; }
    else left.push(left[n - 1]);
    run += 1;
  });
  return left;
}

// Where the page's content is, left to right (what the mascot stands beside).
function contentOf(page: HTMLElement, guide: HTMLElement): { left: number; right: number } {
  let left = Infinity, right = -Infinity;
  for (const child of Array.from(page.children)) {
    if (child === guide || child.contains(guide)) continue;
    const r = child.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    left = Math.min(left, r.left);
    right = Math.max(right, r.right);
  }
  if (left === Infinity) {
    const r = page.getBoundingClientRect();
    return { left: r.left, right: r.right };
  }
  return { left, right };
}

function clamp(v: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, v));
}

export function HomeGuide() {
  return <PageGuide />;
}

export function PageGuide({ hello = "" }: { hello?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [say, setSay] = useState(hello);

  useEffect(() => {
    if (!hello) return;
    const t = setTimeout(() => setSay(""), HELLO_FOR);
    return () => clearTimeout(t);
  }, [hello]);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    const face = new TutorFace(node.querySelector(".home-guide-face") as HTMLElement, SILENT, { mascot: true });
    face.set("IDLE", false);
    face.look = { x: 0.8, y: 0.2 };
    face.emote("wow", 1.2);                  // hello!
    const wide = window.matchMedia(WIDE);
    // Everything moves by time, not by frame: the same on every screen.
    let x = -1, y = -1, raf = 0, last = performance.now(), nextMood = 3, mood = 0;
    let active: HTMLElement | null = null;
    let found: HTMLElement | null = null;        // the part it last "found" (said "wow" to)
    let heroLeft = true, heroTimer = HERO_FIRST;  // its walk to and fro beside the home heading
    let page: HTMLElement | null = null;
    // While the page scrolls it is searching; a moment after, it has found it.
    let scrolling = 0;
    const onScroll = () => { scrolling = 0.35; };
    window.addEventListener("scroll", onScroll, { capture: true, passive: true });

    const frame = (now: number) => {
      raf = requestAnimationFrame(frame);
      const dt = Math.min(1, Math.max(0, (now - last) / 1000));
      last = now;
      // The page it belongs to (it may render a moment after the mascot).
      const cur = document.querySelector<HTMLElement>("main.page");
      if (cur !== page) {
        page?.classList.remove("has-guide");
        page = cur;
        page?.classList.add("has-guide");
      }
      if (!page) return;
      const home = page.classList.contains("home");
      if (scrolling > 0) {
        scrolling -= dt;
        face.emote("search", 0.4);
        nextMood = Math.max(nextMood, 2.5);
      }
      // A new feeling every 3-5 s: a "wow", or just its smile.
      nextMood -= dt;
      if (nextMood <= 0 && scrolling <= 0) {
        face.emote(MOODS[mood % MOODS.length], 1.3);
        mood += 1;
        nextMood = 3 + Math.random() * 2;
      }
      if (!wide.matches) { node.style.transform = ""; return; }   // a phone: it only shows its face
      const size = node.offsetWidth || 112;
      const vh = window.innerHeight, vw = window.innerWidth;
      const stops = stopsOf(page);
      if (!stops.length) return;
      // The part being read: the last one whose heading is above 40% of the
      // screen - or, at the very bottom of the page, the last one on it.
      let i = 0;
      stops.forEach((s, n) => { if (s.top < vh * 0.4) i = n; });
      const scroller = page.scrollHeight > page.clientHeight + 2 ? page : document.scrollingElement;
      if (scroller && scroller.scrollTop > 0 && scroller.scrollTop + scroller.clientHeight >= scroller.scrollHeight - 4) {
        stops.forEach((s, n) => { if (s.top < vh) i = n; });
      }
      const stop = stops[i];
      // Beside the home heading it walks to and fro by itself; further down
      // the side follows the parts of the page.
      const heroHere = home && i === 0;
      if (heroHere && scrolling <= 0) {
        heroTimer -= dt;
        if (heroTimer <= 0) { heroLeft = !heroLeft; heroTimer = HERO_STAY; }
      } else if (!heroHere) {
        heroLeft = true;
        heroTimer = HERO_FIRST;
      }
      const left = heroHere ? heroLeft : sidesFor(stops, vh)[i];
      if (stop.head !== active) active = stop.head;
      // Scrolling has stopped at a new part: found it - "wow".
      if (scrolling <= 0 && found !== active) {
        if (found) { face.emote("wow", 1.2); nextMood = 3.5; }
        found = active;
      }
      const head = stop.head.getBoundingClientRect();
      // Beside the content: the home heading is centred and narrower than the page.
      const text = heroHere ? { left: head.left, right: head.right } : contentOf(page, node);
      const wantX = left ? Math.max(12, text.left - size - 24) : Math.min(vw - size - 12, text.right + 24);
      // While its bubble shows (above it), it stands lower by the bubble's height.
      const bubble = node.querySelector<HTMLElement>(".home-guide-bubble");
      const top = 72 + (bubble ? bubble.offsetHeight + 12 : 0);
      const wantY = clamp(head.top - 10, top, Math.max(top, Math.min(stop.bottom - size, vh - size - 16)));
      if (x < 0) { x = wantX; y = wantY; }
      const dx = wantX - x, dy = wantY - y;
      x += dx * (1 - Math.exp(-dt * 4));      // a smooth glide - no hops, no jumps
      y += dy * (1 - Math.exp(-dt * 5));
      node.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
      node.classList.toggle("on-right", x + size / 2 > vw / 2);
      // It looks towards the content - or where it walks.
      const walking = Math.abs(dx) > 3 || Math.abs(dy) > 3;
      const toText = Math.abs(dx) > 20 ? Math.sign(dx) * 0.9 : x + size / 2 < vw / 2 ? 0.85 : -0.85;
      const headMid = head.top + head.height / 2 - (y + size / 2);
      face.look = { x: toText, y: walking ? clamp(dy / 60, -1, 1) : clamp(headMid / 90, -1, 1) };
    };
    raf = requestAnimationFrame(frame);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("scroll", onScroll, { capture: true });
      face.destroy();
      page?.classList.remove("has-guide");
    };
  }, []);

  return (
    <div className="home-guide" ref={ref} aria-hidden="true">
      <div className="home-guide-face" />
      {say && <div className="home-guide-bubble">{say}</div>}
    </div>
  );
}
