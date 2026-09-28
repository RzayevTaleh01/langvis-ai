"use client";
// The tutor on the home page - a cheerful mascot, only a picture: it never
// speaks here. It starts at the top left beside the heading and walks down
// beside the sections as the page scrolls. It crosses to the other side only
// now and then - at a big section, after at least two on one side - so it
// stays calm; crossing, it jumps and grins. On a phone it stays small at the top.

import { useEffect, useRef } from "react";
import { TutorFace } from "@/legacy/tutor.js";

const SILENT = { outputLevel: () => 0, inputLevel: () => 0 };
const WIDE = "(min-width: 900px)";
const JUMP = 0.56;            // seconds of the jump when it crosses to the other side
const BIG = 0.75;             // a section this share of the screen high is worth crossing for
const STAY = 2;               // sections it stays on one side at least

// Which side it stands on, section by section: left first; the side changes
// only at a big section after STAY sections on the same side.
function sidesFor(sections: Element[], vh: number): boolean[] {
  const left: boolean[] = [];
  let run = 0;
  sections.forEach((s, n) => {
    const big = (s as HTMLElement).offsetHeight >= vh * BIG;
    if (n === 0) left.push(true);
    else if (big && run >= STAY) { left.push(!left[n - 1]); run = 0; }
    else left.push(left[n - 1]);
    run += 1;
  });
  return left;
}

function clamp(v: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, v));
}

export function HomeGuide() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = ref.current;
    const page = node?.closest(".page") as HTMLElement | null;
    if (!node || !page) return;
    page.classList.add("has-guide");
    const face = new TutorFace(node, SILENT, { mascot: true });
    face.set("IDLE", false);
    face.look = { x: 0.8, y: 0.2 };
    face.grin = 1;                           // hello!
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const wide = window.matchMedia(WIDE);
    // Everything moves by time, not by frame: the same on a 60 Hz and a 144 Hz
    // screen, and it catches up when the browser slows a hidden tab down.
    let x = -1, y = -1, t = 0, raf = 0, jump = JUMP, last = performance.now();
    let active: Element | null = null;

    const frame = (now: number) => {
      raf = requestAnimationFrame(frame);
      const dt = Math.min(1, Math.max(0, (now - last) / 1000));
      last = now;
      t += dt * 60;                          // t counts 60ths of a second
      if (!wide.matches) {
        // A phone: a small face at the top that only floats.
        node.style.transform = still ? "" : `translateY(${(Math.sin(t * 0.04) * 3).toFixed(1)}px)`;
        return;
      }
      const size = node.offsetWidth || 112;
      const vh = window.innerHeight, vw = window.innerWidth;
      const sections = Array.from(page.querySelectorAll(":scope > section, :scope > div > section"));
      if (!sections.length) return;
      // The section being read: the last one whose top is above 40% of the
      // screen - or, at the very bottom of the page, the last one on it.
      let i = 0;
      sections.forEach((s, n) => { if (s.getBoundingClientRect().top < vh * 0.4) i = n; });
      if (page.scrollTop + page.clientHeight >= page.scrollHeight - 4) {
        sections.forEach((s, n) => { if (s.getBoundingClientRect().top < vh) i = n; });
      }
      const cur = sections[i];
      const sides = sidesFor(sections, vh);
      const left = sides[i];
      if (cur !== active) {
        const prev = active ? sides[sections.indexOf(active)] : left;
        if (active && prev !== left) { jump = 0; face.grin = 1; }   // crossing: a happy jump
        else if (active) face.grin = Math.max(face.grin, 0.45);     // the next section: a smile
        active = cur;
      }
      const box = cur.getBoundingClientRect();
      const headEl = (cur.querySelector("h1, h2") || cur) as HTMLElement;
      const head = headEl.getBoundingClientRect();
      // The heading's own text width: a centred title (the top) is narrower than its section.
      const text = headEl.tagName === "H1" ? head : box;
      const wantX = left ? Math.max(12, text.left - size - 24) : Math.min(vw - size - 12, text.right + 24);
      const wantY = clamp(head.top - 10, Math.max(72, box.top),
                          Math.max(72, Math.min(box.bottom - size, vh - size - 16)));
      if (x < 0 || still) { x = wantX; y = wantY; }
      const dx = wantX - x, dy = wantY - y;
      x += dx * (1 - Math.exp(-dt * 4.4));
      y += dy * (1 - Math.exp(-dt * 5));
      const walking = Math.abs(dx) > 3 || Math.abs(dy) > 3;
      // Crossing to the other side: big hops; walking down: small hops;
      // standing: a slow float. Arriving: one happy jump.
      let hop = Math.sin(t * 0.04) * 3;
      if (walking) hop = -Math.abs(Math.sin(t * 0.25)) * (Math.abs(dx) > 40 ? 22 : 8);
      let stretch = 1;
      if (jump < JUMP) {
        const p = jump / JUMP;
        hop = -Math.sin(Math.PI * p) * 30;
        stretch = p < 0.5 ? 1.06 : p > 0.9 ? 0.9 : 1;           // stretch up, squash on landing
        jump += dt;
      }
      if (still) { hop = 0; stretch = 1; }
      const lean = still ? 0 : walking ? clamp(dx / 30, -1, 1) * 8 : 0;
      node.style.transform = `translate(${x.toFixed(1)}px, ${(y + hop).toFixed(1)}px) `
        + `rotate(${lean.toFixed(1)}deg) scale(${(2 - stretch).toFixed(3)}, ${stretch.toFixed(3)})`;
      // It looks towards the text: right when it stands on the left, and back.
      const toText = x + size / 2 < vw / 2 ? 0.85 : -0.85;
      const headMid = head.top + head.height / 2 - (y + size / 2);
      face.look = { x: toText, y: walking ? clamp(dy / 60, -1, 1) : clamp(headMid / 90, -1, 1) };
    };
    raf = requestAnimationFrame(frame);

    return () => {
      cancelAnimationFrame(raf);
      face.destroy();
      page.classList.remove("has-guide");
    };
  }, []);

  return <div className="home-guide" ref={ref} aria-hidden="true" />;
}
