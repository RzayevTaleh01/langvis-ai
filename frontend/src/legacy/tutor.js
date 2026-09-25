// The tutor - the LangVis face, drawn in SVG. It lives ON the board, walks to
// whatever it is explaining, and shows what it says in its speech bubble.
//
//   mouth   opens with the REAL audio level of the voice being played
//   eyes    wide listening, narrowed explaining, looking away thinking,
//           closed asleep; the pupils look at the word it is pointing at
//   rim     the state colour - green listening, terracotta speaking,
//           mustard thinking, rose muted
//   rings   travel outwards while it listens, pushed by your voice

const NS = "http://www.w3.org/2000/svg";
const C = {
  panel: "#fffdf9", ink: "#23201a", seat: "#c2b195",
  pri: "#12695a", speak: "#c75a2b", think: "#c98a0a", muted: "#b23a3a", sleep: "#6d6556",
};
const BODY = "M250 110 C295 110 360 175 360 220 C360 265 295 330 250 330 " +
             "C205 330 140 265 140 220 C140 175 205 110 250 110 Z";
const EYE_L = "M190 230 L190 195 C190 178 205 168 220 168 C235 168 242 178 242 195 L242 230 Z";
const EYE_R = "M258 230 L258 195 C258 178 265 168 280 168 C295 168 310 178 310 195 L310 230 Z";

function el(tag, attrs = {}, parent) {
  const node = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (parent) parent.append(node);
  return node;
}

export class TutorFace {
  constructor(host, audio) {
    this.audio = audio;
    this.state = "SLEEPING";
    this.muted = false;
    this.look = null;          // {x, y} unit vector towards what it points at
    this.tick = 0;
    this.amp = 0;
    this.mouth = 0.15;
    this.blink = 0;
    this.nextBlink = 90;
    this.gaze = [0, 0];
    this.gazeTo = [0, 0];
    this.tilt = 0;
    this.build(host);
    this.last = performance.now();
    this.alive = true;
    requestAnimationFrame((t) => this.frame(t));
  }

  // The page closes: the animation stops and the face leaves.
  destroy() {
    this.alive = false;
    this.svg?.remove();
  }

  build(host) {
    const svg = el("svg", { viewBox: "80 50 340 340", class: "face", "aria-hidden": "true" });
    const defs = el("defs", {}, svg);
    const grad = el("linearGradient", { id: "tutor-shell", x1: 250, y1: 110, x2: 250, y2: 330,
                                         gradientUnits: "userSpaceOnUse" }, defs);
    this.stops = [0, 0.42, 0.78, 1].map((o) => el("stop", { offset: o }, grad));

    this.rings = [0, 1].map(() => el("circle", { cx: 250, cy: 220, r: 110, fill: "none" }, svg));
    this.root = el("g", {}, svg);
    for (let i = 0; i < 4; i++) {
      el("ellipse", { cx: 250, cy: 319 + i * 4.5, rx: 82 + i * 10, ry: 13 + i * 2.5,
                      fill: C.seat, "fill-opacity": (13 - i * 2) / 255 }, this.root);
    }
    el("path", { d: BODY, fill: "url(#tutor-shell)", stroke: "rgba(35,32,26,.1)", "stroke-width": 2 }, this.root);
    this.rim = el("path", { d: BODY, fill: "none" }, this.root);

    this.eyes = [true, false].map((left) => {
      const g = el("g", {}, this.root);
      el("path", { d: left ? EYE_L : EYE_R, fill: C.panel }, g);
      const pupil = el("rect", { width: 20, height: 20, rx: 4, fill: C.ink }, g);
      const glint = el("circle", { r: 2.5, fill: C.panel, "fill-opacity": 0.75 }, g);
      return { g, pupil, glint, cx: left ? 216 : 284, px: left ? 204 : 272 };
    });
    this.dots = [0, 1, 2].map((i) => el("circle", { cx: 214 + i * 36, cy: 86, r: 7, fill: C.think }, this.root));
    this.mouthEl = el("rect", { fill: C.ink }, this.root);
    this.tongue = el("rect", { fill: C.speak, "fill-opacity": 0.82 }, this.root);
    host.prepend(svg);
    this.svg = svg;
  }

  set(state, muted) {
    this.state = state;
    this.muted = !!muted;
  }

  tone() {
    if (this.muted) return C.muted;
    if (this.state === "SPEAKING") return C.speak;
    if (this.state === "THINKING") return C.think;
    if (this.state === "SLEEPING") return C.sleep;
    return C.pri;
  }

  frame(now) {
    if (!this.alive) return;
    // The desktop face steps at 30 fps; the same numbers are used here per
    // 33 ms of real time so both move identically.
    this.acc = Math.min(200, (this.acc || 0) + (now - this.last));
    this.last = now;
    if (this.acc >= 33) {
      while (this.acc >= 33) { this.step(); this.acc -= 33; }
      this.draw();
    }
    requestAnimationFrame((t) => this.frame(t));
  }

  step() {
    this.tick += 1;
    const speaking = this.state === "SPEAKING";
    const live = speaking ? this.audio.outputLevel()
      : (!this.muted && this.state === "LISTENING" ? this.audio.inputLevel() : 0);
    this.amp += (live - this.amp) * 0.45;
    const amp = this.amp;

    let target;
    if (this.muted || this.state === "SLEEPING") target = 0;
    else if (speaking) target = 0.22 + amp * 1.5;
    else if (this.state === "THINKING") target = 0.06;
    else target = 0.10 + amp * 0.5;
    target = Math.max(0, Math.min(1, target));
    this.mouth += (target - this.mouth) * (speaking ? 0.5 : 0.25);

    if (this.state === "SLEEPING") this.blink += (1 - this.blink) * 0.15;
    else {
      if (this.tick >= this.nextBlink) {
        this.blink = 1;
        this.nextBlink = this.tick + 70 + Math.floor(Math.random() * 80);
      }
      this.blink *= 0.72;
    }

    if (this.look) {
      // Looking at the word it is explaining.
      this.gazeTo = [this.look.x * 4, this.look.y * 3];
    } else if (this.tick % 40 === 0) {
      if (this.state === "THINKING") this.gazeTo = [-4 + Math.random() * 2, -3 + Math.random() * 2];
      else if (speaking) this.gazeTo = [-2 + Math.random() * 4, -1 + Math.random() * 2];
      else this.gazeTo = [-1.5 + Math.random() * 3, 0];
    }
    for (const i of [0, 1]) this.gaze[i] += (this.gazeTo[i] - this.gaze[i]) * 0.12;
    const tiltTo = this.look ? this.look.x * 7 : 0;
    this.tilt += (tiltTo - this.tilt) * 0.1;
  }

  draw() {
    const amp = this.amp;
    const tone = this.tone();
    const speaking = this.state === "SPEAKING";
    const thinking = this.state === "THINKING";
    const listening = !(speaking || this.muted || this.state === "SLEEPING");

    this.rings.forEach((ring, i) => {
      const phase = ((this.tick * 0.011) + i * 0.5) % 1;
      const alpha = (1 - phase) * (36 + amp * 120) / 255;
      const show = listening && !thinking && alpha > 0.01;
      ring.setAttribute("r", (112 + phase * 58).toFixed(1));
      ring.setAttribute("stroke", tone);
      ring.setAttribute("stroke-opacity", show ? alpha.toFixed(3) : 0);
      ring.setAttribute("stroke-width", 3);
    });

    const breathe = 1 + Math.sin(this.tick * 0.05) * 0.012 + amp * 0.03;
    const sway = thinking ? Math.sin(this.tick * 0.035) * 3 : 0;
    this.root.setAttribute("transform",
      `rotate(${(sway + this.tilt).toFixed(2)} 250 220) translate(250 220) scale(${breathe.toFixed(4)}) translate(-250 -220)`);

    const shell = this.muted ? ["#7e8a80", "#93a08f", "#93a08f", "#b6c0a6"]
      : ["#137a63", "#1fa872", "#64b348", "#bdd977"];
    this.stops.forEach((s, i) => s.setAttribute("stop-color", shell[i]));
    this.rim.setAttribute("stroke", tone);
    this.rim.setAttribute("stroke-opacity", speaking ? 0.82 : 0.47);
    this.rim.setAttribute("stroke-width", (4 + amp * 7).toFixed(2));

    let openY = thinking ? 0.82 : 1;
    if (speaking) openY = 0.88;
    if (this.muted) openY = 0.45;
    openY *= Math.max(0.06, 1 - this.blink);
    for (const eye of this.eyes) {
      eye.g.setAttribute("transform",
        `translate(${eye.cx} 199) scale(1 ${openY.toFixed(3)}) translate(${-eye.cx} -199)`);
      const px = eye.px + this.gaze[0];
      const py = 193 + this.gaze[1];
      eye.pupil.setAttribute("x", px.toFixed(2));
      eye.pupil.setAttribute("y", py.toFixed(2));
      eye.glint.setAttribute("cx", (px + 14.5).toFixed(2));
      eye.glint.setAttribute("cy", (py + 5.5).toFixed(2));
    }

    this.dots.forEach((dot, i) => {
      const phase = ((this.tick * 0.05 - i * 0.6) % 2.4 + 2.4) % 2.4;
      const lift = Math.max(0, Math.sin(phase * 1.3));
      dot.setAttribute("r", (7 + lift * 4).toFixed(2));
      dot.setAttribute("cy", (86 - lift * 10).toFixed(2));
      dot.setAttribute("fill-opacity", thinking ? ((70 + lift * 150) / 255).toFixed(3) : 0);
    });

    const open = this.mouth;
    if (open < 0.06) {
      Object.entries({ x: 232, y: 252, width: 36, height: 5, rx: 2.5 })
        .forEach(([k, v]) => this.mouthEl.setAttribute(k, v));
      this.tongue.setAttribute("height", 0);
    } else {
      const h = 8 + open * 30;
      const w = 38 + open * 10;
      this.mouthEl.setAttribute("x", (250 - w / 2).toFixed(2));
      this.mouthEl.setAttribute("y", 248);
      this.mouthEl.setAttribute("width", w.toFixed(2));
      this.mouthEl.setAttribute("height", h.toFixed(2));
      this.mouthEl.setAttribute("rx", Math.min(h * 0.5, w * 0.35).toFixed(2));
      if (open > 0.35) {
        const th = (h - 6) * 0.45;
        this.tongue.setAttribute("x", (250 - (w - 16) / 2).toFixed(2));
        this.tongue.setAttribute("y", (248 + h - th - 3).toFixed(2));
        this.tongue.setAttribute("width", (w - 16).toFixed(2));
        this.tongue.setAttribute("height", th.toFixed(2));
        this.tongue.setAttribute("rx", (th * 0.5).toFixed(2));
      } else {
        this.tongue.setAttribute("height", 0);
      }
    }
  }
}

// ── Moving about the board ──────────────────────────────────────────────────
// The tutor is absolutely positioned inside the board's scrolling content.

export class TutorWalker {
  // The tutor's home is at the top of the board, beside the block where what
  // it says is written. To explain something it walks down to it - the board
  // scrolls along with it - and when it is done it walks back home and the
  // board scrolls back up with it.
  constructor(board, node, face) {
    this.board = board;          // the scrolling board element
    this.node = node;            // the tutor wrapper (face + bubble)
    this.face = face;
    this.bubble = node.querySelector(".bubble");
    this.speechBox = document.getElementById("speech-text");
    this.target = null;
    this.atHome = true;
    this.home();
    this.onResize = () => this.reflow();
    this.onScroll = () => { if (!this.atHome) this.reflow(); };
    window.addEventListener("resize", this.onResize);
    board.addEventListener("scroll", this.onScroll, { passive: true });
    // Content above it grows or shrinks (a card arrives, a gap opens): stay put
    // next to the same thing, never on top of the next line.
    if ("ResizeObserver" in window) {
      this.resizeObs = new ResizeObserver(() => { if (!this.atHome) this.reflow(); });
      this.resizeObs.observe(board.firstElementChild || board);
      this.mutationObs = new MutationObserver(() => {
        if (this.target && !this.target.isConnected) this.home();   // what it pointed at is gone
      });
      this.mutationObs.observe(board, { childList: true, subtree: true });
    }
  }

  destroy() {
    clearTimeout(this.pointTimer);
    clearTimeout(this.pointTimer2);
    window.removeEventListener("resize", this.onResize);
    this.board.removeEventListener("scroll", this.onScroll);
    this.resizeObs?.disconnect();
    this.mutationObs?.disconnect();
  }

  size() { return this.node.offsetWidth || 88; }

  moveTo(x, y) {
    const maxX = this.board.scrollWidth - this.size() - 6;
    this.x = Math.max(6, Math.min(maxX, x));
    this.y = Math.max(6, y);
    this.node.style.transform = `translate(${this.x}px, ${this.y}px)`;
  }

  homeY() { return 10; }

  home() {
    clearTimeout(this.pointTimer);
    clearTimeout(this.pointTimer2);
    this.clearTarget();
    this.say("");
    this.face.look = { x: 1, y: 0 };      // looking at what it just said
    this.node.classList.remove("away");
    const wasAway = !this.atHome;
    this.atHome = true;
    this.moveTo(10, this.homeY());
    // Back beside what it said: the board goes back up with it.
    if (wasAway && this.board.scrollTop > 0) this.board.scrollTo({ top: 0, behavior: "smooth" });
  }

  clearTarget() {
    if (this.target) this.target.classList.remove("pointed");
    // The gap it stood in closes behind it.
    document.querySelectorAll(".tutor-lane").forEach((gap) => {
      gap.classList.remove("open");
      setTimeout(() => gap.remove(), 380);
    });
    this.target = null;
  }

  // The line the target sits on: the gap for the tutor opens right under it,
  // so it never stands on top of the next line.
  static lineOf(target) {
    return target.closest("li, .sentence, .lesson-title, .lesson-rule, .lesson-diagram, .fix, "
                          + ".item, .skill-moves, .repeat-line") || target;
  }

  openLane(target) {
    const line = TutorWalker.lineOf(target);
    const inList = line.parentElement && /^(UL|OL)$/.test(line.parentElement.tagName);
    const gap = document.createElement(inList ? "li" : "div");
    gap.className = "tutor-lane";
    gap.setAttribute("aria-hidden", "true");
    line.after(gap);
    void gap.offsetHeight;
    gap.classList.add("open");
  }

  // Walk down to `target` (an element on the board) and stand under it, with
  // a short note in the bubble.
  point(target, text, lane) {
    if (!target || !target.isConnected) return this.home();
    this.clearTarget();
    this.atHome = false;
    this.target = target;
    target.classList.add("pointed");
    this.openLane(target);
    this.say(text);
    this.node.classList.add("away");
    // Measure once the lane has started to open, and again when it is open.
    clearTimeout(this.pointTimer);
    clearTimeout(this.pointTimer2);
    this.pointTimer = setTimeout(() => this.reflow(true), 60);
    this.pointTimer2 = setTimeout(() => this.reflow(false), 420);
  }

  reflow(scroll) {
    if (!this.target) return;
    const b = this.board.getBoundingClientRect();
    const r = this.target.getBoundingClientRect();
    const line = TutorWalker.lineOf(this.target).getBoundingClientRect();
    const size = this.size();
    const x = r.left - b.left + this.board.scrollLeft + r.width / 2 - size / 2;
    // It stands in the gap under the whole line, not under the word's own row.
    const y = line.bottom - b.top + this.board.scrollTop + 4;
    this.moveTo(x, y);
    const dx = (r.left + r.width / 2) - (b.left + this.x - this.board.scrollLeft + size / 2);
    this.face.look = { x: Math.max(-1, Math.min(1, dx / 60)), y: -1 };
    const roomRight = this.board.clientWidth - (this.x - this.board.scrollLeft + size);
    this.node.classList.toggle("bubble-left", roomRight < 240);
    if (scroll) {
      // The board follows the tutor: what it explains is kept in view below
      // the speech block, never hidden under it.
      const itemTop = r.top - b.top;                         // relative to the visible board
      const itemBottom = y - this.board.scrollTop + size;
      if (itemTop < 12 || itemBottom > this.board.clientHeight - 12) {
        const want = r.top - b.top + this.board.scrollTop - 60;
        this.board.scrollTo({ top: Math.max(0, want), behavior: "smooth" });
      }
    }
  }

  // The bubble only carries short notes about what it points at.
  say(text) {
    this.bubble.textContent = "";
    if (!text) { this.bubble.classList.add("hidden"); return; }
    if (typeof text === "string") this.bubble.textContent = text;
    else this.bubble.append(text);
    this.bubble.classList.remove("hidden");
  }

  // What the tutor says is written in the speech block at the top of the board.
  speech(text, final) {
    const box = this.speechBox;
    if (!box || !text) return;
    box.textContent = text;
    box.classList.toggle("live", !final);
    box.closest(".speech").classList.remove("empty");
    box.scrollTop = box.scrollHeight;
  }
}
