// Runs on the audio thread. Takes the microphone at the context's own rate
// (usually 48 kHz), averages it down to 16 kHz mono - the average is a cheap
// low-pass, so the downsampling does not alias - and posts int16 blocks of
// 1024 samples (64 ms) to the page, which sends them to the server as they are.

const TARGET_RATE = 16000;
const BLOCK = 1024;

class MicProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.ratio = sampleRate / TARGET_RATE;
    this.phase = 0;
    this.acc = 0;
    this.accN = 0;
    this.out = new Int16Array(BLOCK);
    this.n = 0;
  }

  process(inputs) {
    const channel = inputs[0] && inputs[0][0];
    if (!channel) return true;
    for (let i = 0; i < channel.length; i++) {
      this.acc += channel[i];
      this.accN += 1;
      this.phase += 1;
      if (this.phase >= this.ratio) {
        this.phase -= this.ratio;
        const s = Math.max(-1, Math.min(1, this.acc / this.accN));
        this.acc = 0;
        this.accN = 0;
        this.out[this.n++] = s < 0 ? s * 0x8000 : s * 0x7fff;
        if (this.n === BLOCK) {
          this.port.postMessage(this.out.buffer, [this.out.buffer]);
          this.out = new Int16Array(BLOCK);
          this.n = 0;
        }
      }
    }
    return true;
  }
}

registerProcessor("mic-processor", MicProcessor);
