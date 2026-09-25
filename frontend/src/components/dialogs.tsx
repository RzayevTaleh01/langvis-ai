"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */
// Every dialog of the page: settings (with the API keys and what LangVis
// remembers), the grammar syllabus, a topic of your own, the first API key,
// a text the tutor opened, and "which language do you want to learn?".

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { TrashIcon } from "@/components/icons";
import { useLive } from "@/components/live-provider";
import { getJson, postJson } from "@/lib/api";

type OpenProps = { open: boolean; onOpenChange: (open: boolean) => void };

const TITLE = "font-[Georgia,serif] text-[26px] leading-tight font-normal text-[var(--ink-strong)]";

// ── Settings ─────────────────────────────────────────────────────────────────

export function SettingsDialog({ open, onOpenChange }: OpenProps) {
  const { flash } = useLive();
  const [data, setData] = useState<any>(null);
  const [values, setValues] = useState<Record<string, any>>({});
  const [keys, setKeys] = useState<any[]>([]);
  const [keyNew, setKeyNew] = useState("");
  const [keysNote, setKeysNote] = useState("");
  const [memory, setMemory] = useState<any[]>([]);
  const [q, setQ] = useState("");

  const loadKeys = async () => {
    const res = await getJson("/api/keys");
    setKeys((res && res.keys) || []);
  };

  useEffect(() => {
    if (!open) return;
    (async () => {
      const d = await getJson("/api/settings");
      if (!d) { flash("Settings could not be loaded.", false); onOpenChange(false); return; }
      setData(d);
      const v: Record<string, any> = { user_name: d.user_name || "", voice: d.voice };
      d.plugins.forEach((pl: any) => pl.fields.forEach((f: any) => {
        v[`${pl.namespace}::${f.key}`] = pl.values[f.key] ?? f.default;
      }));
      setValues(v);
      setMemory((await getJson("/api/memory")) || []);
      loadKeys();
    })();
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  const keyAction = async (body: any) => {
    setKeysNote(body.action === "add" ? "Checking the key…" : "");
    const res = await postJson("/api/keys", body);
    setKeysNote(res && res.ok ? "" : (res && res.error) || "It did not work.");
    if (res && res.ok) {
      setKeyNew("");
      loadKeys();
      flash(body.action === "remove" ? "Key removed." : "Key saved.");
    }
  };

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    const body: any = { plugins: {} };
    Object.entries(values).forEach(([k, v]) => {
      const [ns, key] = k.includes("::") ? k.split("::") : ["", k];
      if (ns) (body.plugins[ns] ||= {})[key] = v;
      else body[key] = v;
    });
    const res = await postJson("/api/settings", body);
    onOpenChange(false);
    flash(res && res.ok ? "Settings saved - reconnecting the tutor." : "Settings could not be saved.", !!(res && res.ok));
  };

  const shown = memory.filter((r) => !q || `${r.key} ${r.value} ${r.category}`.toLowerCase().includes(q.toLowerCase()));

  const field = (label: string, input: React.ReactNode, key: string) => (
    <label className="field" key={key}><span>{label}</span>{input}</label>
  );
  const choice = (k: string, options: string[]) => (
    <Select value={String(values[k] ?? "")} onValueChange={(v) => setValues((s) => ({ ...s, [k]: v }))}>
      <SelectTrigger className="w-full bg-[var(--panel)]"><SelectValue /></SelectTrigger>
      <SelectContent>{options.map((o) => <SelectItem key={o} value={o}>{o}</SelectItem>)}</SelectContent>
    </Select>
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[640px] p-7 max-h-[90vh] overflow-auto">
        <form onSubmit={save} className="grid gap-4">
          <DialogHeader><DialogTitle className={TITLE}>Settings</DialogTitle></DialogHeader>
          {data && (
            <div className="settings-grid">
              {field("My name", <Input value={values.user_name || ""}
                onChange={(e) => setValues((s) => ({ ...s, user_name: e.target.value }))} />, "user_name")}
              {field("Tutor's voice", choice("voice", data.voices || []), "voice")}
              {data.plugins.map((pl: any) => pl.fields.filter((f: any) => f.key !== "speak_every").map((f: any) => {
                const k = `${pl.namespace}::${f.key}`;
                return f.type === "toggle"
                  ? field(f.label, <Switch checked={values[k] === true || values[k] === "true"}
                      onCheckedChange={(v) => setValues((s) => ({ ...s, [k]: v }))} />, k)
                  : field(f.label, choice(k, f.options || []), k);
              }))}
            </div>
          )}

          <div className="settings-memory">
            <div className="memory-head">
              <h2>Gemini API keys</h2>
              <span className="muted">{`${keys.length} key${keys.length === 1 ? "" : "s"}`}</span>
            </div>
            <p className="muted small-text">The main key runs the lesson. When a key reaches its free daily limit,
              LangVis moves to another model, then to your extra keys. Keys are saved on this computer only -
              get one free at <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener">Google AI Studio</a>.</p>
            <ul className="memory-list">
              {keys.map((k) => (
                <li key={k.id}>
                  <div>
                    <div className={"mem-key" + (k.main ? " key-main" : "")}>{k.main ? "main key" : "extra key"}</div>
                    <div className="mem-value">{k.masked}</div>
                  </div>
                  {!k.main && (
                    <div className="key-actions">
                      <button type="button" className="link" onClick={() => keyAction({ action: "main", id: k.id })}>make main</button>
                      <button type="button" className="forget" title="Remove this key" aria-label={`Remove key ${k.masked}`}
                              onClick={() => keyAction({ action: "remove", id: k.id })}><TrashIcon /></button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
            <div className="key-add">
              <Input type="password" autoComplete="off" placeholder="Paste a Gemini API key…" value={keyNew}
                     aria-label="New Gemini API key" onChange={(e) => setKeyNew(e.target.value)}
                     onKeyDown={(e) => {
                       if (e.key !== "Enter") return;
                       e.preventDefault();
                       if (keyNew.trim()) keyAction({ action: "add", key: keyNew.trim(), main: false });
                     }} />
              <button className="btn" type="button"
                      onClick={() => keyNew.trim() && keyAction({ action: "add", key: keyNew.trim(), main: false })}>Add as extra</button>
              <button className="btn" type="button"
                      onClick={() => keyNew.trim() && keyAction({ action: "add", key: keyNew.trim(), main: true })}>Set as main</button>
            </div>
            <p className="note">{keysNote}</p>
          </div>

          <div className="settings-memory">
            <div className="memory-head">
              <h2>What LangVis remembers about you</h2>
              <span className="muted">{`${memory.length} facts`}</span>
            </div>
            <Input type="search" placeholder="Search memory…" aria-label="Search memory" value={q} onChange={(e) => setQ(e.target.value)} />
            <ul className="memory-list">
              {!shown.length && <li>{memory.length ? "Nothing matches." : "Nothing remembered yet."}</li>}
              {shown.map((r) => (
                <li key={`${r.category}/${r.key}`}>
                  <div>
                    <div className="mem-key">{`${r.category} · ${r.key.replace(/_/g, " ")}`}</div>
                    <div className="mem-value">{r.value}</div>
                  </div>
                  <button type="button" className="forget" title="Forget this" aria-label={`Forget ${r.key}`}
                          onClick={async () => {
                            const res = await postJson("/api/memory/forget", { category: r.category, key: r.key });
                            if (res && res.ok) setMemory((m) => m.filter((x) => x !== r));
                          }}><TrashIcon /></button>
                </li>
              ))}
            </ul>
          </div>

          <div className="actions end">
            <button className="btn" type="button" onClick={() => onOpenChange(false)}>Cancel</button>
            <button className="btn primary" type="submit">Save</button>
          </div>
          <p className="muted">Saving restarts the connection so the tutor uses the new settings. A new voice starts a fresh lesson.</p>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ── The grammar syllabus (Tutor) ─────────────────────────────────────────────

export function UnitsDialog({ open, onOpenChange }: OpenProps) {
  const { syllabus, send } = useLive();
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[640px] p-7 max-h-[90vh] overflow-auto">
        <DialogHeader>
          <DialogTitle className={TITLE}>Grammar syllabus</DialogTitle>
          <DialogDescription className="card-sub">Every grammar rule from A1 to B2. There is no order: whatever you
            use is measured from your own speech. Click a rule to see it explained on the board.</DialogDescription>
        </DialogHeader>
        <div className="units-list">
          {syllabus.map((band: any) => (
            <section className="units-stage" key={band.band}>
              <div className="units-stage-head">
                <strong>{band.band}</strong>
                <span>{`${band.counts.strong}/${band.total} known · ${band.counts.learning} learning · ${band.counts.weak} weak · ${band.counts.new} not used yet`}</span>
              </div>
              {band.skills.map((k: any) => {
                const m = k.mastery ?? 0;
                const tone = k.mastery === null ? "none" : m >= 70 ? "strong" : m >= 40 ? "mid" : "weak";
                return (
                  <button type="button" key={k.id} className={"grammar-row " + k.status}
                          onClick={() => {
                            onOpenChange(false);
                            send({ type: "explain", item: { kind: "fix", skill_id: k.id, skill: k.name, wrong: "", right: "" } });
                          }}>
                    <span className="unit-title">{k.name}</span>
                    <span className="grammar-hint">{k.hint}</span>
                    <span className="meter"><span className={"meter-fill " + tone} style={{ width: `${m}%` }} /></span>
                    <span className={"status " + k.status}>{k.status === "new" ? "not used yet" : k.status === "strong" ? "known" : k.status}</span>
                  </button>
                );
              })}
            </section>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ── A topic of your own, or the scenario of any topic ────────────────────────

export function CustomTopicDialog({ open, onOpenChange, topic }: OpenProps & { topic: any | null }) {
  const { send } = useLive();
  const [name, setName] = useState("");
  const [prompt, setPrompt] = useState("");
  useEffect(() => {
    if (!open) return;
    setName(topic ? topic.name : "");
    setPrompt(topic ? topic.prompt || "" : "");
  }, [open, topic]);
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (topic) send({ type: "topic", id: topic.id, prompt: prompt.trim() });
    else {
      if (!name.trim()) return;
      send({ type: "topic", custom: name.trim(), prompt: prompt.trim() });
    }
    onOpenChange(false);
  };
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[640px] p-7">
        <form onSubmit={submit} className="grid gap-4">
          <DialogHeader>
            <DialogTitle className={TITLE}>{topic ? `Scenario: ${topic.name}` : "Your own topic"}</DialogTitle>
            <DialogDescription>{topic
              ? "Tell the tutor how to talk with you in this topic - a role, a place, a situation."
              : "Anything you want to talk about - football, programming, a coffee shop. Its words are prepared once."}</DialogDescription>
          </DialogHeader>
          <label className="field">
            <span>Topic</span>
            <Input maxLength={40} autoComplete="off" placeholder="e.g. In the coffee shop" aria-label="Topic name"
                   value={name} disabled={!!topic} autoFocus={!topic} onChange={(e) => setName(e.target.value)} />
          </label>
          <label className="field">
            <span>How should the tutor talk with you? (optional)</span>
            <Textarea rows={6} maxLength={2000} value={prompt} autoFocus={!!topic} onChange={(e) => setPrompt(e.target.value)}
                      placeholder="e.g. Be a barista in a busy coffee shop. I am the customer ordering a drink. Ask about size, milk and snacks." />
          </label>
          <div className="actions">
            <button className="btn" type="button" onClick={() => onOpenChange(false)}>Cancel</button>
            <button className="btn primary" type="submit">{topic ? "Save" : "Start topic"}</button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ── The first Gemini key ─────────────────────────────────────────────────────

export function KeyDialog() {
  const { needKey, setNeedKey, started, send } = useLive();
  const [key, setKey] = useState("");
  const [note, setNote] = useState("");
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await postJson("/api/key", { key: key.trim() });
    if (!res || !res.ok) { setNote((res && res.error) || "Could not save the key."); return; }
    setKey("");
    setNote("");
    setNeedKey(false);
    if (started) send({ type: "start" });
  };
  return (
    <Dialog open={needKey}>
      <DialogContent showCloseButton={false} className="sm:max-w-[420px] p-7 text-center"
                     onInteractOutside={(e) => e.preventDefault()} onEscapeKeyDown={(e) => e.preventDefault()}>
        <form onSubmit={submit} className="grid gap-3">
          <DialogHeader><DialogTitle className={TITLE + " text-center"}>Gemini API key</DialogTitle></DialogHeader>
          <p>Paste your free key from <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener">Google AI Studio</a>. It is saved on this computer only.</p>
          <Input type="password" autoComplete="off" placeholder="AIza…" aria-label="Gemini API key"
                 value={key} onChange={(e) => setKey(e.target.value)} />
          <button className="btn primary justify-center" type="submit">Save key</button>
          <p className="note">{note}</p>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ── A text the tutor opened (a progress file, a plan) ────────────────────────

export function ContentDialog() {
  const { content, setContent } = useLive();
  return (
    <Dialog open={!!content} onOpenChange={(o) => { if (!o) setContent(null); }}>
      <DialogContent className="sm:max-w-[640px] p-7">
        <DialogHeader><DialogTitle className={TITLE}>{content?.title}</DialogTitle></DialogHeader>
        <pre className="content">{content?.text}</pre>
        <DialogFooter><button className="btn" type="button" onClick={() => setContent(null)}>Close</button></DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Start learning a new language: which one? ───────────────────────────────

export function useCatalog() {
  const [catalog, setCatalog] = useState<any>(null);
  useEffect(() => { getJson("/api/catalog").then(setCatalog); }, []);
  return catalog;
}

export function LanguageChoiceDialog({ open, onOpenChange }: OpenProps) {
  const { status, switchLanguage } = useLive();
  const router = useRouter();
  const catalog = useCatalog();
  const current = useMemo(() => ((status.modes || []).find((m: any) => m.active) || {}).key, [status]);
  const pick = (name: string, key: string) => {
    onOpenChange(false);
    if (key === current) router.push("/courses/");
    else switchLanguage(name, "/courses/");
  };
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[640px] p-7">
        <DialogHeader>
          <DialogTitle className={TITLE}>Which language do you want to learn?</DialogTitle>
          <DialogDescription>Your level, course and words are kept separately for each language.</DialogDescription>
        </DialogHeader>
        <div className="lang-options">
          {((catalog && catalog.courses) || []).map((c: any) => (
            <button type="button" key={c.key} className={"lang-option" + (c.key === current ? " current" : "")}
                    onClick={() => pick(c.name, c.key)}>
              <strong>{c.name}</strong>
              <span>{`${c.levels} · ${c.lessons} lessons`}</span>
              <span className="lang-option-note">{c.key === current ? "You are learning it now" : c.learner}</span>
            </button>
          ))}
        </div>
        <DialogFooter className="sm:justify-center"><button className="btn" type="button" onClick={() => onOpenChange(false)}>Cancel</button></DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

