/* eslint-disable @typescript-eslint/no-explicit-any */
// The small SVG charts of the Account page, drawn as in the original page:
// one series each, a recessive grid, and a hover readout.

const NS = "http://www.w3.org/2000/svg";

function node(tag: string, cls?: string, text?: string | null): HTMLElement {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text !== undefined && text !== null) n.textContent = text;
  return n;
}

function svg(tag: string, attrs: Record<string, any> = {}, parent?: Element): SVGElement {
  const n = document.createElementNS(NS, tag) as SVGElement;
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, String(v));
  if (parent) parent.append(n);
  return n;
}

export function fmtDate(iso?: string | null): string {
  if (!iso) return "-";
  const d = new Date(iso.length <= 10 ? iso + "T12:00:00" : iso);
  return d.toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

// ── Tooltip ──────────────────────────────────────────────────────────────────

const tip = () => document.getElementById("tooltip");
export function showTip(evt: MouseEvent, lines: string[]) {
  const t = tip();
  if (!t) return;
  t.textContent = "";
  lines.forEach((l, i) => t.append(i ? node("div", "", l) : node("strong", "", l)));
  t.classList.remove("hidden");
  const x = Math.min(window.innerWidth - t.offsetWidth - 12, evt.clientX + 14);
  const y = Math.max(8, evt.clientY - t.offsetHeight - 10);
  t.style.transform = `translate(${x}px, ${y}px)`;
}
export function hideTip() { tip()?.classList.add("hidden"); }

function empty(host: HTMLElement, text: string) {
  host.textContent = "";
  host.append(node("p", "empty", text));
}

type Point = { x: string; y: number; extra?: string[] };

export function lineChart(host: HTMLElement, points: Point[], { min = 0, max, guides = [], fmt = (v: number) => String(v), area = false, unit = "" }:
  { min?: number; max?: number; guides?: { v: number; label?: string }[]; fmt?: (v: number) => string | number; area?: boolean; unit?: string }) {
  if (points.length < 1) return empty(host, "Not enough practice days yet.");
  host.textContent = "";
  const W = 560, H = 220, L = 34, R = 12, T = 12, B = 26;
  const top = max ?? Math.max(1, ...points.map((p) => p.y)) * 1.15;
  const s = svg("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart-svg", role: "img" }, host);
  const x = (i: number) => L + (points.length === 1 ? (W - L - R) / 2 : i * (W - L - R) / (points.length - 1));
  const y = (v: number) => T + (H - T - B) * (1 - (v - min) / (top - min));

  const ticks = guides.length ? guides : [0, top / 2, top].map((v) => ({ v: Math.round(v), label: undefined as string | undefined }));
  ticks.forEach((g) => {
    svg("line", { x1: L, x2: W - R, y1: y(g.v), y2: y(g.v), class: g.label ? "guide" : "grid" }, s);
    const t = svg("text", { x: L - 6, y: y(g.v) + 4, class: "axis", "text-anchor": "end" }, s);
    t.textContent = String(g.label || g.v);
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
  lab.textContent = String(fmt(last.y));

  [0, points.length - 1].filter((v, i, a) => a.indexOf(v) === i).forEach((i) => {
    const t = svg("text", { x: x(i), y: H - 6, class: "axis", "text-anchor": i ? "end" : "start" }, s);
    t.textContent = fmtDate(points[i].x);
  });

  // Crosshair: the nearest day under the pointer.
  const cross = svg("line", { y1: T, y2: H - B, class: "cross hidden" }, s);
  const hit = svg("rect", { x: L, y: T, width: W - L - R, height: H - T - B, fill: "transparent" }, s);
  hit.addEventListener("mousemove", (e: any) => {
    const box = s.getBoundingClientRect();
    const px = (e.clientX - box.left) * (W / box.width);
    let best = 0;
    points.forEach((_p, i) => { if (Math.abs(x(i) - px) < Math.abs(x(best) - px)) best = i; });
    cross.setAttribute("x1", String(x(best)));
    cross.setAttribute("x2", String(x(best)));
    cross.classList.remove("hidden");
    showTip(e, [fmtDate(points[best].x), `${fmt(points[best].y)}${unit}`, ...(points[best].extra || [])]);
  });
  hit.addEventListener("mouseleave", () => { cross.classList.add("hidden"); hideTip(); });
}

export function barChart(host: HTMLElement, points: Point[], { unit = "" }: { unit?: string }) {
  if (!points.length) return empty(host, "No mistakes recorded yet.");
  host.textContent = "";
  const W = 560, H = 220, L = 34, R = 12, T = 12, B = 26;
  const top = Math.max(1, ...points.map((p) => p.y)) * 1.15;
  const s = svg("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart-svg", role: "img" }, host);
  const slot = (W - L - R) / points.length;
  const bw = Math.max(3, Math.min(28, slot - 2));
  const y = (v: number) => T + (H - T - B) * (1 - v / top);
  [Math.round(top / 2), Math.round(top)].forEach((v) => {
    svg("line", { x1: L, x2: W - R, y1: y(v), y2: y(v), class: "grid" }, s);
    svg("text", { x: L - 6, y: y(v) + 4, class: "axis", "text-anchor": "end" }, s).textContent = String(v);
  });
  points.forEach((p, i) => {
    const bx = L + i * slot + (slot - bw) / 2;
    const h = Math.max(p.y ? 2 : 0, H - B - y(p.y));
    // Rounded at the data end only, square on the baseline.
    const r = Math.min(4, bw / 2, h);
    const top_ = H - B - h;
    svg("path", { class: "bar", d: `M${bx} ${H - B} V${top_ + r} Q${bx} ${top_} ${bx + r} ${top_} H${bx + bw - r} Q${bx + bw} ${top_} ${bx + bw} ${top_ + r} V${H - B} Z` }, s);
    const hit = svg("rect", { x: L + i * slot, y: T, width: slot, height: H - T - B, fill: "transparent" }, s);
    hit.addEventListener("mousemove", (e: any) => showTip(e, [fmtDate(p.x), `${p.y}${unit}`, ...(p.extra || [])]));
    hit.addEventListener("mouseleave", hideTip);
  });
  svg("line", { x1: L, x2: W - R, y1: H - B, y2: H - B, class: "baseline" }, s);
  [0, points.length - 1].filter((v, i, a) => a.indexOf(v) === i).forEach((i) => {
    svg("text", { x: L + i * slot + slot / 2, y: H - 6, class: "axis", "text-anchor": i ? "end" : "start" }, s)
      .textContent = fmtDate(points[i].x);
  });
}
