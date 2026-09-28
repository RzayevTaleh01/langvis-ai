"use client";
// The mascot on the Log in and Sign up pages: it sits on top of the form and
// reacts to what is typed - it says hello to your name, watches your email
// being written, and shuts its eyes while you type your password.

import { useEffect, useRef } from "react";
import { TutorFace } from "@/legacy/tutor.js";

const SILENT = { outputLevel: () => 0, inputLevel: () => 0 };

export type MascotMood = "smile" | "focus" | "wow" | "search" | "sad" | "laugh";

export function AuthMascot({ say, mood, shut, look }: {
  say: string;                                 // what the bubble says ("" = no bubble)
  mood: MascotMood;
  shut: boolean;                               // eyes closed (a password is being typed)
  look: { x: number; y: number } | null;       // where it looks (-1..1), null = straight ahead
}) {
  const host = useRef<HTMLDivElement>(null);
  const face = useRef<any>(null);            // eslint-disable-line @typescript-eslint/no-explicit-any

  useEffect(() => {
    if (!host.current) return;
    const f = new TutorFace(host.current, SILENT, { mascot: true });
    f.set("IDLE", false);
    face.current = f;
    return () => { f.destroy(); face.current = null; };
  }, []);

  // Its face follows the form: kept up to date on every change.
  useEffect(() => {
    const f = face.current;
    if (!f) return;
    f.shut = shut;
    f.look = look;
    if (mood === "smile") f.moodLeft = 0;
    else f.emote(mood, 600);                   // held until the form changes it
  }, [mood, shut, look]);

  return (
    <div className="auth-mascot" aria-hidden="true">
      <div className="auth-mascot-face" ref={host} />
      {say && <div className="auth-bubble" key={say.split(",")[0]}>{say}</div>}
    </div>
  );
}
