// The tutor - the LangVis face, drawn in SVG. It lives ON the board, walks to
// whatever it is explaining, and shows what it says in its speech bubble.
//
//   mouth   a smile; it opens with the REAL audio level of the voice being
//           played, and takes the shape of the letter being said (round for
//           o and u, wide for a, e and i, closed for m, b and p) - the words
//           in the speech block are typed out at the same pace
//   cheeks  a light blush, warmer when it talks or grins
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
const CHEEK = "#f08a74";
const MOUTH_Y = 248;

// The shape of the mouth for a letter: [width, how far it opens].
const SHAPES = {
  a: [1.05, 1], e: [1.15, 0.62], i: [1.2, 0.38], y: [1.2, 0.38], o: [0.7, 0.95], u: [0.58, 0.66],
  m: [0.95, 0], b: [0.95, 0], p: [0.95, 0], f: [1, 0.22], v: [1, 0.22], w: [0.62, 0.5],
};
function shapeOf(ch) {
  if (!ch) return [0.9, 0.25];
  const c = ch.normalize("NFD").charAt(0).toLowerCase();
  if (SHAPES[c]) return SHAPES[c];
  return /[a-z]/.test(c) ? [0.95, 0.5] : [0.9, 0.25];      // another consonant / a pause
}
let faces = 0;

function el(tag, attrs = {}, parent) {
  const node = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  if (parent) parent.append(node);
  return node;
}

export class TutorFace {
  // `opts.onReveal(text, done)`: the words said so far, as the mouth says them.
  constructor(host, audio, opts = {}) {
    this.audio = audio;
    this.onReveal = opts.onReveal || null;
    this.id = ++faces;
    this.full = "";            // the tutor's words of this turn, as far as they have arrived
    this.shownF = 0;           // how many of them have been "said" (typed out)
    this.done = false;
    this.shape = [1, 1];
    this.grin = 0;             // a happy open smile, 0..1 (the home page)
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
    this.cheeks = [182, 318].map((cx) => el("ellipse", { cx, cy: 246, rx: 13, ry: 7.5, fill: CHEEK }, this.root));
    // The mouth is one path: a smiling line when closed, a smiling open mouth
    // when it talks; the tongue is clipped to it.
    const clip = el("clipPath", { id: `tutor-mouth-${this.id}` }, defs);
    this.clipPath = el("path", {}, clip);
    this.mouthEl = el("path", { fill: C.ink, "stroke-linecap": "round", "stroke-linejoin": "round" }, this.root);
    this.tongue = el("ellipse", { fill: C.speak, "fill-opacity": 0.85,
                                  "clip-path": `url(#tutor-mouth-${this.id})` }, this.root);
    host.prepend(svg);
    this.svg = svg;
  }

  set(state, muted) {
    this.state = state;
    this.muted = !!muted;
  }

  // The tutor's words of this turn so far. They are typed out as the voice
  // says them, and the mouth takes the shape of the letter being said.
  follow(text, final) {
    text = text || "";
    let same = 0;
    const n = Math.min(this.full.length, text.length);
    while (same < n && this.full[same] === text[same]) same += 1;
    if (same < Math.min(12, text.length)) this.shownF = 0;      // a new turn
    else this.shownF = Math.min(this.shownF, same);
    this.full = text;
    this.done = !!final;
    if (!this.onReveal) this.shownF = text.length;
    this.reveal();
  }

  reveal() {
    const shown = Math.min(this.full.length, Math.floor(this.shownF));
    if (shown === this.revealed && this.done === this.revealedDone) return;
    this.revealed = shown;
    this.revealedDone = this.done;
    if (this.onReveal) this.onReveal(this.full.slice(0, shown), this.done && shown >= this.full.length);
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

    // Typing the words out at speaking pace: faster when they have piled up,
    // almost still while the voice pauses, and at once after it has stopped.
    if (this.full.length > this.shownF) {
      const backlog = this.full.length - this.shownF;
      let cps = 40;
      if (speaking) cps = backlog > 40 ? 26 : (amp < 0.03 && backlog < 25 ? 4 : 14);
      this.shownF = Math.min(this.full.length, this.shownF + cps * 0.033);
      this.reveal();
    } else if (this.done) this.reveal();

    // The letter being said gives the mouth its shape.
    const shapeTo = speaking ? shapeOf(this.full[Math.floor(this.shownF)]) : [1, 1];
    this.shape = this.shape.map((v, i) => v + (shapeTo[i] - v) * 0.45);

    let target;
    if (this.muted || this.state === "SLEEPING") target = 0;
    else if (speaking) target = (0.22 + amp * 1.5) * (0.35 + 0.65 * this.shape[1]) * (amp < 0.02 ? 0.3 : 1);
    else if (this.state === "THINKING") target = 0.03;
    else target = amp * 0.5 + this.grin * 0.3;
    target = Math.max(0, Math.min(1, target));
    this.mouth += (target - this.mouth) * (speaking ? 0.5 : 0.25);
    this.grin *= 0.97;

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
    const idle = this.state === "IDLE";          // only a picture (the home page)
    const listening = !(speaking || this.muted || this.state === "SLEEPING" || idle);

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

    const warm = this.muted ? 0.12 : 0.3 + amp * 0.35 + this.grin * 0.2;
    this.cheeks.forEach((c) => c.setAttribute("fill-opacity", warm.toFixed(3)));

    const open = this.mouth;
    const sad = this.muted || this.state === "SLEEPING";
    if (open < 0.06) {
      // Closed: a smiling line (flatter when muted or asleep).
      const curve = sad ? 5 : 15;
      this.mouthEl.setAttribute("d", `M226 ${MOUTH_Y - 1} Q250 ${MOUTH_Y - 1 + curve} 274 ${MOUTH_Y - 1}`);
      this.mouthEl.setAttribute("fill", "none");
      this.mouthEl.setAttribute("stroke", C.ink);
      this.mouthEl.setAttribute("stroke-width", 5.5);
      this.tongue.setAttribute("ry", 0);
    } else {
      // Open: a smile whose corners stay up, shaped by the letter being said.
      const [wf, hf] = this.shape;
      const w = (40 + open * 12) * (speaking ? wf : 1.05);
      const h = (7 + open * 26) * (speaking ? 0.55 + 0.45 * Math.max(hf, 0.25) : 1);
      const round = speaking ? Math.max(0, 1 - wf) * 1.6 : 0;      // o and u: rounder, corners lower
      const y0 = MOUTH_Y - 2 + round * 3;
      const l = 250 - w / 2, r = 250 + w / 2;
      const d = `M${l.toFixed(1)} ${y0.toFixed(1)} Q250 ${(y0 + 5 - round * 6).toFixed(1)} ${r.toFixed(1)} ${y0.toFixed(1)} `
              + `Q250 ${(y0 + h * 1.9).toFixed(1)} ${l.toFixed(1)} ${y0.toFixed(1)} Z`;
      this.mouthEl.setAttribute("d", d);
      this.mouthEl.setAttribute("fill", C.ink);
      this.mouthEl.setAttribute("stroke", C.ink);
      this.mouthEl.setAttribute("stroke-width", 2);
      this.clipPath.setAttribute("d", d);
      this.tongue.setAttribute("cx", 250);
      this.tongue.setAttribute("cy", (y0 + h * 0.95).toFixed(1));
      this.tongue.setAttribute("rx", (w * 0.3).toFixed(1));
      this.tongue.setAttribute("ry", open > 0.3 ? (h * 0.32).toFixed(1) : 0);
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
  // The face types it out as its mouth says it (TutorFace.follow).
  speech(text, final) {
    const box = this.speechBox;
    if (!box || !text) return;
    if (!this.face.onReveal) {
      this.face.onReveal = (shown, done) => {
        box.textContent = shown;
        box.classList.toggle("live", !done);
        box.closest(".speech").classList.remove("empty");
        box.scrollTop = box.scrollHeight;
      };
    }
    this.face.follow(text, final);
  }
}
