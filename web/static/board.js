// The board: the learner's sentence, what was wrong, the richer version one
// level up, which grammar went up or down, and the lessons the teacher writes
// on it - with the tutor walking to each thing as it explains it.
import { draw } from "/static/diagrams.js";

const $ = (id) => document.getElementById(id);
const MODE_TEXT = {
  correct: "Correcting", better: "Better version · one level up", again: "Try again",
  explain: "Grammar explain", talk: "Conversation", fluency: "Fluency · talk freely",
};
const CIRCLED = ["①", "②", "③", "④", "⑤"];
const KIND = { phrasal: "phrasal verb", collocation: "collocation", word: "better word", expression: "expression" };

function norm(s) {
  return String(s || "").toLowerCase().replace(/[^\p{L}\p{N}']+/gu, "");
}

// Lower-case words only, so "Look at the board." matches "look at the board".
function words(text) {
  return String(text || "").toLowerCase().replace(/[^\p{L}\p{N}' ]+/gu, " ").replace(/\s+/g, " ").trim();
}

function node(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined) n.textContent = text;
  return n;
}

// A bubble line: bold head, then the rest.
function bubble(head, ...rest) {
  const frag = document.createDocumentFragment();
  if (head) frag.append(node("strong", "", head));
  rest.filter(Boolean).forEach((r) => {
    frag.append(document.createElement("br"));
    frag.append(typeof r === "string" ? document.createTextNode(r) : r);
  });
  return frag;
}

export class Board {
  constructor({ walker, audio, send }) {
    this.walker = walker;
    this.audio = audio;
    this.send = send;
    this.steps = [];
    this.idx = -1;
    this.stepAt = 0;
    this.lastLoud = 0;
    this.heard = false;
    this.holdUntil = 0;
    this.stamp = null;
    this.state = "SLEEPING";
    this.listening = false;
    setInterval(() => this.tick(), 100);
    $("undo").addEventListener("click", () => this.send({ type: "undo" }));
  }

  setState(state) {
    this.state = state;
    $("mode-pill").dataset.state = state;
    this.updateWaiting();
  }

  // ── While they speak ──────────────────────────────────────────────────────

  showLive(text, final) {
    if (!text) return;
    const said = $("said");
    said.classList.toggle("live", !final);
    said.textContent = "";
    text.split(/\s+/).filter(Boolean).forEach((w, i) => {
      if (i) said.append(" ");
      said.append(node("span", "tok", w));
    });
    if (!final) {
      // A new sentence: the old card no longer belongs to it.
      ["fixed-block", "better-block", "skills-block", "lesson-block"].forEach((id) => $(id).classList.add("hidden"));
      $("undo").hidden = true;
      this.steps = [];
      this.listening = true;
      const last = said.lastElementChild;
      this.walker.point(last, "", $("said-block"));
    }
  }

  // The server heard the learner start (true) or stop (false) a sentence. The
  // words arrive after the thinking, so meanwhile the board says what it is doing.
  hearing(on) {
    const said = $("said");
    if (on === null) {
      // It was only noise: put the board back as it was.
      this.listening = false;
      if (this.lastSaid) { said.classList.remove("live"); said.textContent = ""; said.append(...this.lastSaid); }
      this.walker.home();
      return;
    }
    this.listening = true;
    this.steps = [];
    said.classList.add("live");
    said.textContent = "";
    said.append(node("span", "hint pulse", on ? "Listening…" : "Thinking - checking your sentence…"));
    // The rest of the board stays: if this is a repeat, it is still what they
    // are repeating; if it is a new sentence, its own card replaces it.
    this.walker.point(said.firstElementChild, on ? "" : bubble("Thinking…"), $("said-block"));
  }

  // A repeat was checked: tick or cross next to what they had to say.
  repeat(m) {
    const block = m.phase === "repeat_fix" ? $("fixed-block") : $("better-block");
    const target = block.classList.contains("hidden") ? $("said-block") : block;
    target.querySelectorAll(".repeat-line").forEach((n) => n.remove());
    const line = node("p", "repeat-line " + (m.ok ? "ok" : "no"));
    const missing = (m.missing || [])[0];
    line.append(node("span", "tick", m.ok ? "✓" : "✗"), ` ${m.ok ? "You said it:" : "Almost - you said:"} `,
                node("em", "", m.text));
    if (!m.ok && missing) line.append(" - missing ", node("strong", "", `“${missing}”`));
    target.append(line);
    // Put the previous card back: a repeat does not replace it.
    this.listening = false;
    const said = $("said");
    if (this.lastSaid) { said.classList.remove("live"); said.textContent = ""; said.append(...this.lastSaid); }
    this.walker.point(line, m.ok ? bubble("Good!") : bubble("Again:", m.expected), target);
    this.hold(4000);
  }

  // ── A new analysis ────────────────────────────────────────────────────────

  render(card) {
    if (!card.stamp || card.stamp === this.stamp) return;
    this.stamp = card.stamp;
    this.listening = false;
    if (card.reset) return this.reset();
    if (card.undone) return this.renderUndone(card);

    const fixes = card.fixes || [];
    const said = $("said");
    said.classList.remove("live");
    said.textContent = "";
    const toks = card.said_tokens && card.said_tokens.length ? card.said_tokens : [{ text: card.said || "" }];
    // Which bad words belong to which correction.
    const owner = toks.map(() => -1);
    fixes.forEach((f, i) => {
      const wrong = new Set(String(f.wrong || "").split(/\s+/).map(norm).filter(Boolean));
      toks.forEach((t, j) => { if (owner[j] < 0 && t.bad && wrong.has(norm(t.text))) owner[j] = i; });
    });
    const firstBad = toks.findIndex((t) => t.bad);
    const marked = new Set();
    toks.forEach((t, j) => {
      if (j) said.append(" ");
      const span = node("span", "tok" + (t.bad ? " bad" : ""), t.text);
      let fi = owner[j];
      if (t.bad && fi < 0 && fixes.length) fi = 0;
      if (t.bad && fi >= 0) {
        span.dataset.fix = fi;
        span.tabIndex = 0;
        span.title = "Click: the tutor explains this";
        if (!marked.has(fi)) { marked.add(fi); span.append(node("sup", "n", CIRCLED[fi] || "•")); }
        span.addEventListener("click", () => this.explainFix(fixes[fi], span));
      }
      said.append(span);
    });
    $("undo").hidden = false;
    this.lastSaid = [...said.childNodes].map((n) => n.cloneNode(true));
    // Re-attach the click handlers the clones lost.
    this.lastSaid.forEach((n) => {
      if (n.dataset && n.dataset.fix !== undefined) {
        n.addEventListener("click", () => this.explainFix(fixes[+n.dataset.fix], n));
      }
    });
    document.querySelectorAll(".repeat-line").forEach((n) => n.remove());

    const hasFix = !card.clean && !!card.corrected;
    $("fixed-block").classList.toggle("hidden", !hasFix);
    if (hasFix) {
      const fixed = $("fixed");
      fixed.textContent = "";
      (card.fixed_tokens || []).forEach((t, j) => {
        if (j) fixed.append(" ");
        fixed.append(node("span", "tok" + (t.fixed ? " good" : ""), t.text));
      });
      const list = $("fixes");
      list.textContent = "";
      fixes.forEach((f, i) => {
        const li = node("li", "fix");
        li.tabIndex = 0;
        li.append(node("span", "n", CIRCLED[i] || "•"), node("span", "skill", f.skill),
                  node("span", "change", ` ${f.wrong} → ${f.right}`), node("span", "why", f.why ? ` - ${f.why}` : ""));
        li.addEventListener("click", () => this.explainFix(f, li));
        list.append(li);
      });
    }

    const enrich = card.enrich || [];
    $("better-block").classList.toggle("hidden", !card.improved);
    const better = $("better");
    better.textContent = "";
    const newSpans = [];
    if (card.improved) {
      // Highlight each new item inside the richer sentence.
      const text = card.improved;
      const low = text.toLowerCase();
      const hits = [];
      enrich.forEach((e, i) => {
        const at = low.indexOf(String(e.to || "").toLowerCase());
        if (at >= 0) hits.push({ at, end: at + e.to.length, i });
      });
      hits.sort((a, b) => a.at - b.at);
      let pos = 0;
      hits.forEach((h) => {
        if (h.at < pos) return;
        better.append(text.slice(pos, h.at));
        const span = node("span", "new", text.slice(h.at, h.end));
        span.tabIndex = 0;
        span.dataset.enrich = h.i;
        span.addEventListener("click", () => this.explainEnrich(enrich[h.i], span));
        better.append(span);
        newSpans[h.i] = span;
        pos = h.end;
      });
      better.append(text.slice(pos));
    }
    const list = $("enrich");
    list.textContent = "";
    enrich.forEach((e, i) => {
      const li = node("li", "item");
      li.tabIndex = 0;
      const head = node("div", "item-head");
      head.append(node("span", "item-to", e.to), node("span", "badge " + e.type, KIND[e.type] || e.type),
                  node("span", "badge lvl", e.level || ""));
      li.append(head);
      if (e.from) li.append(node("div", "item-from", `instead of “${e.from}”`));
      li.append(node("div", "item-meaning", [e.meaning, e.native && `· ${e.native}`].filter(Boolean).join(" ")));
      if (e.why) li.append(node("div", "item-why", e.why));
      li.addEventListener("click", () => this.explainEnrich(e, newSpans[i] || li));
      list.append(li);
    });

    const moves = card.skill_changes || [];
    $("skills-block").classList.toggle("hidden", !moves.length);
    const box = $("skill-moves");
    box.textContent = "";
    moves.forEach((m) => {
      const up = m.after > m.before;
      const chip = node("span", "move " + (up ? "up" : "down"));
      chip.append(node("span", "arrow", up ? "▲" : "▼"), ` ${m.name} `,
                  node("span", "from", String(m.before)), " → ", node("strong", "", String(m.after)));
      box.append(chip);
    });

    // A new sentence of theirs: last sentence's lesson leaves the board
    // unless this one brings its own.
    if (card.clean) $("lesson-block").classList.add("hidden");

    this.parts = { card, fixes, enrich, newSpans, moves };
    if (this.pendingMode) this.startTour(this.pendingMode);
  }

  renderUndone(card) {
    const said = $("said");
    said.textContent = "";
    said.append(node("span", "hint", `Taken back: “${card.said || ""}” - say it again.`));
    ["fixed-block", "better-block", "skills-block", "lesson-block"].forEach((id) => $(id).classList.add("hidden"));
    $("undo").hidden = true;
    this.steps = [];
    this.walker.home();
  }

  // The tutor asked a question: what the learner could say back.
  answers(m) {
    $("answers-q").textContent = m.question ? `· ${m.question}` : "";
    const list = $("answers-list");
    list.textContent = "";
    (m.answers || []).forEach((a) => list.append(node("li", "", a)));
    const block = $("answers-block");
    block.classList.remove("hidden", "write");
    void block.offsetWidth;
    block.classList.add("write");
  }

  hideAnswers() {
    $("answers-block").classList.add("hidden");
  }

  // A fresh lesson: the board is wiped clean.
  reset() {
    this.hideAnswers();
    const said = $("said");
    said.classList.remove("live");
    said.textContent = "";
    said.append(node("span", "hint", "A fresh start. Speak - your sentence is written here."));
    ["fixed-block", "better-block", "skills-block", "lesson-block"].forEach((id) => $(id).classList.add("hidden"));
    document.querySelectorAll(".repeat-line").forEach((n) => n.remove());
    $("undo").hidden = true;
    this.steps = [];
    this.parts = null;
    this.lastSaid = null;
    this.setMode("", "");
    this.walker.home();
  }

  // ── The teacher writes a lesson on the board ──────────────────────────────

  lesson(card) {
    const block = $("lesson-block");
    block.classList.remove("hidden");
    block.classList.remove("write");
    void block.offsetWidth;                   // restart the "writing" animation
    block.classList.add("write");
    $("lesson-title").textContent = card.title || "";
    $("lesson-band").textContent = card.band || "";
    $("lesson-band").classList.toggle("hidden", !card.band);
    $("lesson-kind").textContent = card.kind ? (KIND[card.kind] || card.kind) : "grammar";
    $("lesson-rule").textContent = [card.rule, card.native && `· ${card.native}`].filter(Boolean).join(" ");

    const formula = $("lesson-formula");
    formula.textContent = "";
    (card.formula || []).forEach((f, i) => {
      const li = node("li", "chalk", f);
      li.style.setProperty("--i", i);
      formula.append(li);
    });
    const pieces = draw($("lesson-diagram"), card.diagram);

    const ex = $("lesson-examples");
    ex.textContent = "";
    (card.mine || []).filter((m) => m.wrong || m.right).forEach((m) => {
      const li = node("li", "mine");
      li.append(node("span", "strike", m.wrong), " → ", node("strong", "", m.right));
      ex.append(li);
    });
    (card.examples || []).forEach((e) => ex.append(node("li", "", e)));
    $("lesson-use").classList.toggle("hidden", !ex.childElementCount);

    this.lessonParts = {
      title: $("lesson-title"),
      formula: [...formula.children],
      pieces,
      examples: [...ex.children],
      card,
    };
    // A lesson that arrives while the tutor explains is walked straight away.
    if (this.mode === "explain") this.startTour("explain");
  }

  // ── What the teacher is doing ─────────────────────────────────────────────

  setMode(mode, expect) {
    this.mode = mode;
    this.expect = expect || "";
    const pill = $("mode-pill");
    pill.dataset.mode = mode || "idle";
    pill.querySelector(".mode-text").textContent = MODE_TEXT[mode] || "Conversation";
    this.updateWaiting();
    if (!mode) return;
    // The card this mode is about may still be on its way; give it a moment.
    clearTimeout(this.tourTimer);
    this.pendingMode = mode;
    this.tourTimer = setTimeout(() => {
      if (this.pendingMode) this.startTour(this.pendingMode);
    }, 900);
  }

  updateWaiting() {
    const box = $("waiting");
    const waiting = this.state === "LISTENING" && this.expect
      && ["correct", "better", "again"].includes(this.mode);
    box.classList.toggle("hidden", !waiting);
    if (waiting) $("waiting-text").textContent = this.expect;
  }

  // One walk per mode: correcting shows the mistake, the fix and the rule;
  // a better version shows its new parts; explaining walks the lesson.
  startTour(mode) {
    this.pendingMode = null;
    const p = this.parts || {};
    const L = this.lessonParts;
    const steps = [];
    const lessonSteps = () => {
      if (!L || $("lesson-block").classList.contains("hidden")) return;
      const lane = $("lesson-block");
      steps.push({ el: L.title, lane, say: bubble(L.card.title, L.card.rule),
                   keys: ["look at the board", words(L.card.title), words(L.card.rule).slice(0, 18)] });
      L.formula.forEach((f, i) => steps.push({ el: f, lane, say: bubble("The form:", f.textContent),
                                               keys: i ? [words(f.textContent).slice(0, 14)] : ["the form", words(f.textContent).slice(0, 14)] }));
      if (L.pieces.length) {
        steps.push({ el: $("lesson-diagram"), lane, say: bubble("Look:", "the picture shows what it means."),
                     keys: ["time line", "timeline", "on the left", "on the right", "leads to", "becomes", "picture"] });
      }
      if (L.examples.length) {
        steps.push({ el: L.examples[0], lane, say: bubble("Use it like this:", L.examples[0].textContent),
                     keys: ["for example", "so not", "we say", "use it like"] });
      }
    };
    if (mode === "correct") {
      (p.fixes || []).forEach((f, i) => {
        const at = document.querySelector(`#said [data-fix="${i}"]`) || document.querySelector("#said .bad");
        steps.push({ el: at, lane: $("said-block"),
                     say: bubble(`${CIRCLED[i] || "•"} ${f.skill}`, `${f.wrong} → ${f.right}`, f.why),
                     keys: ["did you mean"] });
      });
      lessonSteps();
      if (p.card && !p.card.clean && p.card.corrected) {
        steps.push({ el: document.querySelector("#fixed .good") || $("fixed"), lane: $("fixed-block"),
                     say: bubble("Say it:", p.card.corrected), keys: ["now say it", "say it:"] });
      }
    } else if (mode === "better") {
      (p.enrich || []).forEach((e, i) => {
        steps.push({ el: (p.newSpans || [])[i] || $("better"), lane: $("better-block"),
                     say: bubble(`${e.to} · ${KIND[e.type] || e.type} · ${e.level}`,
                                 [e.meaning, e.native && `(${e.native})`].filter(Boolean).join(" "), e.why),
                     keys: i ? [words(e.to)] : ["better", words(e.to)] });
      });
      if (p.card && p.card.improved) {
        steps.push({ el: $("better").firstElementChild || $("better"), lane: $("better-block"),
                     say: bubble("Now you say it:", p.card.improved), keys: ["now you say it", "now say it"] });
      }
    } else if (mode === "explain") {
      lessonSteps();
    } else if (mode === "again") {
      const block = $("better-block").classList.contains("hidden") ? $("fixed-block") : $("better-block");
      steps.push({ el: block.querySelector(".sentence"), lane: block, say: bubble("Again:", this.expect) });
    } else if (mode === "talk" && (p.moves || []).length) {
      steps.push({ el: $("skill-moves").firstElementChild, lane: $("skills-block"),
                   say: bubble("Your grammar", p.moves.map((m) => `${m.name}: ${m.before} → ${m.after}`).join(" · ")) });
    }
    // A stop on something hidden or already gone is no place to stand.
    this.steps = steps.filter((s) => s.el && s.el.isConnected && s.el.offsetParent !== null);
    this.steps.forEach((s) => { s.keys = (s.keys || []).map(words).filter((k) => k.length >= 3); });
    this.idx = -1;
    this.heard = false;
    this.spoke = false;           // the walk only moves on once the tutor talks
    this.byWords = false;         // …and once its words are heard, it follows its words
    if (this.steps.length) this.next();
    else if (mode === "talk" || mode === "fluency") this.walker.home();
  }

  // What the tutor is saying right now (the live transcript of this turn).
  // The walk goes to the furthest stop whose words it has already said - so
  // it stands at the formula while it says "the form", at the picture while
  // it describes the picture, and never runs ahead of the voice.
  onWords(text) {
    if (!this.steps.length || this.idx < 0 || this.idx >= this.steps.length) return;
    const said = words(text);
    let at = this.idx;
    let from = 0;
    for (let i = 0; i < this.steps.length; i++) {
      const hits = this.steps[i].keys.map((k) => said.indexOf(k, from)).filter((x) => x >= 0);
      if (!hits.length) continue;
      from = Math.min(...hits);
      if (i > at) at = i;
    }
    if (at > this.idx) {
      this.byWords = true;
      this.idx = at - 1;
      this.next();
    }
  }

  next() {
    this.idx += 1;
    this.stepAt = performance.now();
    this.heard = false;
    const step = this.steps[this.idx];
    if (!step) {
      this.restAt = performance.now();
      return;
    }
    this.walker.point(step.el, step.say, step.lane);
  }

  tick() {
    const now = performance.now();
    this.updateWaiting();
    if (now < this.holdUntil || this.listening) return;
    if (this.idx >= this.steps.length) {
      // The walk is over: back to its corner after a moment.
      if (this.steps.length && this.restAt && now - this.restAt > 3500) {
        this.restAt = 0;
        this.walker.home();
      }
      return;
    }
    if (this.idx < 0) return;
    const dwell = now - this.stepAt;
    if (this.state === "SPEAKING") {
      // Moves on at the tutor's own pauses, so the walk keeps pace with the
      // explanation it is giving.
      this.spoke = true;
      if (this.audio.outputLevel() > 0.05) { this.lastLoud = now; this.heard = true; }
      // Its words drive the walk; pauses are only a fallback when a stop's
      // words never come (the tutor put it its own way).
      const waitFor = this.byWords ? 6000 : 1500;
      if (this.heard && dwell > waitFor && now - this.lastLoud > 420) this.next();
    } else if (this.spoke && this.state === "LISTENING" && dwell > 1200) {
      // It has finished talking: go to the last stop - what they must say now.
      if (this.idx < this.steps.length - 1) {
        this.idx = this.steps.length - 2;
        this.next();
      } else {
        this.next();
      }
    }
  }

  // ── Clicks: the learner asks about something on the board ─────────────────

  hold(ms = 7000) { this.holdUntil = performance.now() + ms; }

  explainFix(f, at) {
    if (!f) return;
    this.hold(1500);
    this.walker.point(at, bubble(f.skill, `${f.wrong} → ${f.right}`, f.why), at.closest(".block"));
    this.send({ type: "explain", item: { kind: "fix", wrong: f.wrong, right: f.right, skill: f.skill,
                                         skill_id: f.skill_id } });
  }

  explainEnrich(e, at) {
    if (!e) return;
    this.hold(1500);
    this.walker.point(at, bubble(`${e.to} · ${e.level}`, [e.meaning, e.native && `(${e.native})`].filter(Boolean).join(" ")),
                      at.closest(".block"));
    this.send({ type: "explain", item: { kind: "enrich", to: e.to, from: e.from, type: e.type, level: e.level,
                                         meaning: e.meaning, native: e.native } });
  }
}
