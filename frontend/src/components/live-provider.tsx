"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
// The connection to the LangVis backend, shared by every page: the WebSocket,
// the voice (microphone out, tutor in), the status of the learner, and the
// messages that drive the board. The board itself (legacy/board.js, the tutor
// that walks on it) registers here while the Tutor or a course lesson is open.

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { Audio as VoiceAudio } from "@/legacy/audio.js";
import { AUTH_EVENT, getJson, wsUrl } from "@/lib/api";

export type Page = "home" | "lesson" | "tutor" | "courses" | "dictionary" | "grammar" | "account";

export type BoardApi = {
  board: any;
  walker: any;
  face: any;
};

export type LogLine = { id: number; kind: "sys" | "err" | "you" | "tutor-line" | "day" | "plain"; who?: string; text: string };

type StartWith = { track?: string; lesson?: number };

type Live = {
  audio: any;
  send: (m: any) => void;
  sendSoon: (m: any) => void;
  status: any;
  coaching: any;
  syllabus: any[];
  state: string;
  stateText: string;
  muted: boolean;
  started: boolean;
  needKey: boolean;
  // Another account signed in on this computer: this tab is no longer connected.
  seatTakenBy: string | null;
  setNeedKey: (v: boolean) => void;
  content: { title: string; text: string } | null;
  setContent: (c: { title: string; text: string } | null) => void;
  notice: { text: string; ok: boolean; id: number } | null;
  flash: (text: string, ok?: boolean) => void;
  log: LogLine[];
  loadHistory: () => void;
  page: Page;
  setPage: (p: Page) => void;
  begin: (startWith?: StartWith, on?: Page) => void;
  stop: () => void;
  switchLanguage: (name: string, then?: string) => void;
  registerBoard: (api: BoardApi | null) => void;
  boardRef: React.MutableRefObject<BoardApi | null>;
};

const Ctx = createContext<Live | null>(null);

export function useLive(): Live {
  const v = useContext(Ctx);
  if (!v) throw new Error("useLive outside LiveProvider");
  return v;
}

const STATE_TEXT: Record<string, string> = {
  LISTENING: "Your turn - speak", SPEAKING: "Speaking", THINKING: "Thinking…", SLEEPING: "Offline",
};

let lineId = 0;

function parseLine(text: string): LogLine {
  const m = /^([^:]{1,24}):\s?([\s\S]*)$/.exec(text);
  const who = m ? m[1] : "";
  const body = m ? m[2] : text;
  if (who === "SYS" || who === "NET") return { id: ++lineId, kind: "sys", text: body };
  if (who === "ERR") return { id: ++lineId, kind: "err", text: body };
  if (who) return { id: ++lineId, kind: who === "You" ? "you" : "tutor-line", who, text: body };
  return { id: ++lineId, kind: "plain", text };
}

export function LiveProvider({ children }: { children: React.ReactNode }) {
  const audioRef = useRef<any>(null);
  if (audioRef.current === null && typeof window !== "undefined") audioRef.current = new VoiceAudio();
  const wsRef = useRef<WebSocket | null>(null);
  const pending = useRef<any[]>([]);
  const boardRef = useRef<BoardApi | null>(null);

  const [status, setStatus] = useState<any>({});
  const [coaching, setCoaching] = useState<any>({});
  const [syllabus, setSyllabus] = useState<any[]>([]);
  const [state, setStateRaw] = useState("SLEEPING");
  const [stateText, setStateText] = useState("Offline");
  const [muted, setMuted] = useState(false);
  const [started, setStarted] = useState(false);
  const [needKey, setNeedKey] = useState(false);
  const [seatTakenBy, setSeatTakenBy] = useState<string | null>(null);
  const seatTaken = useRef(false);
  const [content, setContent] = useState<{ title: string; text: string } | null>(null);
  const [notice, setNotice] = useState<{ text: string; ok: boolean; id: number } | null>(null);
  const [log, setLog] = useState<LogLine[]>([]);
  const [page, setPage] = useState<Page>("home");

  // Latest values for callbacks that outlive a render.
  const live = useRef({ started: false, beginning: false, startedOn: "" as string, startWith: {} as StartWith,
                        freshStart: false, muted: false, state: "SLEEPING", page: "home" as Page, startOn: "" as string,
                        status: {} as any, switchingTo: "", tutorTurnOpen: false });
  live.current.muted = muted;
  live.current.page = page;
  live.current.status = status;

  // Replayed on the board when it mounts after the messages arrived.
  const lastBoard = useRef<{ lesson?: any; mode?: any; coaching?: any; speech?: string }>({});

  const send = useCallback((obj: any) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
  }, []);
  const sendSoon = useCallback((obj: any) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) send(obj);
    else pending.current.push(obj);
  }, [send]);

  const flash = useCallback((text: string, ok = true) => setNotice({ text, ok, id: Date.now() }), []);

  const setState = useCallback((value: string, text?: string) => {
    live.current.state = value;
    setStateRaw(value);
    setStateText(text || STATE_TEXT[value] || value);
    document.body.dataset.state = value;
    const b = boardRef.current;
    if (b) { b.face.set(value, live.current.muted); b.board.setState(value); }
  }, []);

  const addLog = useCallback((text: string) => {
    setLog((l) => {
      const next = [...l, parseLine(text)];
      return next.length > 700 ? next.slice(next.length - 700) : next;
    });
  }, []);

  const loadHistory = useCallback(async () => {
    const topic = (live.current.status.topic || {}).id || "";
    const res = await getJson(`/api/history?topic=${encodeURIComponent(topic)}`);
    if (!res) return;
    const lines: LogLine[] = [];
    let day = "";
    (res.lines || []).forEach((l: any) => {
      const d = (l.ts || "").slice(0, 10);
      if (d && d !== day) {
        day = d;
        lines.push({ id: ++lineId, kind: "day", text: new Date(d + "T12:00:00").toLocaleDateString(undefined,
          { weekday: "short", day: "numeric", month: "short" }) });
      }
      lines.push(parseLine(`${l.who}: ${l.text}`));
    });
    if (!res.lines.length) {
      lines.push({ id: ++lineId, kind: "sys",
                   text: `No conversation in ${(live.current.status.topic || {}).name || "this topic"} yet.` });
    }
    setLog(lines);
  }, []);

  // ── Starting and stopping ────────────────────────────────────────────────

  const stopped = useCallback(() => {
    live.current.started = false;
    live.current.beginning = false;
    setStarted(false);
    audioRef.current?.flush();
    setState("SLEEPING");
  }, [setState]);

  const go = useCallback(() => {
    const L = live.current;
    if (L.started) return;
    L.started = true;
    L.beginning = false;
    L.startedOn = L.startOn || L.page;
    L.startOn = "";
    setStarted(true);
    // The page decides the kind of lesson: the Tutor is free talk, a lesson is the course.
    if (!L.startWith.track && L.startWith.lesson === undefined) {
      L.startWith = { track: L.startedOn === "tutor" ? "normal" : "intensive" };
    }
    const speech = document.getElementById("speech-text");
    if (speech) speech.textContent = "Connecting - I will start talking in a moment.";
    L.freshStart = true;
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      send({ type: "start", fresh: true, ...L.startWith });
      L.freshStart = false;
      L.startWith = {};
    }
  }, [send]);

  const begin = useCallback(async (startWith?: StartWith, on?: Page) => {
    const L = live.current;
    if (startWith) L.startWith = startWith;
    if (on) L.startOn = on;   // the page the lesson belongs to (it may still be opening)
    if (L.started || L.beginning) return;
    L.beginning = true;
    const audio = audioRef.current;
    const micOk = await audio.start();
    if (!micOk) flash("The microphone is not available - you can still type.", false);
    if (audio.canPlay()) { go(); return; }
    const speech = document.getElementById("speech-text");
    if (speech) speech.textContent = "Click anywhere on the page - then I start talking.";
    const unlock = async () => {
      window.removeEventListener("pointerdown", unlock, true);
      window.removeEventListener("keydown", unlock, true);
      await audio.unlock();
      go();
    };
    window.addEventListener("pointerdown", unlock, true);
    window.addEventListener("keydown", unlock, true);
  }, [flash, go]);

  const stop = useCallback(() => {
    if (live.current.started) send({ type: "stop" });
    stopped();
  }, [send, stopped]);

  const switchLanguage = useCallback((name: string, then?: string) => {
    audioRef.current?.flush();
    send({ type: "language", value: name });
    flash(`Switching to ${name}…`);
    live.current.switchingTo = name;
    const target = then;
    const reload = () => { if (target) window.location.href = target; else window.location.reload(); };
    (live.current as any).afterSwitch = reload;
    setTimeout(reload, 4000);   // in case the new status is slow
  }, [flash, send]);

  // ── Messages from the server ─────────────────────────────────────────────

  const handle = useCallback((msg: any) => {
    const b = boardRef.current;
    switch (msg.type) {
      case "state": setState(msg.state); break;
      case "muted":
        setMuted(!!msg.value);
        live.current.muted = !!msg.value;
        document.body.dataset.muted = String(!!msg.value);
        setState(live.current.state);
        break;
      case "live_sentence": b?.board.showLive(msg.text, msg.final); break;
      case "hearing": b?.board.hearing(msg.value); break;
      case "mode": lastBoard.current.mode = msg; b?.board.setMode(msg.mode, msg.expect); break;
      case "lesson": lastBoard.current.lesson = msg.card || {}; b?.board.lesson(msg.card || {}); break;
      case "tutor_words":
        if (b) {
          if (!live.current.tutorTurnOpen && !msg.final) b.board.hideAnswers();
          b.walker.speech(msg.text, msg.final);
          b.board.onWords(msg.text);
        }
        live.current.tutorTurnOpen = !msg.final;
        if (msg.final) lastBoard.current.speech = msg.text;
        break;
      case "answers": b?.board.answers(msg); break;
      case "stopped": stopped(); break;
      case "reset":
        lastBoard.current = {};
        if (b) {
          b.board.reset();
          const sp = document.getElementById("speech-text");
          if (sp) {
            sp.textContent = "A fresh start - what I say is written here.";
            sp.closest(".speech")?.classList.add("empty");
          }
        }
        loadHistory();
        break;
      case "repeat": b?.board.repeat(msg); break;
      case "log": addLog(msg.text); break;
      case "log_history": loadHistory(); break;
      case "status": {
        const s = msg.data || {};
        if (!s.level) break;
        const topicChanged = (live.current.status.topic || {}).id !== (s.topic || {}).id;
        live.current.status = s;
        setStatus(s);
        if (topicChanged) loadHistory();
        document.body.dataset.track = s.track || "normal";
        // The new language is on: reload, so every page starts in it.
        const active = (s.modes || []).find((m: any) => m.active);
        if (live.current.switchingTo && active && active.name === live.current.switchingTo) {
          live.current.switchingTo = "";
          (live.current as any).afterSwitch?.();
        }
        break;
      }
      case "coaching": {
        const card = msg.data || {};
        lastBoard.current.coaching = card;
        setCoaching(card);
        b?.board.render(card);
        if (card.notice && card.notice_stamp !== (live.current as any).noticeStamp) {
          (live.current as any).noticeStamp = card.notice_stamp;
          flash(card.notice, false);
        }
        break;
      }
      case "syllabus": setSyllabus(msg.data || []); break;
      case "flush": audioRef.current?.flush(); break;
      case "notice": flash(msg.text, msg.ok); break;
      case "need_key": setNeedKey(!!msg.value); break;
      case "seat_taken":
        seatTaken.current = true;
        stopped();
        setSeatTakenBy(msg.by || "Another account");
        break;
      case "signed_out": window.dispatchEvent(new Event(AUTH_EVENT)); break;
      case "content": setContent({ title: msg.title, text: msg.text }); break;
    }
  }, [addLog, flash, loadHistory, setState, stopped]);

  // ── The socket ───────────────────────────────────────────────────────────

  useEffect(() => {
    let closed = false;
    let retry: ReturnType<typeof setTimeout> | undefined;
    const audio = audioRef.current;
    const connect = () => {
      const ws = new WebSocket(wsUrl());
      ws.binaryType = "arraybuffer";
      wsRef.current = ws;
      ws.onopen = () => {
        pending.current.splice(0).forEach((m) => ws.send(JSON.stringify(m)));
        const L = live.current;
        if (L.freshStart) {                 // Start was pressed before the socket was open
          ws.send(JSON.stringify({ type: "start", fresh: true, ...L.startWith }));
          L.freshStart = false;
          L.startWith = {};
        } else if (L.started) {
          // The connection (or the server) was lost: the lesson does not start
          // again by itself - Start is pressed again.
          stopped();
        }
      };
      ws.onmessage = (e) => {
        if (e.data instanceof ArrayBuffer) { audio?.play(e.data); return; }
        let msg: any;
        try { msg = JSON.parse(e.data); } catch { return; }
        handle(msg);
      };
      ws.onclose = () => {
        if (closed || seatTaken.current) return;
        // Refused or dropped: maybe the account is signed out - the page asks.
        window.dispatchEvent(new Event(AUTH_EVENT));
        setState("SLEEPING", "Reconnecting…");
        retry = setTimeout(connect, 1500);
      };
    };
    connect();
    // The microphone always goes to the server, which decides.
    audio.onMicBlock = (buffer: ArrayBuffer) => {
      const ws = wsRef.current;
      if (!live.current.muted && ws && ws.readyState === WebSocket.OPEN) ws.send(buffer);
    };
    setState("SLEEPING");
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "F4") { e.preventDefault(); send({ type: "mute", value: !live.current.muted }); }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      closed = true;
      clearTimeout(retry);
      document.removeEventListener("keydown", onKey);
      wsRef.current?.close();
    };
  }, [handle, send, setState, stopped]);

  // The page changes: a lesson started on another page stops (the course
  // lesson and the Tutor are two places), and the body knows where it is.
  useEffect(() => {
    document.body.dataset.page = page;
    const L = live.current;
    if (L.started && page !== L.startedOn) { send({ type: "stop" }); stopped(); }
  }, [page, send, stopped]);

  const registerBoard = useCallback((api: BoardApi | null) => {
    boardRef.current = api;
    if (!api) return;
    // Catch up with what arrived before the board was on the page.
    api.face.set(live.current.state, live.current.muted);
    api.board.setState(live.current.state);
    const last = lastBoard.current;
    if (last.coaching) api.board.render(last.coaching);
    if (last.lesson) api.board.lesson(last.lesson);
    if (last.mode) api.board.setMode(last.mode.mode, last.mode.expect);
  }, []);

  const value = useMemo<Live>(() => ({
    audio: audioRef.current, send, sendSoon, status, coaching, syllabus, state, stateText, muted, started,
    needKey, setNeedKey, seatTakenBy, content, setContent, notice, flash, log, loadHistory, page, setPage,
    begin, stop, switchLanguage, registerBoard, boardRef,
  }), [send, sendSoon, status, coaching, syllabus, state, stateText, muted, started, needKey, seatTakenBy, content,
       notice, flash, log, loadHistory, page, begin, stop, switchLanguage, registerBoard]);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
