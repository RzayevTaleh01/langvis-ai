// Sound in the browser: the microphone going out, the tutor's voice coming in,
// and a 0..1 loudness for each so the face can move with the real audio.

const RECEIVE_RATE = 24000;
const START_DELAY = 0.06;   // seconds of slack before the first chunk of a turn

function rms(analyser, buf) {
  analyser.getFloatTimeDomainData(buf);
  let sum = 0;
  for (let i = 0; i < buf.length; i++) sum += buf[i] * buf[i];
  return Math.sqrt(sum / buf.length);
}

// Same shape as main.py's _pcm_level: quiet room → 0, loud speech → 1.
function level(value) {
  const floor = 0.004, full = 0.12;
  if (value <= floor) return 0;
  return Math.min(1, (value - floor) / (full - floor));
}

export class Audio {
  constructor() {
    this.ctx = null;
    this.next = 0;
    this.sources = new Set();
    this.onMicBlock = null;     // (ArrayBuffer) => void
    this.micReady = false;
  }

  // Opens the microphone. The browser may keep the speaker locked until the
  // first click on the page - then `canPlay()` is false and `unlock()` must be
  // called from that click. (Awaiting resume() here would hang until then.)
  async start() {
    this.ctx = new (window.AudioContext || window.webkitAudioContext)();
    this.ctx.resume().catch(() => {});

    this.gain = this.ctx.createGain();
    this.outAnalyser = this.ctx.createAnalyser();
    this.outAnalyser.fftSize = 1024;
    this.outAnalyser.minDecibels = -85;
    this.outAnalyser.maxDecibels = -25;
    this.gain.connect(this.outAnalyser);
    this.outAnalyser.connect(this.ctx.destination);
    this.outBuf = new Float32Array(this.outAnalyser.fftSize);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      await this.ctx.audioWorklet.addModule("/static/mic-worklet.js");
      const source = this.ctx.createMediaStreamSource(stream);
      const worklet = new AudioWorkletNode(this.ctx, "mic-processor");
      worklet.port.onmessage = (e) => this.onMicBlock && this.onMicBlock(e.data);
      source.connect(worklet);
      // A worklet only runs when it is pulled; a silent gain keeps it pulled
      // without the learner hearing themselves.
      const sink = this.ctx.createGain();
      sink.gain.value = 0;
      worklet.connect(sink).connect(this.ctx.destination);

      this.inAnalyser = this.ctx.createAnalyser();
      this.inAnalyser.fftSize = 1024;
      this.inAnalyser.minDecibels = -85;
      this.inAnalyser.maxDecibels = -25;
      source.connect(this.inAnalyser);
      this.inBuf = new Float32Array(this.inAnalyser.fftSize);
      this.micReady = true;
    } catch (err) {
      console.warn("microphone unavailable", err);
      this.micReady = false;
    }
    return this.micReady;
  }

  play(arrayBuffer) {
    if (!this.ctx) return;
    const pcm = new Int16Array(arrayBuffer);
    if (!pcm.length) return;
    const samples = new Float32Array(pcm.length);
    for (let i = 0; i < pcm.length; i++) samples[i] = pcm[i] / 32768;
    const buffer = this.ctx.createBuffer(1, samples.length, RECEIVE_RATE);
    buffer.copyToChannel(samples, 0);
    const src = this.ctx.createBufferSource();
    src.buffer = buffer;
    src.connect(this.gain);
    const at = Math.max(this.next, this.ctx.currentTime + START_DELAY);
    src.start(at);
    this.next = at + buffer.duration;
    this.sources.add(src);
    src.onended = () => this.sources.delete(src);
  }

  // Interrupt: everything already scheduled stops now.
  flush() {
    for (const src of this.sources) {
      try { src.stop(); } catch (_) { /* already ended */ }
    }
    this.sources.clear();
    this.next = 0;
  }

  canPlay() {
    return !!this.ctx && this.ctx.state === "running";
  }

  unlock() {
    return this.ctx ? this.ctx.resume().catch(() => {}) : Promise.resolve();
  }

  // True while the tutor's voice is still coming out of the speaker, and for
  // `tail` seconds after - the room still rings with it.
  busy(tail = 0.4) {
    return !!this.ctx && this.next + tail > this.ctx.currentTime;
  }

  // The voice as `n` bands of loudness, 0..1, low pitch first - for the wave.
  // `which`: "in" (the learner) or "out" (the tutor).
  spectrum(which, n) {
    const an = which === "in" ? this.inAnalyser : this.outAnalyser;
    const out = new Array(n).fill(0);
    if (!an) return out;
    if (!this.freq || this.freq.length !== an.frequencyBinCount) this.freq = new Uint8Array(an.frequencyBinCount);
    an.getByteFrequencyData(this.freq);
    // Speech lives between ~90 Hz and ~4 kHz; the bands are spaced like the ear hears.
    const hz = this.ctx.sampleRate / 2 / an.frequencyBinCount;
    const lo = Math.max(1, Math.round(90 / hz)), hi = Math.round(4000 / hz);
    for (let i = 0; i < n; i++) {
      const a = Math.floor(lo * Math.pow(hi / lo, i / n));
      const b = Math.max(a + 1, Math.floor(lo * Math.pow(hi / lo, (i + 1) / n)));
      let sum = 0;
      for (let k = a; k < b; k++) sum += this.freq[k];
      out[i] = sum / (b - a) / 255;
    }
    return out;
  }

  outputLevel() {
    return this.outAnalyser ? level(rms(this.outAnalyser, this.outBuf)) : 0;
  }

  inputLevel() {
    return this.inAnalyser ? level(rms(this.inAnalyser, this.inBuf)) : 0;
  }
}
