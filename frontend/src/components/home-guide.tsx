"use client";
// The tutor on the home page - only a picture, it never speaks here. It waits
// beside the top of the page, and as the page scrolls it walks down beside each
// section, looking at it as if it were explaining it, with a smile when it
// arrives. On a phone it stays small at the top.

import { useEffect, useRef } from "react";
import { TutorFace } from "@/legacy/tutor.js";

const SILENT = { outputLevel: () => 0, inputLevel: () => 0 };
const WIDE = "(min-width: 900px)";

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
    const face = new TutorFace(node, SILENT);
    face.set("IDLE", false);
    face.look = { x: -0.7, y: 0.2 };
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const wide = window.matchMedia(WIDE);
    let x = -1, y = -1, t = 0, raf = 0;
    let active: Element | null = null;

    const frame = () => {
      raf = requestAnimationFrame(frame);
      t += 1;
      if (!wide.matches) {
        // A phone: a small face at the top that only floats.
        node.style.transform = still ? "" : `translateY(${(Math.sin(t * 0.04) * 3).toFixed(1)}px)`;
        return;
      }
      const size = node.offsetWidth || 104;
      const vh = window.innerHeight, vw = window.innerWidth;
      const sections = Array.from(page.querySelectorAll(":scope > section, :scope > div > section"));
      if (!sections.length) return;
      // The section being read: the last one whose top is above 40% of the screen.
      let cur = sections[0];
      for (const s of sections) if (s.getBoundingClientRect().top < vh * 0.4) cur = s;
      // At the very bottom the last section is the one being read.
      if (page.scrollTop + page.clientHeight >= page.scrollHeight - 4) {
        cur = sections.filter((s) => s.getBoundingClientRect().top < vh).pop() || cur;
      }
      if (cur !== active) {
        active = cur;
        face.grin = 1;                       // arrived: a happy smile
      }
      const box = cur.getBoundingClientRect();
      const head = (cur.querySelector("h1, h2") || cur).getBoundingClientRect();
      // Beside the section's heading, but never outside the section or the screen.
      const wantY = clamp(head.top - 6, Math.max(72, box.top), Math.max(72, Math.min(box.bottom - size, vh - size - 16)));
      const wantX = Math.min(vw - size - 16, box.right + 24);
      if (x < 0 || still) { x = wantX; y = wantY; }
      const dy = wantY - y;
      x += (wantX - x) * 0.12;
      y += dy * 0.08;
      const walking = Math.abs(dy) > 2;
      // Walking: little hops and a lean; standing: a slow float.
      const hop = still ? 0 : walking ? -Math.abs(Math.sin(t * 0.28)) * 7 : Math.sin(t * 0.04) * 3;
      const lean = still ? 0 : walking ? clamp(dy / 40, -1, 1) * 6 : 0;
      node.style.transform = `translate(${x.toFixed(1)}px, ${(y + hop).toFixed(1)}px) rotate(${lean.toFixed(1)}deg)`;
      // It looks at the heading beside it - and down the page while walking.
      const headMid = head.top + head.height / 2 - (y + size / 2);
      face.look = { x: -0.85, y: walking ? clamp(dy / 60, -1, 1) : clamp(headMid / 90, -1, 1) };
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
