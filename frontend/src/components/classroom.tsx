"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
// The board page - a course lesson (/lesson) or the Tutor (/tutor). React draws
// the frame; what is ON the board (your sentence, the corrections, the lesson
// card, the tutor walking to what it explains) is drawn by legacy/board.js and
// legacy/tutor.js, exactly as in the original page, into the same elements.

import { useEffect, useRef, useState } from "react";
import { Board } from "@/legacy/board.js";
import { TutorFace, TutorWalker } from "@/legacy/tutor.js";
import { useLive } from "@/components/live-provider";
import {
  KeyboardIcon, MicOffIcon, MicOnIcon, PlayIcon, RestartIcon, SendIcon, SkipIcon, StopIcon,
} from "@/components/icons";
import { CourseSide } from "@/components/course-side";

export function Classroom({ kind }: { kind: "lesson" | "tutor" }) {
  const live = useLive();
  const boardEl = useRef<HTMLElement>(null);
  const tutorEl = useRef<HTMLDivElement>(null);

  // The board and the walking tutor live as long as the page does.
  useEffect(() => {
    if (!boardEl.current || !tutorEl.current) return;
    const face = new TutorFace(tutorEl.current, live.audio);
    const walker = new TutorWalker(boardEl.current, tutorEl.current, face);
    const board = new Board({ walker, audio: live.audio, send: live.send });
    live.registerBoard({ board, walker, face });
    requestAnimationFrame(() => walker.reflow());
    return () => {
      live.registerBoard(null);
      board.destroy();
      walker.destroy();
      face.destroy();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // The history of this conversation, in the transcript.
  useEffect(() => { live.loadHistory(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const muted = live.muted;
  const pill = muted && live.state !== "SPEAKING" ? "Microphone off" : live.stateText;

  return (
    <main className="page stage" id="page-lesson">
      {kind === "lesson" && <CourseSide />}
      <section className="board" id="board" aria-label="Board" ref={boardEl}>
        {!live.started && (
          <div className="start-gate" id="start-gate">
            <div className="start-box">
              <h2>Ready when you are</h2>
              <p id="start-what">{kind === "tutor"
                ? "Free conversation: talk about anything, ask about any grammar or word. Press Start and your tutor begins."
                : "Your course lesson, step by step. Press Start and the teacher begins."}</p>
              <button className="btn primary start-btn" id="start-btn" type="button" onClick={() => live.begin()}>
                <PlayIcon />
                Start</button>
            </div>
          </div>
        )}
        <div className="board-top">
          <div className="board-head">
            <span className="mode-pill" id="mode-pill" data-mode="idle">
              <span className="mode-dot" /><span className="mode-text">Conversation</span>
            </span>
            <span className="spacer" />
            <span className="state-pill" id="tutor-state">{pill}</span>
            <button className="icon-btn small" id="restart" type="button" title="Start the lesson again"
                    aria-label="Start the lesson again"
                    onClick={() => {
                      if (!live.started) return;
                      live.audio.flush();
                      live.send({ type: "restart" });
                      live.flash("Starting the lesson again…");
                    }}>
              <RestartIcon />
            </button>
          </div>
          <div className="speech empty" aria-live="polite">
            <span className="speech-who">LangVis says</span>
            <p className="speech-text" id="speech-text">Connecting - I will start talking in a moment.</p>
          </div>
        </div>
        <div className="waiting hidden" id="waiting">
          <div><span className="waiting-label">Your turn - say:</span> <span id="waiting-text" /></div>
          <button className="btn ghost small" id="skip" type="button" title="Go on without repeating"
                  onClick={() => live.send({ type: "skip" })}>
            <SkipIcon />
            Skip</button>
        </div>

        <div className="answers hidden" id="answers-block">
          <div className="label">You can say <span className="answers-q" id="answers-q" /></div>
          <ul className="answers-list" id="answers-list" />
        </div>

        <div className="block" id="said-block">
          <div className="label">You said <button className="link" id="undo" type="button" hidden>I didn&apos;t say that</button></div>
          <p className="sentence" id="said"><span className="hint">Speak - your sentence is written here.</span></p>
        </div>

        <div className="block hidden" id="fixed-block">
          <div className="label">Corrected - say it</div>
          <p className="sentence fixed" id="fixed" />
          <ol className="fixes" id="fixes" />
        </div>

        <div className="block lesson hidden" id="lesson-block">
          <div className="lesson-head">
            <span className="label">On the board</span>
            <span className="badge lesson-kind" id="lesson-kind">grammar</span>
            <span className="badge lvl" id="lesson-band" />
          </div>
          <div className="lesson-diagram" id="lesson-diagram" />
          <h2 className="lesson-title chalk" id="lesson-title" />
          <p className="lesson-rule chalk" id="lesson-rule" />
          <ul className="lesson-formula" id="lesson-formula" />
          <div className="label lesson-use" id="lesson-use">Use it like this</div>
          <ul className="lesson-examples" id="lesson-examples" />
        </div>

        <div className="block hidden" id="better-block">
          <div className="label">Say it better · one level up</div>
          <p className="sentence better" id="better" />
          <ul className="enrich" id="enrich" />
        </div>

        <div className="block hidden" id="skills-block">
          <div className="label">Your grammar</div>
          <div className="skill-moves" id="skill-moves" />
        </div>

        <Notice />

        <div className="tutor" id="tutor" ref={tutorEl}>
          <div className="bubble hidden" />
        </div>
      </section>

      <SidePanel />
      <Controls />
    </main>
  );
}

// A short message on the board (it fades after five seconds).
function Notice() {
  const { notice } = useLive();
  const [shown, setShown] = useState<typeof notice>(null);
  useEffect(() => {
    if (!notice) return;
    setShown(notice);
    const t = setTimeout(() => setShown(null), 5000);
    return () => clearTimeout(t);
  }, [notice]);
  return <p className={"notice" + (shown ? "" : " hidden") + (shown && !shown.ok ? " bad" : "")} id="notice">{shown?.text}</p>;
}

// ── The side panel: the words of the topic or lesson, and the transcript ─────

function SidePanel() {
  const live = useLive();
  const [tab, setTab] = useState<"words" | "transcript">("words");
  const [asked, setAsked] = useState<string>("");
  const paneRef = useRef<HTMLDivElement>(null);
  const card = live.coaching || {};
  const deck = card.deck || {};
  const items: any[] = deck.items || [];
  const due: any[] = card.due || [];
  const lex = card.lexis || {};
  const learned = items.filter((i) => i.stage >= 3).length;
  const head = !live.status.lexicon_ready && !deck.intensive
    ? (live.status.lexicon_building ? `Preparing the words for ${(live.status.topic || {}).name}… (once only)`
                                    : "The topic's words are on their way…")
    : items.length
      ? (deck.intensive ? `${deck.tier} · ${deck.title} · ${items.length} words and phrases`
                        : `${deck.tier} words for this topic · ${learned}/${items.length} learned · ${(lex.learned || 0) + (lex.strong || 0)} learned in all topics`)
      : "Preparing the topic's words…";

  useEffect(() => {
    if (tab === "transcript" && paneRef.current) paneRef.current.scrollTop = paneRef.current.scrollHeight;
  }, [live.log, tab]);

  const explain = (text: string) => {
    live.boardRef.current?.board.hold();
    live.send({ type: "explain", item: { kind: "word", text } });
    setAsked(text);
    setTimeout(() => setAsked(""), 1500);
  };

  return (
    <aside className="side">
      <div className="tabs" role="tablist">
        <button className={"tab" + (tab === "words" ? " active" : "")} role="tab" onClick={() => setTab("words")}>
          {deck.intensive ? "Lesson words" : "Topic words"}</button>
        <button className={"tab" + (tab === "transcript" ? " active" : "")} role="tab" onClick={() => setTab("transcript")}>Transcript</button>
      </div>
      <div className={"pane" + (tab === "words" ? "" : " hidden")} id="pane-words">
        <div className="pane-head" id="words-head">{head}</div>
        <ul className="words" id="words">
          {items.map((it) => <WordRow key={it.text} it={it} asked={asked === it.text} onClick={() => explain(it.text)} />)}
        </ul>
        <div className={"label small" + (due.length ? "" : " hidden")} id="due-label">
          {deck.intensive ? "From earlier lessons - review" : "Old words - use them again"}</div>
        <ul className="words due" id="due">
          {due.map((it) => <WordRow key={it.text} it={it} asked={false}
                                    onClick={() => live.send({ type: "explain", item: { kind: "word", text: it.text } })} />)}
        </ul>
      </div>
      <div className={"pane" + (tab === "transcript" ? "" : " hidden")} id="pane-transcript" ref={paneRef}>
        <ol className="transcript" id="transcript">
          {live.log.map((l) => (
            <li key={l.id} className={l.kind === "plain" ? "" : l.kind}>
              {l.who ? <><span className="who">{l.who}</span>{" "}{l.text}</> : l.text}
            </li>
          ))}
        </ol>
      </div>
    </aside>
  );
}

function WordRow({ it, onClick, asked }: { it: any; onClick: () => void; asked: boolean }) {
  const kind = it.kind === "phrasal" ? "phrasal" : it.kind === "collocation" ? "colloc." : it.kind === "expression" ? "expr." : "word";
  return (
    <li tabIndex={0} className={"word s" + it.stage + (it.now ? " now" : "") + (asked ? " asked" : "")} onClick={onClick}>
      <div className="word-top">
        <span className="word-text">{it.text}</span>
        <span className={"badge " + it.kind}>{kind}</span>
        <span className="dots">{[1, 2, 3, 4].map((i) => <span key={i} className={"d" + (i <= it.stage ? " on" : "")} />)}</span>
        <span className="word-count" title={`used ${it.uses} times, on ${it.days} different days`}>
          {it.uses ? `${it.uses}× · ${it.days}d` : "0×"}</span>
      </div>
      {(it.meaning || it.native) && (
        <div className="word-meaning">{[it.meaning, it.native && `· ${it.native}`].filter(Boolean).join(" ")}</div>
      )}
    </li>
  );
}

// ── The controls: the microphone and your voice as a wave, typing, interrupt ─

const BANDS = 24;
const WAVE_RGB: Record<string, number[]> = {
  open: [18, 105, 90], speaking: [199, 90, 43], thinking: [201, 138, 10], off: [178, 58, 58], wait: [148, 139, 120],
};

function Controls() {
  const live = useLive();
  const [typing, setTyping] = useState(false);
  const [text, setText] = useState("");
  const wave = useRef<HTMLCanvasElement>(null);
  const hint = useRef<HTMLSpanElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const now = useRef({ started: false, muted: false, state: "SLEEPING" });
  now.current = { started: live.started, muted: live.muted, state: live.state };

  // Rounded bars that are the real voice, mirrored left and right. Quiet: a
  // row of dots with a slow shimmer running through them.
  useEffect(() => {
    const canvas = wave.current;
    if (!canvas) return;
    const audio = live.audio;
    const bars = new Array(BANDS).fill(0);
    let level = 0, tick = 0, raf = 0;
    const draw = () => {
      const { started, muted, state } = now.current;
      const dpr = window.devicePixelRatio || 1;
      const w = canvas.clientWidth, h = canvas.clientHeight;
      if (w && canvas.width !== Math.round(w * dpr)) { canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr); }
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      tick += 1;
      const speaking = state === "SPEAKING" || (started && audio.busy(0));
      const hearing = started && !muted && !speaking && state === "LISTENING";
      document.body.dataset.mic = started && !muted && (state === "LISTENING" || state === "SPEAKING") ? "open" : "wait";
      const source = muted || !started ? null : speaking ? "out" : hearing ? "in" : null;
      const bands = source ? audio.spectrum(source, BANDS) : new Array(BANDS).fill(0);
      level += ((source === "in" ? audio.inputLevel() : source === "out" ? audio.outputLevel() : 0) - level) * 0.2;
      const rgb = muted ? WAVE_RGB.off : speaking ? WAVE_RGB.speaking
        : state === "THINKING" ? WAVE_RGB.thinking : hearing ? WAVE_RGB.open : WAVE_RGB.wait;
      const total = BANDS * 2;
      const slot = w / total, bw = Math.max(2.5, Math.min(7, slot * 0.55)), mid = h / 2;
      for (let i = 0; i < BANDS; i++) {
        const v = level > 0.02 ? Math.pow(bands[i], 1.6) : 0;
        const shimmer = muted || !started ? 0 : 0.5 + 0.5 * Math.sin(tick * 0.06 - i * 0.45);
        const goal = Math.max(v, shimmer * 0.06);
        bars[i] += (goal - bars[i]) * (goal > bars[i] ? 0.5 : 0.18);
        const bh = Math.max(bw, bars[i] * (h - 2));
        const alpha = 0.35 + 0.65 * Math.min(1, bars[i] * 2.5);
        ctx.fillStyle = `rgba(${rgb.join(",")}, ${alpha})`;
        for (const side of [-1, 1]) {
          const cx = w / 2 + side * (i + 0.5) * slot;
          ctx.beginPath();
          ctx.roundRect(cx - bw / 2, mid - bh / 2, bw, bh, bw / 2);
          ctx.fill();
        }
      }
      if (hint.current) {
        hint.current.textContent = !started ? "Press Start to begin"
          : muted ? "Microphone off - click the mic"
          : speaking ? "LangVis is speaking - talk to cut in"
          : state === "THINKING" ? "Thinking…"
          : state !== "LISTENING" ? "Connecting…"
          : level > 0.04 ? "Listening…" : "Your turn - just talk";
      }
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [live.audio]);

  useEffect(() => { if (typing) inputRef.current?.focus(); }, [typing]);

  return (
    <footer className="controls">
      <div className={"voicebar" + (typing ? " hidden" : "")} id="voicebar">
        <button className="mic-toggle" id="mic" type="button" aria-pressed={!live.muted} aria-label="Microphone"
                title={live.muted ? "Microphone off - click to turn it on (F4)" : "Microphone on - click to turn it off (F4)"}
                onClick={() => live.send({ type: "mute", value: !live.muted })}>
          <MicOnIcon />
          <MicOffIcon />
        </button>
        <canvas id="wave" aria-hidden="true" ref={wave} />
        <span className="voice-hint" id="voice-hint" ref={hint}>Just talk - I&apos;m listening</span>
      </div>
      <form className={"compose" + (typing ? "" : " hidden")} id="compose"
            onSubmit={(e) => {
              e.preventDefault();
              if (!text.trim()) return;
              live.send({ type: "text", text: text.trim() });
              setText("");
            }}>
        <input ref={inputRef} id="text" type="text" autoComplete="off" placeholder="Type a sentence and press Enter…"
               aria-label="Type a sentence" value={text} onChange={(e) => setText(e.target.value)} />
        <button className="send" type="submit" title="Send" aria-label="Send"><SendIcon /></button>
      </form>
      <div className="control-buttons">
        <button className={"icon-btn keyboard" + (typing ? " active" : "")} id="keyboard-btn" type="button"
                title="Type a message instead" aria-label="Type a message" onClick={() => setTyping((t) => !t)}>
          <KeyboardIcon />
        </button>
        <button className="btn ghost" id="interrupt" type="button"
                onClick={() => { live.audio.flush(); live.send({ type: "interrupt" }); }}>
          <StopIcon />
          Interrupt</button>
      </div>
    </footer>
  );
}
