// The Dictionary and Hesab (account) pages, and the small SVG charts they use.

const $ = (id) => document.getElementById(id);
const NS = "http://www.w3.org/2000/svg";
const STATUS_TEXT = { new: "New", learning: "Learning", learned: "Learned", strong: "Strong" };
const KIND = { phrasal: "phrasal verb", collocation: "collocation", word: "word", expression: "expression" };

function node(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined && text !== null) n.textContent = text;
  return n;
}

function svg(tag, attrs = {}, parent) {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  if (parent) parent.append(n);
  return n;
}

function fmtDate(iso) {
  if (!iso) return "-";
  const d = new Date(iso.length <= 10 ? iso + "T12:00:00" : iso);
  return d.toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

// ── Tooltip ─────────────────────────────────────────────────────────────────

const tip = () => $("tooltip");
function showTip(evt, lines) {
  const t = tip();
  t.textContent = "";
  lines.forEach((l, i) => t.append(i ? node("div", "", l) : node("strong", "", l)));
  t.classList.remove("hidden");
  const x = Math.min(window.innerWidth - t.offsetWidth - 12, evt.clientX + 14);
  const y = Math.max(8, evt.clientY - t.offsetHeight - 10);
  t.style.transform = `translate(${x}px, ${y}px)`;
}
function hideTip() { tip().classList.add("hidden"); }

// ── Charts ──────────────────────────────────────────────────────────────────
// One series each, so one colour each, a recessive grid, and a hover readout.

function empty(host, text) {
  host.textContent = "";
  host.append(node("p", "empty", text));
}

function lineChart(host, points, { min = 0, max, guides = [], fmt = (v) => v, area = false, unit = "" }) {
  if (points.length < 1) return empty(host, "Not enough practice days yet.");
  host.textContent = "";
  const W = 560, H = 220, L = 34, R = 12, T = 12, B = 26;
  const top = max ?? Math.max(1, ...points.map((p) => p.y)) * 1.15;
  const s = svg("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart-svg", role: "img" }, host);
  const x = (i) => L + (points.length === 1 ? (W - L - R) / 2 : i * (W - L - R) / (points.length - 1));
  const y = (v) => T + (H - T - B) * (1 - (v - min) / (top - min));

  const ticks = guides.length ? guides : [0, top / 2, top].map((v) => ({ v: Math.round(v) }));
  ticks.forEach((g) => {
    svg("line", { x1: L, x2: W - R, y1: y(g.v), y2: y(g.v), class: g.label ? "guide" : "grid" }, s);
    const t = svg("text", { x: L - 6, y: y(g.v) + 4, class: "axis", "text-anchor": "end" }, s);
    t.textContent = g.label || g.v;
  });
  svg("line", { x1: L, x2: W - R, y1: y(min), y2: y(min), class: "baseline" }, s);

  const d = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)} ${y(p.y).toFixed(1)}`).join(" ");
  if (area && points.length > 1) {
    svg("path", { d: `${d} L${x(points.length - 1)} ${y(min)} L${x(0)} ${y(min)} Z`, class: "area" }, s);
  }
  svg("path", { d, class: "line" }, s);
  const last = points[points.length - 1];
  svg("circle", { cx: x(points.length - 1), cy: y(last.y), r: 4.5, class: "dot" }, s);
  const lab = svg("text", { x: x(points.length - 1) - 8, y: y(last.y) - 10, class: "value", "text-anchor": "end" }, s);
  lab.textContent = fmt(last.y);

  [0, points.length - 1].filter((v, i, a) => a.indexOf(v) === i).forEach((i) => {
    const t = svg("text", { x: x(i), y: H - 6, class: "axis", "text-anchor": i ? "end" : "start" }, s);
    t.textContent = fmtDate(points[i].x);
  });

  // Crosshair: the nearest day under the pointer.
  const cross = svg("line", { y1: T, y2: H - B, class: "cross hidden" }, s);
  const hit = svg("rect", { x: L, y: T, width: W - L - R, height: H - T - B, fill: "transparent" }, s);
  hit.addEventListener("mousemove", (e) => {
    const box = s.getBoundingClientRect();
    const px = (e.clientX - box.left) * (W / box.width);
    let best = 0;
    points.forEach((p, i) => { if (Math.abs(x(i) - px) < Math.abs(x(best) - px)) best = i; });
    cross.setAttribute("x1", x(best));
    cross.setAttribute("x2", x(best));
    cross.classList.remove("hidden");
    showTip(e, [fmtDate(points[best].x), `${fmt(points[best].y)}${unit}`, ...(points[best].extra || [])]);
  });
  hit.addEventListener("mouseleave", () => { cross.classList.add("hidden"); hideTip(); });
}

function barChart(host, points, { unit = "" }) {
  if (!points.length) return empty(host, "No mistakes recorded yet.");
  host.textContent = "";
  const W = 560, H = 220, L = 34, R = 12, T = 12, B = 26;
  const top = Math.max(1, ...points.map((p) => p.y)) * 1.15;
  const s = svg("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart-svg", role: "img" }, host);
  const slot = (W - L - R) / points.length;
  const bw = Math.max(3, Math.min(28, slot - 2));
  const y = (v) => T + (H - T - B) * (1 - v / top);
  [Math.round(top / 2), Math.round(top)].forEach((v) => {
    svg("line", { x1: L, x2: W - R, y1: y(v), y2: y(v), class: "grid" }, s);
    svg("text", { x: L - 6, y: y(v) + 4, class: "axis", "text-anchor": "end" }, s).textContent = v;
  });
  points.forEach((p, i) => {
    const bx = L + i * slot + (slot - bw) / 2;
    const h = Math.max(p.y ? 2 : 0, H - B - y(p.y));
    // Rounded at the data end only, square on the baseline.
    const r = Math.min(4, bw / 2, h);
    const top_ = H - B - h;
    svg("path", { class: "bar", d: `M${bx} ${H - B} V${top_ + r} Q${bx} ${top_} ${bx + r} ${top_} H${bx + bw - r} Q${bx + bw} ${top_} ${bx + bw} ${top_ + r} V${H - B} Z` }, s);
    const hit = svg("rect", { x: L + i * slot, y: T, width: slot, height: H - T - B, fill: "transparent" }, s);
    hit.addEventListener("mousemove", (e) => showTip(e, [fmtDate(p.x), `${p.y}${unit}`, ...(p.extra || [])]));
    hit.addEventListener("mouseleave", hideTip);
  });
  svg("line", { x1: L, x2: W - R, y1: H - B, y2: H - B, class: "baseline" }, s);
  [0, points.length - 1].filter((v, i, a) => a.indexOf(v) === i).forEach((i) => {
    svg("text", { x: L + i * slot + slot / 2, y: H - 6, class: "axis", "text-anchor": i ? "end" : "start" }, s)
      .textContent = fmtDate(points[i].x);
  });
}

function hbars(host, rows) {
  host.textContent = "";
  if (!rows.length) return empty(host, "No mistakes recorded yet.");
  const top = Math.max(...rows.map((r) => r.value));
  rows.forEach((r) => {
    const row = node("div", "hbar");
    row.append(node("span", "hbar-label", r.label));
    const track = node("span", "hbar-track");
    const fill = node("span", "hbar-fill");
    fill.style.width = `${Math.max(2, 100 * r.value / top)}%`;
    track.append(fill);
    row.append(track, node("span", "hbar-value", String(r.value)));
    row.addEventListener("mousemove", (e) => showTip(e, [r.label, `${r.value} mistakes`]));
    row.addEventListener("mouseleave", hideTip);
    host.append(row);
  });
}

function stat(label, value, sub) {
  const box = node("div", "stat");
  box.append(node("div", "stat-label", label), node("div", "stat-value", value));
  if (sub) box.append(node("div", "stat-sub", sub));
  return box;
}

function meter(value) {
  const bar = node("span", "meter");
  const fill = node("span", "meter-fill " + (value === null ? "none" : value < 40 ? "weak" : value < 70 ? "mid" : "strong"));
  fill.style.width = `${value ?? 0}%`;
  bar.append(fill);
  return bar;
}

function dots(stage) {
  const box = node("span", "dots");
  box.title = `${stage} of 4`;
  for (let i = 1; i <= 4; i++) box.append(node("span", "d" + (i <= stage ? " on" : "")));
  return box;
}

// ── Dictionary ──────────────────────────────────────────────────────────────

let dictData = null;

export async function loadDictionary() {
  const res = await fetch("/api/dictionary").then((r) => r.json()).catch(() => null);
  if (!res || res.error) {
    $("dict-sub").textContent = "The dictionary could not be loaded.";
    return;
  }
  dictData = res;
  const c = res.counts;
  $("dict-sub").textContent = "Every word and phrase you met. Nothing is forgotten: each one comes back on its review day, in whatever topic you are in.";
  const stats = $("dict-stats");
  stats.textContent = "";
  stats.append(stat("Learned", String(c.learned + c.strong), `${c.strong} strong`),
               stat("On the way", String(c.learning), "used on 1-2 days"),
               stat("Used", String(c.used), `of ${c.total} items`),
               stat("Due today", String(c.due), "come back in the lesson"));
  const topicSel = $("dict-topic");
  const keep = topicSel.value;
  topicSel.length = 1;
  res.topics.forEach((t) => topicSel.append(new Option(t, t)));
  topicSel.value = keep;
  renderDictionary();
}

export function renderDictionary() {
  if (!dictData) return;
  const q = $("dict-search").value.trim().toLowerCase();
  const topic = $("dict-topic").value;
  const kind = $("dict-kind").value;
  const status = $("dict-status").value;
  const today = new Date().toISOString().slice(0, 10);
  const body = $("dict-table").tBodies[0];
  body.textContent = "";
  const rows = dictData.items.filter((r) =>
    (!q || r.text.includes(q) || (r.meaning || "").toLowerCase().includes(q) || (r.native || "").toLowerCase().includes(q))
    && (!topic || r.topic_name === topic) && (!kind || r.kind === kind)
    && (!status || (status === "used" ? r.uses > 0
        : status === "mine" ? r.source === "mine"
        : status === "suggested" ? r.source !== "mine" && r.uses === 0
        : status === "due" ? r.uses > 0 && r.next_review && r.next_review <= today
        : r.status === status)));
  if (!rows.length) {
    const tr = node("tr");
    const td = node("td", "empty", "Nothing matches.");
    td.colSpan = 11;
    tr.append(td);
    body.append(tr);
    return;
  }
  rows.slice(0, 800).forEach((r) => {
    const tr = node("tr", "dict-row");
    const item = node("td");
    item.append(node("strong", "", r.text));
    if (r.meaning || r.native) item.append(node("div", "muted", [r.meaning, r.native && `· ${r.native}`].filter(Boolean).join(" ")));
    const st = node("td");
    st.append(dots(r.stage), " ", node("span", "status " + r.status, STATUS_TEXT[r.status] || r.status));
    const from = { mine: "you", topic: "topic list", board: "tutor" }[r.source] || "earlier";
    tr.append(item, node("td", "", KIND[r.kind] || r.kind), node("td", "", r.level || "-"),
              node("td", "", from), node("td", "", r.topic_name || "-"),
              node("td", "num", r.wrong ? `${r.uses} (${r.wrong}✗)` : String(r.uses)),
              node("td", "num", String(r.days)), node("td", "num", String(r.heard || 0)),
              node("td", "", fmtDate(r.last)), st,
              node("td", "", r.uses ? fmtDate(r.next_review) : "-"));
    const detail = node("tr", "detail hidden");
    const td = node("td");
    td.colSpan = 11;
    if (r.sentences.length) {
      td.append(node("div", "label", "Your sentences"));
      const ul = node("ul", "quotes");
      r.sentences.forEach((s) => ul.append(node("li", "", s)));
      td.append(ul);
    }
    if (r.wrong_sentences.length) {
      td.append(node("div", "label", "Used wrongly"));
      const ul = node("ul", "quotes bad");
      r.wrong_sentences.forEach((s) => ul.append(node("li", "", s)));
      td.append(ul);
    }
    if (r.example) td.append(node("div", "label", "Example"), node("p", "quote", r.example));
    if (!td.childElementCount) td.append(node("p", "muted", "Not used yet - the tutor will ask for it."));
    detail.append(td);
    tr.addEventListener("click", () => detail.classList.toggle("hidden"));
    body.append(tr, detail);
  });
}

["dict-search", "dict-topic", "dict-kind", "dict-status"].forEach((id) =>
  document.getElementById(id).addEventListener("input", renderDictionary));

// ── Account ─────────────────────────────────────────────────────────────────

let accData = null;

export async function loadAccount() {
  const res = await fetch("/api/account").then((r) => r.json()).catch(() => null);
  if (!res || res.error) {
    $("acc-sub").textContent = "The account could not be loaded.";
    return;
  }
  accData = res;
  const t = res.totals;
  $("acc-sub").textContent = `Level ${res.level} · ${Math.round(res.score)}/100 · goal ${res.goal}`
    + (res.measured ? "" : " · still mostly your own estimate");

  const stats = $("acc-stats");
  stats.textContent = "";
  const strong = res.skills.filter((s) => s.status === "strong").length;
  const weak = res.skills.filter((s) => s.status === "weak").length;
  stats.append(stat("Level", res.level, `${Math.round(res.score)} / 100`),
               stat("Sentences", String(t.sentences), `${t.words} words · ${t.days} days`),
               stat("Words learned", String(res.lexis.learned + res.lexis.strong), `${res.lexis.learning} on the way`),
               stat("Mistakes", String(t.mistakes), "all recorded"),
               stat("Grammar", `${strong} strong`, `${weak} weak · ${res.skills.length} in total`));

  const guides = [{ v: res.bands.A2, label: "A2" }, { v: res.bands.B1, label: "B1" }, { v: res.bands.B2, label: "B2" }];
  lineChart($("chart-level"), res.history.map((h) => ({ x: h.date, y: h.score,
    extra: [`${h.sentences} sentences`, `${h.mistakes} mistakes`] })),
    { min: 0, max: 75, guides, fmt: (v) => Math.round(v), unit: " / 100" });
  lineChart($("chart-growth"), res.growth.map((g) => ({ x: g.date, y: g.learned })),
    { min: 0, area: true, unit: " learned" });
  barChart($("chart-mistakes"), res.history.map((h) => ({ x: h.date, y: h.mistakes,
    extra: [`${h.sentences} sentences`] })), { unit: " mistakes" });

  const bySkill = res.skills.map((s) => ({ label: s.name, value: s.logged_errors || s.errors }))
    .filter((r) => r.value > 0).sort((a, b) => b.value - a.value).slice(0, 10);
  hbars($("chart-skills"), bySkill);

  renderGrammar(res);

  const sel = $("mis-skill");
  const keep = sel.value;
  sel.length = 1;
  [...new Set(res.mistakes.map((m) => m.skill))].forEach((sid) => {
    const s = res.skills.find((k) => k.id === sid);
    sel.append(new Option(s ? s.name : sid, sid));
  });
  sel.value = keep;
  renderMistakes();
}

function renderGrammar(res) {
  const host = $("acc-grammar");
  host.textContent = "";
  ["A1", "A2", "B1", "B2"].forEach((b) => {
    const group = node("div", "band-group");
    const skills = res.skills.filter((s) => s.band === b);
    const strong = skills.filter((s) => s.status === "strong").length;
    group.append(node("h3", "", `${b}  ·  ${strong}/${skills.length} known`));
    skills.forEach((s) => {
      const row = node("div", "skill-row");
      const head = node("div", "skill-head");
      head.append(node("span", "skill-name", s.name), meter(s.mastery),
                  node("span", "skill-num", s.mastery === null ? "-" : String(s.mastery)),
                  node("span", "status " + s.status, s.status === "new" ? "not used yet" : s.status),
                  node("span", "skill-counts", `${s.correct}✓ ${s.errors}✗`));
      const body = node("div", "skill-body hidden");
      body.append(node("p", "muted", s.hint));
      if (s.rule) body.append(node("p", "", s.rule));
      if (s.examples.length) {
        body.append(node("div", "label", "Your mistakes"));
        const ul = node("ul", "quotes");
        s.examples.forEach((e) => {
          const li = node("li");
          li.append(node("span", "strike", e.wrong), " → ", node("strong", "", e.right));
          ul.append(li);
        });
        body.append(ul);
      }
      if (s.next_review) body.append(node("p", "muted", `Review on ${fmtDate(s.next_review)}`));
      head.addEventListener("click", () => body.classList.toggle("hidden"));
      row.append(head, body);
      group.append(row);
    });
    host.append(group);
  });
}



export function renderMistakes() {
  if (!accData) return;
  const skill = $("mis-skill").value;
  const body = $("mis-table").tBodies[0];
  body.textContent = "";
  const rows = accData.mistakes.filter((m) => !skill || m.skill === skill);
  if (!rows.length) {
    const tr = node("tr");
    const td = node("td", "empty", "No mistakes recorded yet.");
    td.colSpan = 5;
    tr.append(td);
    body.append(tr);
    return;
  }
  const names = Object.fromEntries(accData.skills.map((s) => [s.id, s.name]));
  rows.forEach((m) => {
    const tr = node("tr");
    const said = node("td");
    said.append(node("span", "strike", m.wrong), node("div", "muted", m.said));
    tr.append(node("td", "", fmtDate(m.ts)), said, node("td", "good-text", m.right),
              node("td", "", names[m.skill] || m.skill), node("td", "muted", m.why));
    body.append(tr);
  });
}

document.getElementById("mis-skill").addEventListener("input", renderMistakes);


// ── Intensive course ────────────────────────────────────────────────────────
// The course map: four weeks of lessons, the one to do now on top. `act` is
// how the page talks to the server: act("track", "intensive"), act("lesson", 3).

export async function loadIntensive(act) {
  const data = await fetch("/api/intensive").then((r) => r.json()).catch(() => null);
  const now = $("int-now"), weeks = $("int-weeks");
  now.textContent = "";
  weeks.textContent = "";
  document.querySelectorAll(".int-switch .seg").forEach((b) =>
    b.classList.toggle("active", (b.dataset.track === "intensive") === !!(data && data.active)));
  if (!data || data.error) {
    $("int-sub").textContent = "The course could not be loaded.";
    return;
  }
  renderCourseCards(data, act);
  if (!data.available) {
    $("int-title").textContent = "";
    $("int-sub").textContent = "";
    now.append(node("p", "", `There is no course for ${data.language} yet - choose one above.`));
    return;
  }
  $("int-title").textContent = data.title;
  const pct = Math.round((100 * data.done) / data.total);
  $("int-sub").textContent = `${data.done} of ${data.total} lessons done · ${pct}%`;

  const cur = data.lessons[data.current];
  const going = data.step > 0;
  now.append(node("div", "int-now-kicker", `Lesson ${cur.index + 1} · week ${cur.week}, day ${cur.day} · ${cur.band}`));
  now.append(node("h2", "int-now-title", cur.title));
  now.append(node("p", "int-now-goal", `After it you can ${cur.goal}.`));
  const words = node("div", "int-words");
  cur.words.forEach((w) => words.append(node("span", "int-word", w)));
  now.append(words);
  const bar = node("div", "int-bar");
  const fill = node("span");
  fill.style.width = `${Math.round((100 * data.step) / Math.max(1, data.steps))}%`;
  bar.append(fill);
  if (going) now.append(bar, node("p", "int-step", `Step ${data.step + 1} of ${data.steps}`));
  const go = node("button", "btn primary", going ? "Continue the lesson" : "Start the lesson");
  go.type = "button";
  go.addEventListener("click", () => act(data.active ? "open" : "track", "intensive"));
  now.append(go);

  data.weeks.forEach((wk) => {
    const sec = node("section", "int-week");
    const head = node("div", "int-week-head");
    head.append(node("h3", "", `Week ${wk.week} · ${wk.title}`), node("span", "badge lvl", wk.band));
    sec.append(head);
    const grid = node("div", "int-grid");
    data.lessons.filter((l) => l.week === wk.week).forEach((l) => {
      const tile = node("button", `int-tile ${l.state}`);
      tile.type = "button";
      tile.disabled = !l.open;
      tile.title = l.open ? l.goal : "Finish the lessons before it first";
      const top = node("span", "int-tile-top", `${l.index + 1}`);
      if (l.state === "done") top.append(node("span", "int-check", " ✓"));
      tile.append(top, node("span", "int-tile-title", l.title));
      tile.addEventListener("click", () => { if (l.open) act("lesson", l.index); });
      grid.append(tile);
    });
    sec.append(grid);
    weeks.append(sec);
  });
}

// The languages on the Courses page: the one being learned is marked, one
// without a course yet says so.
function renderCourseCards(data, act) {
  const host = $("course-cards");
  host.textContent = "";
  (data.courses || []).forEach((c) => {
    const card = node("button", "course-card" + (c.current && data.available ? " current" : ""));
    card.type = "button";
    card.disabled = !c.available;
    card.append(node("strong", "", c.name), node("span", "course-card-lvl", c.levels));
    card.append(node("span", "course-card-meta",
      c.available ? `${c.lessons} lessons · ${c.weeks} weeks` : "Hazırlanır - coming soon"));
    card.addEventListener("click", () => {
      if (!c.available) return;
      act("track", `intensive:${c.key}`);
      setTimeout(() => loadIntensive(act), 700);
    });
    host.append(card);
  });
}

// ── The course beside the board ─────────────────────────────────────────────

export function renderCourseSide(it, act) {
  if (!it) return;
  $("cs-course").textContent = it.course;
  $("cs-now").textContent = "";
  $("cs-now").append(node("span", "cs-kicker", `Lesson ${it.lesson} of ${it.total} · ${it.band}`),
                     node("strong", "", it.title));
  $("cs-bar").style.width = `${Math.round((100 * it.step) / Math.max(1, it.steps))}%`;
  const secs = $("cs-sections");
  secs.textContent = "";
  it.sections.forEach((sec) => {
    const here = it.step >= sec.start && it.step < sec.start + sec.count;
    const past = it.step >= sec.start + sec.count;
    const li = node("li", here ? "here" : past ? "past" : "");
    li.append(node("span", "", sec.label),
              node("span", "cs-count", here ? `${it.step - sec.start + 1}/${sec.count}` : past ? "✓" : `${sec.count}`));
    secs.append(li);
  });
  const list = $("cs-list");
  const sig = JSON.stringify(it.lessons.map((l) => l.state));
  if (list.dataset.sig === sig) return;
  list.dataset.sig = sig;
  list.textContent = "";
  it.weeks.forEach((wk) => {
    list.append(node("div", "cs-week", `Week ${wk.week} · ${wk.band}`));
    it.lessons.filter((l) => l.week === wk.week).forEach((l) => {
      const b = node("button", `cs-lesson ${l.state}`);
      b.type = "button";
      b.disabled = !l.open;
      b.append(node("span", "cs-num", l.state === "done" ? "✓" : `${l.index + 1}`), node("span", "", l.title));
      b.addEventListener("click", () => { if (l.open && l.state !== "current") act("lesson", l.index); });
      list.append(b);
    });
  });
  const cur = list.querySelector(".cs-lesson.current");
  if (cur) cur.scrollIntoView({ block: "center" });
}
