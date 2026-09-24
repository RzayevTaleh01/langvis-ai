// Pictures the teacher draws on the board: what a tense MEANS in time, how a
// sentence is BUILT, which of two forms goes where. Specs come from
// tutor/curriculum.py (SKILL_BOARD); every stroke is drawn in, one after the
// other, like chalk - `draw()` returns the pieces in the order they appear, so
// the tutor can walk along with them.

const NS = "http://www.w3.org/2000/svg";
const W = 560;

function el(tag, attrs = {}, parent) {
  const n = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  if (parent) parent.append(n);
  return n;
}

function text(parent, x, y, str, cls = "d-text", anchor = "middle") {
  const t = el("text", { x, y, class: cls, "text-anchor": anchor }, parent);
  t.textContent = str;
  return t;
}

// A group that "appears": strokes draw in, text fades in, in sequence.
function step(parent, i) {
  return el("g", { class: "d-step", style: `--i:${i}` }, parent);
}

function timeline(svg, items) {
  const H = 176, y = 92, L = 30, R = W - 30;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const x = (v) => L + (v + 1) / 2 * (R - L);
  let i = 0;
  const axis = step(svg, i++);
  el("line", { x1: L, y1: y, x2: R, y2: y, class: "d-axis" }, axis);
  el("path", { d: `M${R - 8} ${y - 6} L${R} ${y} L${R - 8} ${y + 6}`, class: "d-axis" }, axis);
  text(axis, L + 4, y + 26, "PAST", "d-small", "start");
  text(axis, R - 4, y + 26, "FUTURE", "d-small", "end");
  el("line", { x1: x(0), y1: y - 12, x2: x(0), y2: y + 12, class: "d-now" }, axis);
  text(axis, x(0), y + 26, "NOW", "d-small d-now-text");
  const pieces = [axis];
  // Labels take turns above and below the line, so two never sit on each other.
  items.forEach((it, k) => {
    const g = step(svg, i++);
    const below = k % 2 === 1;
    const ly = (above, belowY) => (below ? belowY : above);
    if (it.type === "point") {
      el("circle", { cx: x(it.at), cy: y, r: 7, class: "d-mark" }, g);
      if (below) el("line", { x1: x(it.at), y1: y + 9, x2: x(it.at), y2: y + 40, class: "d-tick" }, g);
      else el("line", { x1: x(it.at), y1: y - 9, x2: x(it.at), y2: y - 18, class: "d-tick" }, g);
      text(g, x(it.at), ly(y - 24, y + 58), it.label || "");
    } else if (it.type === "range") {
      el("rect", { x: x(it.from), y: y - 10, width: x(it.to) - x(it.from), height: 20, rx: 8, class: "d-range" }, g);
      text(g, (x(it.from) + x(it.to)) / 2, ly(y - 22, y + 58), it.label || "");
    } else if (it.type === "repeat") {
      const n = it.n || 5;
      for (let k = 0; k < n; k++) {
        const cx = x(it.from + (it.to - it.from) * k / (n - 1));
        el("path", { d: `M${cx - 6} ${y - 6} L${cx + 6} ${y + 6} M${cx + 6} ${y - 6} L${cx - 6} ${y + 6}`, class: "d-mark-line" }, g);
      }
      text(g, (x(it.from) + x(it.to)) / 2, ly(y - 22, y + 58), it.label || "");
    } else if (it.type === "arrow") {
      const x1 = x(it.from), x2 = x(it.to);
      el("path", { d: `M${x1} ${y - 30} C${x1 + 30} ${y - 58}, ${x2 - 30} ${y - 58}, ${x2} ${y - 30}`, class: "d-arrow" }, g);
      el("path", { d: `M${x2 - 9} ${y - 38} L${x2} ${y - 30} L${x2 - 11} ${y - 27}`, class: "d-arrow" }, g);
      text(g, (x1 + x2) / 2, y - 60, it.label || "");
    } else if (it.type === "cross") {
      el("path", { d: `M${x(it.at) - 10} ${y - 10} L${x(it.at) + 10} ${y + 10} M${x(it.at) + 10} ${y - 10} L${x(it.at) - 10} ${y + 10}`, class: "d-cross" }, g);
      text(g, x(it.at), ly(y - 22, y + 58), it.label || "", "d-text d-bad");
    }
    pieces.push(g);
  });
  return pieces;
}

function boxes(svg, items, { arrows = false, rising = false } = {}) {
  const n = items.length;
  const gap = arrows ? 34 : 12;
  const bw = Math.min(160, (W - 20 - gap * (n - 1)) / n);
  const H = rising ? 170 : 110;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const total = bw * n + gap * (n - 1);
  let x = (W - total) / 2;
  const pieces = [];
  items.forEach((label, k) => {
    const g = step(svg, k);
    const h = rising ? 40 + k * (90 / Math.max(1, n - 1)) : 56;
    const y = H - 20 - h;
    const isLink = arrows && (label === "→" || /^(so|however,|and|but|because|\+|=)$/i.test(label));
    if (isLink) {
      el("path", { d: `M${x + 4} ${y + h / 2} L${x + bw - 8} ${y + h / 2}`, class: "d-arrow" }, g);
      el("path", { d: `M${x + bw - 16} ${y + h / 2 - 7} L${x + bw - 8} ${y + h / 2} L${x + bw - 16} ${y + h / 2 + 7}`, class: "d-arrow" }, g);
      if (label !== "→") text(g, x + bw / 2, y + h / 2 - 12, label, "d-small");
    } else {
      el("rect", { x, y, width: bw, height: h, rx: 10, class: rising ? "d-step-box" : "d-box" }, g);
      text(g, x + bw / 2, y + h / 2 + 5, label, "d-text");
    }
    pieces.push(g);
    x += bw + gap;
  });
  return pieces;
}

function nest(svg, rings) {
  const H = 200;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const pieces = [];
  rings.forEach(([word, what], k) => {
    const g = step(svg, k);
    const pad = k * 34;
    el("rect", { x: 20 + pad, y: 10 + pad * 0.9, width: W - 40 - pad * 2, height: H - 20 - pad * 1.8, rx: 16,
                 class: "d-ring d-ring-" + k }, g);
    text(g, 36 + pad, 36 + pad * 0.9, word.toUpperCase(), "d-word", "start");
    text(g, 90 + pad, 36 + pad * 0.9, what, "d-small", "start");
    pieces.push(g);
  });
  return pieces;
}

function split(svg, left, right) {
  const rows = Math.max(left.lines.length, right.lines.length);
  const H = 60 + rows * 30;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const pieces = [];
  [left, right].forEach((col, k) => {
    const g = step(svg, k);
    const x = k ? W / 2 + 10 : 10;
    const w = W / 2 - 20;
    el("rect", { x, y: 6, width: w, height: H - 12, rx: 12, class: k ? "d-col d-col-b" : "d-col" }, g);
    text(g, x + w / 2, 34, col.title, "d-word");
    col.lines.forEach((line, j) => text(g, x + w / 2, 66 + j * 30, line, "d-text"));
    pieces.push(g);
  });
  const mid = step(svg, 2);
  text(mid, W / 2, H / 2 + 6, "vs", "d-small");
  pieces.push(mid);
  return pieces;
}

function shift(svg, pairs) {
  const H = 30 + pairs.length * 34;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const pieces = [];
  text(step(svg, 0), W * 0.3, 22, "they said", "d-small");
  text(step(svg, 0), W * 0.7, 22, "you report", "d-small");
  pairs.forEach(([a, b], k) => {
    const g = step(svg, k + 1);
    const y = 50 + k * 34;
    text(g, W * 0.3, y, a, "d-text");
    el("path", { d: `M${W * 0.42} ${y - 5} L${W * 0.58} ${y - 5}`, class: "d-arrow" }, g);
    el("path", { d: `M${W * 0.58 - 8} ${y - 11} L${W * 0.58} ${y - 5} L${W * 0.58 - 8} ${y + 1}`, class: "d-arrow" }, g);
    text(g, W * 0.7, y, b, "d-word");
    pieces.push(g);
  });
  return pieces;
}

// Their own sentence as blocks, twice: what they said with the wrong block
// crossed out, then the fixed sentence with the new block marked.
function fix(svg, spec) {
  const rows = [
    { chunks: spec.wrong || [], marked: new Set(spec.bad || []), cls: "d-fix-bad", tag: "you said" },
    { chunks: spec.right || [], marked: new Set(spec.good || []), cls: "d-fix-good", tag: "say" },
  ];
  const H = 150;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const pieces = [];
  rows.forEach((row, r) => {
    const g = step(svg, r);
    const y = 18 + r * 70;
    text(g, 6, y - 4, row.tag.toUpperCase(), "d-small", "start");
    // Each block is as wide as its words; the row is scaled down to fit.
    const widths = row.chunks.map((c) => 22 + c.length * 10.5);
    const gap = 8;
    const total = widths.reduce((a, b) => a + b, 0) + gap * Math.max(0, widths.length - 1);
    const k = Math.min(1, (W - 12) / total);
    let x = 6;
    row.chunks.forEach((c, i) => {
      const w = widths[i] * k;
      const on = row.marked.has(i);
      el("rect", { x, y: y + 4, width: w, height: 38, rx: 9, class: on ? `d-box ${row.cls}` : "d-box d-fix-plain" }, g);
      text(g, x + w / 2, y + 29, c, on ? `d-text ${row.cls}-text` : "d-text");
      if (on && r === 0) {
        el("line", { x1: x + 6, y1: y + 23, x2: x + w - 6, y2: y + 23, class: "d-fix-strike" }, g);
      }
      x += w + gap * k;
    });
    pieces.push(g);
  });
  return pieces;
}

// Draw `spec` into `host`. Returns the pieces in drawing order.
export function draw(host, spec) {
  host.textContent = "";
  if (!spec || !spec.kind) return [];
  const svg = el("svg", { class: "diagram", role: "img" }, host);
  const items = (spec.items || []).filter((x) => x !== "" && x !== null && x !== undefined);
  switch (spec.kind) {
    case "timeline": return timeline(svg, items);
    case "flow": return boxes(svg, items, { arrows: true });
    case "ladder": return boxes(svg, items, { rising: true });
    case "blocks": return boxes(svg, items);
    case "nest": return nest(svg, items);
    case "split": return split(svg, spec.left || { title: "", lines: [] }, spec.right || { title: "", lines: [] });
    case "shift": return shift(svg, items);
    case "fix": return fix(svg, spec);
    default: host.textContent = ""; return [];
  }
}
