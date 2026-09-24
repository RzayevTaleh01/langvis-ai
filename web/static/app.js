// LangVis in the browser: the socket to the local server, the pages, the header.
import { Audio } from "/static/audio.js";
import { TutorFace, TutorWalker } from "/static/tutor.js";
import { Board } from "/static/board.js";
import { loadAccount, loadDictionary, loadGrammar, loadHome, loadIntensive, renderCourseSide,
         renderLanguageChoice } from "/static/pages.js";

const $ = (id) => document.getElementById(id);
const audio = new Audio();
let ws = null;
let started = false;
let startWith = {};   // a course or course lesson that goes with the next Start
let startedOn = "";   // the page the lesson was started on
let lastPage = "";    // the page shown before this one
let freshStart = false;
let tutorTurnOpen = false;  // the tutor is in the middle of a turn     // the first "start" of this page opens a new lesson
let muted = false;
let state = "SLEEPING";
let status = {};
let syllabus = [];

const face = new TutorFace($("tutor"), audio);
const walker = new TutorWalker($("board"), $("tutor"), face);
const board = new Board({ walker, audio, send });

// ── Socket ──────────────────────────────────────────────────────────────────

function connect() {
  ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws`);
  ws.binaryType = "arraybuffer";
  // After a lost connection the lesson simply carries on.
  ws.onopen = () => {
    pending.splice(0).forEach(send);
    if (freshStart) {                 // Start was pressed before the socket was open
      send(Object.assign({ type: "start", fresh: true }, startWith));
      freshStart = false;
      startWith = {};
    } else if (started) {
      // The connection (or the server) was lost: the lesson does not start
      // again by itself - Start is pressed again.
      stopped();
    }
  };
  ws.onmessage = (e) => {
    if (e.data instanceof ArrayBuffer) { audio.play(e.data); return; }
    let msg;
    try { msg = JSON.parse(e.data); } catch (_) { return; }
    (handlers[msg.type] || (() => {}))(msg);
  };
  ws.onclose = () => {
    setState("SLEEPING", "Reconnecting…");
    setTimeout(connect, 1500);
  };
}

function send(obj) {
  if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(obj));
}

// A choice made before the socket is open is sent as soon as it opens.
const pending = [];
function sendSoon(obj) {
  if (ws && ws.readyState === WebSocket.OPEN) send(obj);
  else pending.push(obj);
}

// The microphone always goes to the server, which decides: the learner may cut
// in over the tutor with a clear voice, and the tutor's own echo is dropped.
audio.onMicBlock = (buffer) => {
  if (!muted && ws && ws.readyState === WebSocket.OPEN) ws.send(buffer);
};

const handlers = {
  state: (m) => setState(m.state),
  muted: (m) => setMuted(m.value),
  live_sentence: (m) => board.showLive(m.text, m.final),
  hearing: (m) => board.hearing(m.value),
  mode: (m) => board.setMode(m.mode, m.expect),
  lesson: (m) => board.lesson(m.card || {}),
  tutor_words: (m) => {
    // A new turn of the tutor's: the answers to its last question are done.
    if (!tutorTurnOpen && !m.final) board.hideAnswers();
    tutorTurnOpen = !m.final;
    walker.speech(m.text, m.final);
    board.onWords(m.text);
  },
  answers: (m) => board.answers(m),
  stopped: () => stopped(),
  reset: () => {
    board.reset();
    loadHistory();
    $("speech-text").textContent = "A fresh start - what I say is written here.";
    $("speech-text").closest(".speech").classList.add("empty");
  },
  repeat: (m) => board.repeat(m),
  log: (m) => addLog(m.text),
  log_history: () => loadHistory(),
  status: (m) => renderStatus(m.data || {}),
  coaching: (m) => renderCoaching(m.data || {}),
  syllabus: (m) => { syllabus = m.data || []; if (!$("units-overlay").classList.contains("hidden")) renderUnits(); },
  flush: () => audio.flush(),
  notice: (m) => flash(m.text, m.ok),
  need_key: (m) => $("key-overlay").classList.toggle("hidden", !m.value),
  content: (m) => {
    $("content-title").textContent = m.title;
    $("content-text").textContent = m.text;
    $("content-overlay").classList.remove("hidden");
  },
};

// ── State ───────────────────────────────────────────────────────────────────

const STATE_TEXT = { LISTENING: "Your turn - speak", SPEAKING: "Speaking", THINKING: "Thinking…", SLEEPING: "Offline" };

function setState(value, text) {
  state = value;
  document.body.dataset.state = value;
  face.set(value, muted);
  board.setState(value);
  $("tutor-state").textContent = muted && value !== "SPEAKING" ? "Microphone off" : (text || STATE_TEXT[value] || value);
}

function setMuted(value) {
  muted = !!value;
  document.body.dataset.muted = String(muted);
  $("mic").setAttribute("aria-pressed", String(!muted));
  $("mic").title = muted ? "Microphone off - click to turn it on (F4)" : "Microphone on - click to turn it off (F4)";
  setState(state);
}

function flash(text, ok = true) {
  const n = $("notice");
  n.textContent = text;
  n.classList.toggle("bad", !ok);
  n.classList.remove("hidden");
  clearTimeout(flash.t);
  flash.t = setTimeout(() => n.classList.add("hidden"), 5000);
}

// ── Header ──────────────────────────────────────────────────────────────────

function renderStatus(s) {
  if (!s.level) return;
  const topicChanged = (status.topic || {}).id !== (s.topic || {}).id;
  status = s;
  if (topicChanged) loadHistory();
  const lvl = $("chip-level");
  lvl.textContent = "";
  const b = document.createElement("strong");
  b.textContent = s.level;
  lvl.append(b, ` · ${s.score}/100 → ${s.goal}`);
  document.body.dataset.track = s.track || "normal";
  const it = s.intensive;
  renderLanguages(s);
  if (it) renderCourseSide(it, act);
  const g = s.grammar || {};
  $("unit-name").textContent = g.total ? `Grammar · ${g.strong}/${g.total} known · ${g.weak} weak` : "Grammar";
  renderTopics(s);

  if (!s.lexicon_ready) {
    $("words-head").textContent = s.lexicon_building
      ? `Preparing the words for ${(s.topic || {}).name}… (once only)` : "The topic's words are on their way…";
  }
}

// The language select: every language with its own level. Choosing one
// switches the whole lesson - level, course, words - to that language.
function renderLanguages(s) {
  const modes = (s.modes || []).filter((m) => m.enabled);
  const active = modes.find((m) => m.active);
  // The new language is on: reload, so every page starts in it.
  if (switchingTo && active && active.name === switchingTo) { location.reload(); return; }
  if (active) $("lang-name").textContent = active.name;
  const menu = $("lang-menu");
  const sig = JSON.stringify(modes.map((m) => [m.name, m.active]));
  if (menu.dataset.sig === sig) return;
  menu.dataset.sig = sig;
  menu.textContent = "";
  const li = document.createElement("li");
  const h = document.createElement("h6");
  h.className = "dropdown-header";
  h.textContent = "Language to learn";
  li.append(h);
  menu.append(li);
  modes.forEach((m) => {
    const item = document.createElement("li");
    const b = document.createElement("button");
    b.type = "button";
    b.className = "dropdown-item" + (m.active ? " active" : "");
    const name = document.createElement("span");
    name.textContent = m.name;
    b.append(name);
    b.addEventListener("click", () => { if (!m.active) switchLanguage(m.name); });
    item.append(b);
    menu.append(item);
  });
}
function switchLanguage(name) {
  audio.flush();
  send({ type: "language", value: name });
  $("lang-name").textContent = `${name}…`;
  flash(`Switching to ${name}…`);
  switchingTo = name;
  setTimeout(() => location.reload(), 4000);   // in case the new status is slow
}
let switchingTo = "";

// The topic dropdown (Bootstrap): started topics first, then the rest, then
// "your own".
function renderTopics(s) {
  $("topic-name").textContent = (s.topic || {}).name || "Topic";
  const sig = JSON.stringify([(s.topics || []).map((t) => [t.id, t.started]), (s.topic || {}).id]);
  const menu = $("topic-menu");
  if (menu.dataset.sig === sig) return;
  menu.dataset.sig = sig;
  menu.textContent = "";
  const header = (text) => {
    const li = document.createElement("li");
    const h = document.createElement("h6");
    h.className = "dropdown-header";
    h.textContent = text;
    li.append(h);
    menu.append(li);
  };
  const item = (t) => {
    const li = document.createElement("li");
    li.className = "topic-li";
    const a = document.createElement("button");
    a.type = "button";
    a.className = "dropdown-item" + (t.current ? " active" : "");
    const name = document.createElement("span");
    if (t.started) {
      const dot = document.createElement("span");
      dot.className = "started-dot";
      dot.title = "started";
      name.append(dot);
    }
    name.append(t.custom ? `${t.name}` : t.name);
    const az = document.createElement("span");
    az.className = "az";
    az.textContent = t.custom ? "my topic" : "";
    a.append(name, az);
    a.addEventListener("click", () => { if (!t.current) send({ type: "topic", id: t.id }); });
    li.append(a);
    const edit = document.createElement("button");
    edit.type = "button";
    edit.className = "topic-edit";
    edit.title = t.prompt ? `Scenario: ${t.prompt}` : "Add a scenario for this topic";
    edit.setAttribute("aria-label", `Scenario for ${t.name}`);
    edit.textContent = t.prompt ? "✎•" : "✎";
    edit.addEventListener("click", (e) => { e.stopPropagation(); openTopicDialog(t); });
    li.append(edit);
    if (t.started && t.id !== "free") {
      li.classList.add("deletable");
      const del = document.createElement("button");
      del.type = "button";
      del.className = "topic-del";
      del.title = `Delete ${t.name}`;
      del.setAttribute("aria-label", `Delete topic ${t.name}`);
      del.textContent = "✕";
      del.addEventListener("click", (e) => {
        e.stopPropagation();
        if (confirm(`Delete the topic "${t.name}"? Its words stay in your dictionary.`)) {
          send({ type: "delete_topic", id: t.id });
        }
      });
      li.append(del);
    }
    menu.append(li);
  };
  const topics = s.topics || [];
  const started = topics.filter((t) => t.started);
  if (started.length) { header("My topics"); started.forEach(item); }
  const rest = topics.filter((t) => !t.started);
  if (rest.length) { header("More topics"); rest.forEach(item); }
  const li = document.createElement("li");
  li.innerHTML = '<hr class="dropdown-divider">';
  menu.append(li);
  const own = document.createElement("li");
  const b = document.createElement("button");
  b.type = "button";
  b.className = "dropdown-item own";
  b.textContent = "+ My own topic…";
  b.addEventListener("click", () => openTopicDialog(null));
  own.append(b);
  menu.append(own);
}
// One dialog for a new topic of your own, and for the scenario of any topic.
let editingTopic = null;
function openTopicDialog(t) {
  editingTopic = t;
  $("custom-title").textContent = t ? `Scenario: ${t.name}` : "Your own topic";
  $("custom-sub").textContent = t
    ? "Tell the tutor how to talk with you in this topic - a role, a place, a situation."
    : "Anything you want to talk about - football, programming, a coffee shop. Its words are prepared once.";
  $("custom-topic").value = t ? t.name : "";
  $("custom-topic").disabled = !!t;
  $("custom-prompt").value = t ? (t.prompt || "") : "";
  $("custom-submit").textContent = t ? "Save" : "Start topic";
  try { bootstrap.Dropdown.getOrCreateInstance($("topic-btn")).hide(); } catch (_) { /* no menu */ }
  $("custom-overlay").classList.remove("hidden");
  (t ? $("custom-prompt") : $("custom-topic")).focus();
}
$("custom-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const prompt = $("custom-prompt").value.trim();
  if (editingTopic) {
    send({ type: "topic", id: editingTopic.id, prompt });
  } else {
    const name = $("custom-topic").value.trim();
    if (!name) return;
    send({ type: "topic", custom: name, prompt });
  }
  $("custom-topic").value = "";
  $("custom-prompt").value = "";
  $("custom-overlay").classList.add("hidden");
});
$("custom-cancel").addEventListener("click", () => $("custom-overlay").classList.add("hidden"));

// ── The board and the word list ─────────────────────────────────────────────

function renderCoaching(card) {
  board.render(card);
  renderWords(card);
  if (card.notice && card.notice_stamp !== renderCoaching.notice) {
    renderCoaching.notice = card.notice_stamp;
    flash(card.notice, false);
  }
}

function wordRow(it, onClick) {
  const li = document.createElement("li");
  li.tabIndex = 0;
  li.className = "word s" + it.stage + (it.now ? " now" : "");
  const top = document.createElement("div");
  top.className = "word-top";
  const t = document.createElement("span");
  t.className = "word-text";
  t.textContent = it.text;
  const k = document.createElement("span");
  k.className = "badge " + it.kind;
  k.textContent = it.kind === "phrasal" ? "phrasal" : it.kind === "collocation" ? "colloc." : it.kind === "expression" ? "expr." : "word";
  const n = document.createElement("span");
  n.className = "word-count";
  n.textContent = it.uses ? `${it.uses}× · ${it.days}d` : "0×";
  n.title = `used ${it.uses} times, on ${it.days} different days`;
  const d = document.createElement("span");
  d.className = "dots";
  for (let i = 1; i <= 4; i++) {
    const dot = document.createElement("span");
    dot.className = "d" + (i <= it.stage ? " on" : "");
    d.append(dot);
  }
  top.append(t, k, d, n);
  li.append(top);
  if (it.meaning || it.native) {
    const m = document.createElement("div");
    m.className = "word-meaning";
    m.textContent = [it.meaning, it.native && `· ${it.native}`].filter(Boolean).join(" ");
    li.append(m);
  }
  li.addEventListener("click", () => onClick(li));
  return li;
}

function renderWords(card) {
  const deck = card.deck || {};
  const items = deck.items || [];
  const lex = card.lexis || {};
  document.querySelector('.tab[data-tab="words"]').textContent = deck.intensive ? "Lesson words" : "Topic words";
  $("due-label").textContent = deck.intensive ? "From earlier lessons - review" : "Old words - use them again";
  if (items.length) {
    const learned = items.filter((i) => i.stage >= 3).length;
    $("words-head").textContent = deck.intensive
      ? `${deck.tier} · ${deck.title} · ${items.length} words and phrases`
      : `${deck.tier} words for this topic · ${learned}/${items.length} learned`
        + ` · ${(lex.learned || 0) + (lex.strong || 0)} learned in all topics`;
  }
  const sig = JSON.stringify([items.map((i) => [i.text, i.uses, i.days, i.now]), (card.due || []).map((i) => i.text)]);
  if (renderWords.sig === sig) return;
  renderWords.sig = sig;
  const list = $("words");
  list.textContent = "";
  items.forEach((it) => list.append(wordRow(it, (li) => {
    board.hold();
    send({ type: "explain", item: { kind: "word", text: it.text } });
    li.classList.add("asked");
    setTimeout(() => li.classList.remove("asked"), 1500);
  })));
  const due = card.due || [];
  $("due-label").classList.toggle("hidden", !due.length);
  const dl = $("due");
  dl.textContent = "";
  due.forEach((it) => dl.append(wordRow(it, () => send({ type: "explain", item: { kind: "word", text: it.text } }))));
}

// ── The course, unit by unit ────────────────────────────────────────────────

function renderUnits() {
  const host = $("units-list");
  host.textContent = "";
  syllabus.forEach((band) => {
    const box = document.createElement("section");
    box.className = "units-stage";
    const head = document.createElement("div");
    head.className = "units-stage-head";
    const name = document.createElement("strong");
    name.textContent = band.band;
    const info = document.createElement("span");
    info.textContent = `${band.counts.strong}/${band.total} known · ${band.counts.learning} learning · ${band.counts.weak} weak · ${band.counts.new} not used yet`;
    head.append(name, info);
    box.append(head);
    band.skills.forEach((k) => {
      const row = document.createElement("button");
      row.type = "button";
      row.className = "grammar-row " + k.status;
      const title = document.createElement("span");
      title.className = "unit-title";
      title.textContent = k.name;
      const hint = document.createElement("span");
      hint.className = "grammar-hint";
      hint.textContent = k.hint;
      const bar = document.createElement("span");
      bar.className = "meter";
      const fill = document.createElement("span");
      const m = k.mastery ?? 0;
      fill.className = "meter-fill " + (k.mastery === null ? "none" : m >= 70 ? "strong" : m >= 40 ? "mid" : "weak");
      fill.style.width = `${m}%`;
      bar.append(fill);
      const st = document.createElement("span");
      st.className = "status " + k.status;
      st.textContent = k.status === "new" ? "not used yet" : k.status === "strong" ? "known" : k.status;
      row.append(title, hint, bar, st);
      row.addEventListener("click", () => {
        $("units-overlay").classList.add("hidden");
        location.hash = "#/lesson";
        send({ type: "explain", item: { kind: "fix", skill_id: k.id, skill: k.name, wrong: "", right: "" } });
      });
      box.append(row);
    });
    host.append(box);
  });
}
$("chip-unit").addEventListener("click", () => {
  renderUnits();
  $("units-overlay").classList.remove("hidden");
});

// ── Settings ────────────────────────────────────────────────────────────────

function field(label, input) {
  const wrap = document.createElement("label");
  wrap.className = "field";
  const l = document.createElement("span");
  l.textContent = label;
  wrap.append(l, input);
  return wrap;
}

function choice(options, value) {
  const sel = document.createElement("select");
  sel.className = "select form-select";
  options.forEach((o) => sel.append(new Option(o, o)));
  sel.value = value;
  return sel;
}

async function openSettings() {
  const data = await fetch("/api/settings").then((r) => r.json()).catch(() => null);
  if (!data) return flash("Settings could not be loaded.", false);
  const host = $("settings-fields");
  host.textContent = "";
  const you = document.createElement("input");
  you.className = "input";
  you.value = data.user_name || "";
  you.dataset.key = "user_name";
  host.append(field("My name", you));
  const voice = choice(data.voices, data.voice);
  voice.dataset.key = "voice";
  host.append(field("Tutor's voice", voice));
  data.plugins.forEach((pl) => {
    // The "second opinion" setting belonged to the old flow; the board is it now.
    pl.fields.filter((f) => f.key !== "speak_every").forEach((f) => {
      const value = pl.values[f.key] ?? f.default;
      let input;
      if (f.type === "toggle") {
        input = document.createElement("input");
        input.type = "checkbox";
        input.checked = value === true || value === "true";
      } else {
        input = choice(f.options || [], String(value));
      }
      input.dataset.ns = pl.namespace;
      input.dataset.key = f.key;
      host.append(field(f.label, input));
    });
  });
  $("settings-overlay").classList.remove("hidden");
  loadMemory();
  loadKeys();
}

// ── Gemini keys: the main one and extras, never shown whole ────────────────

async function loadKeys() {
  const res = await fetch("/api/keys").then((r) => r.json()).catch(() => ({ keys: [] }));
  const list = $("keys-list");
  list.textContent = "";
  $("keys-count").textContent = `${res.keys.length} key${res.keys.length === 1 ? "" : "s"}`;
  res.keys.forEach((k) => {
    const li = document.createElement("li");
    const text = document.createElement("div");
    const tag = document.createElement("div");
    tag.className = "mem-key" + (k.main ? " key-main" : "");
    tag.textContent = k.main ? "main key" : "extra key";
    const value = document.createElement("div");
    value.className = "mem-value";
    value.textContent = k.masked;
    text.append(tag, value);
    const actions = document.createElement("div");
    actions.className = "key-actions";
    if (!k.main) {
      const main = document.createElement("button");
      main.type = "button";
      main.className = "link";
      main.textContent = "make main";
      main.addEventListener("click", () => keyAction({ action: "main", id: k.id }));
      const del = document.createElement("button");
      del.type = "button";
      del.className = "forget";
      del.title = "Remove this key";
      del.setAttribute("aria-label", `Remove key ${k.masked}`);
      del.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7h14M10 7V5h4v2M7 7l1 12h8l1-12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
      del.addEventListener("click", () => keyAction({ action: "remove", id: k.id }));
      actions.append(main, del);
    }
    li.append(text, actions);
    list.append(li);
  });
}

async function keyAction(body) {
  $("keys-note").textContent = body.action === "add" ? "Checking the key…" : "";
  const res = await fetch("/api/keys", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  }).then((r) => r.json()).catch(() => ({ ok: false, error: "The server did not answer." }));
  $("keys-note").textContent = res.ok ? "" : (res.error || "It did not work.");
  if (res.ok) {
    $("key-new").value = "";
    loadKeys();
    flash(body.action === "remove" ? "Key removed." : "Key saved.");
  }
}

$("key-add-extra").addEventListener("click", () => {
  const key = $("key-new").value.trim();
  if (key) keyAction({ action: "add", key, main: false });
});
// Enter in the key box adds it as an extra - it must not save the whole form.
$("key-new").addEventListener("keydown", (e) => {
  if (e.key !== "Enter") return;
  e.preventDefault();
  $("key-add-extra").click();
});
$("key-add-main").addEventListener("click", () => {
  const key = $("key-new").value.trim();
  if (key) keyAction({ action: "add", key, main: true });
});

// What LangVis remembers about you - each fact can be forgotten.
let memoryRows = [];

async function loadMemory() {
  memoryRows = await fetch("/api/memory").then((r) => r.json()).catch(() => []);
  renderMemory();
}

function renderMemory() {
  const q = $("memory-search").value.trim().toLowerCase();
  const list = $("memory-list");
  list.textContent = "";
  const rows = memoryRows.filter((r) => !q || `${r.key} ${r.value} ${r.category}`.toLowerCase().includes(q));
  $("memory-count").textContent = `${memoryRows.length} facts`;
  if (!rows.length) {
    const li = document.createElement("li");
    li.textContent = memoryRows.length ? "Nothing matches." : "Nothing remembered yet.";
    list.append(li);
    return;
  }
  rows.forEach((r) => {
    const li = document.createElement("li");
    const text = document.createElement("div");
    const key = document.createElement("div");
    key.className = "mem-key";
    key.textContent = `${r.category} · ${r.key.replace(/_/g, " ")}`;
    const value = document.createElement("div");
    value.className = "mem-value";
    value.textContent = r.value;
    text.append(key, value);
    const del = document.createElement("button");
    del.type = "button";
    del.className = "forget";
    del.title = "Forget this";
    del.setAttribute("aria-label", `Forget ${r.key}`);
    del.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7h14M10 7V5h4v2M7 7l1 12h8l1-12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    del.addEventListener("click", async () => {
      const res = await fetch("/api/memory/forget", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category: r.category, key: r.key }),
      }).then((x) => x.json()).catch(() => ({ ok: false }));
      if (res.ok) {
        memoryRows = memoryRows.filter((m) => m !== r);
        renderMemory();
      }
    });
    li.append(text, del);
    list.append(li);
  });
}
$("memory-search").addEventListener("input", renderMemory);

$("settings-btn").addEventListener("click", openSettings);
$("settings-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = { plugins: {} };
  $("settings-fields").querySelectorAll("[data-key]").forEach((el) => {
    const value = el.type === "checkbox" ? el.checked : el.value;
    if (el.dataset.ns) (body.plugins[el.dataset.ns] ||= {})[el.dataset.key] = value;
    else body[el.dataset.key] = value;
  });
  const res = await fetch("/api/settings", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  }).then((r) => r.json()).catch(() => ({ ok: false }));
  $("settings-overlay").classList.add("hidden");
  flash(res.ok ? "Settings saved - reconnecting the tutor." : "Settings could not be saved.", !!res.ok);
});

document.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", () =>
  $(b.dataset.close).classList.add("hidden")));
document.querySelectorAll(".overlay").forEach((o) => o.addEventListener("click", (e) => {
  if (e.target === o && o.id !== "key-overlay") o.classList.add("hidden");
}));
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") ["units-overlay", "settings-overlay", "content-overlay", "custom-overlay"]
    .forEach((id) => $(id).classList.add("hidden"));
});

// ── Transcript: the whole conversation of this topic ───────────────────────

async function loadHistory() {
  const topic = (status.topic || {}).id || "";
  const res = await fetch(`/api/history?topic=${encodeURIComponent(topic)}`)
    .then((r) => r.json()).catch(() => null);
  if (!res) return;
  const list = $("transcript");
  list.textContent = "";
  let day = "";
  res.lines.forEach((l) => {
    const d = (l.ts || "").slice(0, 10);
    if (d && d !== day) {
      day = d;
      const sep = document.createElement("li");
      sep.className = "day";
      sep.textContent = new Date(d + "T12:00:00").toLocaleDateString(undefined,
        { weekday: "short", day: "numeric", month: "short" });
      list.append(sep);
    }
    addLog(`${l.who}: ${l.text}`);
  });
  if (!res.lines.length) {
    const li = document.createElement("li");
    li.className = "sys";
    li.textContent = `No conversation in ${(status.topic || {}).name || "this topic"} yet.`;
    list.append(li);
  }
}

// ── Transcript ──────────────────────────────────────────────────────────────

function addLog(text) {
  const li = document.createElement("li");
  const m = /^([^:]{1,24}):\s?(.*)$/s.exec(text);
  const who = m ? m[1] : "";
  const body = m ? m[2] : text;
  if (who === "SYS" || who === "NET") { li.className = "sys"; li.textContent = body; }
  else if (who === "ERR") { li.className = "err"; li.textContent = body; }
  else if (who) {
    li.className = who === "You" ? "you" : "tutor-line";
    const w = document.createElement("span");
    w.className = "who";
    w.textContent = who;
    li.append(w, " ", body);
  } else { li.textContent = text; }
  const list = $("transcript");
  list.append(li);
  while (list.children.length > 700) list.firstChild.remove();
  list.parentElement.scrollTop = list.parentElement.scrollHeight;
}

// ── Pages ───────────────────────────────────────────────────────────────────

function route() {
  // Home is the start page. A course lesson and the Tutor share the board.
  let page = (location.hash.replace(/^#\/?/, "") || "home").split("?")[0];
  if (page === "intensive") page = "courses";
  const pages = ["home", "lesson", "tutor", "courses", "dictionary", "grammar", "account"];
  const known = pages.includes(page) ? page : "home";
  // The Tutor is a page of its own: going in or out of it loads the page afresh.
  if (lastPage && (lastPage === "tutor") !== (known === "tutor")) {
    if (started) send({ type: "stop" });
    location.reload();
    return;
  }
  lastPage = known;
  const view = known === "tutor" ? "lesson" : known;
  const tab = { lesson: "courses", dictionary: "account", grammar: "account" }[known] || known;
  document.body.dataset.page = known;
  document.querySelectorAll(".page").forEach((p) => p.classList.toggle("hidden", p.id !== `page-${view}`));
  document.querySelectorAll(".nav a").forEach((a) => a.classList.toggle("active", a.dataset.page === tab));
  // Nothing starts by itself: the teacher begins when Start is pressed, and
  // stops when its page is left (a course lesson and the Tutor are two places).
  if (started && known !== startedOn) { send({ type: "stop" }); stopped(); }
  $("start-what").textContent = known === "tutor"
    ? "Free conversation: talk about anything, ask about any grammar or word. Press Start and your tutor begins."
    : "Your course lesson, step by step. Press Start and the teacher begins.";
  if (known === "courses") loadIntensive(act);
  if (known === "home") loadHome(openCourse);
  if (known === "dictionary") loadDictionary();
  if (known === "grammar") loadGrammar();
  if (known === "account") loadAccount();
  if (view === "lesson") requestAnimationFrame(() => walker.reflow());
}
window.addEventListener("hashchange", route);

// "Start learning a new language": which language, then its courses.
function openCourse(name, key) {
  $("lang-overlay").classList.add("hidden");
  const active = ((status.modes || []).find((m) => m.active) || {}).key;
  if (key === active) { goTo("courses"); return; }
  location.hash = "#/courses";       // the reload after the switch lands on Courses
  switchLanguage(name);
}
function askLanguage() {
  renderLanguageChoice(openCourse);
  $("lang-overlay").classList.remove("hidden");
}
["home-start", "home-start-2"].forEach((id) => $(id).addEventListener("click", askLanguage));
$("lang-cancel").addEventListener("click", () => $("lang-overlay").classList.add("hidden"));
$("lang-overlay").addEventListener("click", (e) => {
  if (e.target === $("lang-overlay")) $("lang-overlay").classList.add("hidden");
});

function goTo(page) {
  if (location.hash === `#/${page}`) route();
  else location.hash = `#/${page}`;
}

// What the Courses page asks for.
// Its "Start / Continue the lesson" and the lesson tiles are an explicit
// start, so they open the Classroom and begin at once.
function act(kind, value) {
  if (kind === "choose") {
    sendSoon({ type: "track", value });   // a course card: only choose it
  } else if (kind === "track") {
    startWith = { track: value };          // the course goes with Start, applied first
    goTo("lesson");
    begin();
  } else if (kind === "lesson") {
    startWith = { lesson: value };
    goTo("lesson");
    begin();
  } else if (kind === "open") {
    startWith = { track: "intensive" };
    goTo("lesson");
    begin();
  }
}

$("start-btn").addEventListener("click", () => begin());

// ── Controls ────────────────────────────────────────────────────────────────

document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t === tab));
  $("pane-words").classList.toggle("hidden", tab.dataset.tab !== "words");
  $("pane-transcript").classList.toggle("hidden", tab.dataset.tab !== "transcript");
}));

$("compose").addEventListener("submit", (e) => {
  e.preventDefault();
  const text = $("text").value.trim();
  if (!text) return;
  send({ type: "text", text });
  $("text").value = "";
});

$("skip").addEventListener("click", () => send({ type: "skip" }));
$("restart").addEventListener("click", () => {
  if (!started) return;
  audio.flush();
  send({ type: "restart" });
  flash("Starting the lesson again…");
});
$("interrupt").addEventListener("click", () => { audio.flush(); send({ type: "interrupt" }); });
// ── The voice bar: the microphone switch, your voice as a wave ─────────────

const wave = $("wave");
const BANDS = 24;                         // per side: the bars are mirrored
const bars = new Array(BANDS).fill(0);
let waveLevel = 0;
let waveTick = 0;
const WAVE_RGB = {
  open: [18, 105, 90], speaking: [199, 90, 43], thinking: [201, 138, 10], off: [178, 58, 58], wait: [148, 139, 120],
};

function micOpen() {
  return started && !muted && (state === "LISTENING" || state === "SPEAKING");
}

// Rounded bars that are the real voice: each one a band of its pitch, low in
// the middle, high at the edges, mirrored left and right. Quiet: a row of
// dots with a slow shimmer running through them.
function drawWave() {
  const dpr = window.devicePixelRatio || 1;
  const w = wave.clientWidth, h = wave.clientHeight;
  if (w && wave.width !== Math.round(w * dpr)) { wave.width = Math.round(w * dpr); wave.height = Math.round(h * dpr); }
  const ctx = wave.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  waveTick += 1;

  const speaking = state === "SPEAKING" || (started && audio.busy(0));
  const hearing = started && !muted && !speaking && state === "LISTENING";
  document.body.dataset.mic = micOpen() ? "open" : "wait";
  const source = muted || !started ? null : speaking ? "out" : hearing ? "in" : null;
  const bands = source ? audio.spectrum(source, BANDS) : new Array(BANDS).fill(0);
  waveLevel += ((source === "in" ? audio.inputLevel() : source === "out" ? audio.outputLevel() : 0) - waveLevel) * 0.2;
  const rgb = muted ? WAVE_RGB.off : speaking ? WAVE_RGB.speaking
    : state === "THINKING" ? WAVE_RGB.thinking : hearing ? WAVE_RGB.open : WAVE_RGB.wait;

  const total = BANDS * 2;
  const slot = w / total, bw = Math.max(2.5, Math.min(7, slot * 0.55)), mid = h / 2;
  for (let i = 0; i < BANDS; i++) {
    // Loud enough to show only when there is a voice at all.
    const v = waveLevel > 0.02 ? Math.pow(bands[i], 1.6) : 0;
    const shimmer = muted || !started ? 0 : 0.5 + 0.5 * Math.sin(waveTick * 0.06 - i * 0.45);
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

  $("voice-hint").textContent = !started ? "Press Start to begin"
    : muted ? "Microphone off - click the mic"
    : speaking ? "LangVis is speaking - talk to cut in"
    : state === "THINKING" ? "Thinking…"
    : state !== "LISTENING" ? "Connecting…"
    : waveLevel > 0.04 ? "Listening…" : "Your turn - just talk";
  requestAnimationFrame(drawWave);
}
requestAnimationFrame(drawWave);

$("keyboard-btn").addEventListener("click", () => {
  const typing = $("compose").classList.toggle("hidden") === false;
  $("voicebar").classList.toggle("hidden", typing);
  $("keyboard-btn").classList.toggle("active", typing);
  if (typing) $("text").focus();
});
$("mic").addEventListener("click", () => send({ type: "mute", value: !muted }));
document.addEventListener("keydown", (e) => {
  if (e.key === "F4") { e.preventDefault(); send({ type: "mute", value: !muted }); }
});
$("content-close").addEventListener("click", () => $("content-overlay").classList.add("hidden"));

// ── The start: no button. Opening the lesson starts it, and the tutor speaks
// first. Browsers may lock the speaker until the page is clicked once - then
// the first click anywhere starts it.

let beginning = false;
async function begin() {
  if (started || beginning) return;
  beginning = true;
  const micOk = await audio.start();
  if (!micOk) flash("The microphone is not available - you can still type.", false);
  if (audio.canPlay()) { go(); return; }
  $("speech-text").textContent = "Click anywhere on the page - then I start talking.";
  const unlock = async () => {
    window.removeEventListener("pointerdown", unlock, true);
    window.removeEventListener("keydown", unlock, true);
    await audio.unlock();
    go();
  };
  window.addEventListener("pointerdown", unlock, true);
  window.addEventListener("keydown", unlock, true);
}

function go() {
  if (started) return;
  started = true;
  beginning = false;
  startedOn = document.body.dataset.page;
  // The page decides the kind of lesson: the Tutor is free talk, a lesson is the course.
  if (!startWith.track && startWith.lesson === undefined) {
    startWith = { track: startedOn === "tutor" ? "normal" : "intensive" };
  }
  $("start-gate").classList.add("hidden");
  $("speech-text").textContent = "Connecting - I will start talking in a moment.";
  // Start begins the lesson from nothing (with the course chosen, if any).
  freshStart = true;
  if (ws && ws.readyState === WebSocket.OPEN) {
    send(Object.assign({ type: "start", fresh: true }, startWith));
    freshStart = false;
    startWith = {};
  }
}

// The lesson has stopped (the Classroom was left, a topic, language or course
// changed, or the connection was lost): the teacher is silent until Start.
function stopped() {
  started = false;
  beginning = false;
  audio.flush();
  $("start-gate").classList.remove("hidden");
  setState("SLEEPING");
}

$("key-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const key = $("key").value.trim();
  const res = await fetch("/api/key", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ key }),
  }).then((r) => r.json()).catch(() => ({ ok: false, error: "The server did not answer." }));
  if (!res.ok) { $("key-note").textContent = res.error || "Could not save the key."; return; }
  $("key").value = "";
  $("key-note").textContent = "";
  $("key-overlay").classList.add("hidden");
  if (started) send({ type: "start" });
});

setState("SLEEPING");
route();
connect();
