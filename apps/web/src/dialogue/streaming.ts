/* Streaming voice client: mic -> backend WS -> Meta live ASR (TRD 7.4).
   The browser captures mic audio, resamples to 24 kHz mono Int16 PCM in an
   inline AudioWorklet, and streams ~80ms binary frames to
   /api/v1/sessions/{id}/voice. Normalized app events come back as text:
   partial (ephemeral), final (authoritative turn text), boundary
   (barge-in: stop TTS when the expert starts talking), speaker, error.
   Returns false from start() when the relay is unreachable so the caller
   falls back to on-device browser speech. */

import { stopSpeaking } from "./speech";

export interface RelayCallbacks {
  onPartial(text: string, turn: number): void;
  onFinal(text: string, turn: number): void;
  onNote(msg: string): void;
  onError(msg: string): void;
  onClosed?(): void;
  onAudioFrame?(): void;
}

const WORKLET = `
class Pcm24k extends AudioWorkletProcessor {
  constructor() { super(); this._buf = []; this._ratio = sampleRate / 24000; this._acc = 0; }
  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    if (!ch) return true;
    for (let i = 0; i < ch.length; i++) {
      this._acc += 1;
      while (this._acc >= this._ratio) {
        this._acc -= this._ratio;
        const s = Math.max(-1, Math.min(1, ch[i]));
        this._buf.push(s < 0 ? s * 0x8000 : s * 0x7fff);
        if (this._buf.length >= 1920) {
          const frame = new Int16Array(this._buf.splice(0, 1920));
          this.port.postMessage(frame, [frame.buffer]);
        }
      }
    }
    return true;
  }
}
registerProcessor("pcm24k", Pcm24k);
`;

let primedContext: AudioContext | null = null;

export function primeVoiceAudio(): void {
  if (primedContext || typeof window.AudioContext === "undefined") return;
  try {
    primedContext = new window.AudioContext();
    void primedContext.resume();
  } catch { /* browser speech may still be available */ }
}

export class RelayVoice {
  private ws: WebSocket | null = null;
  private ctx: AudioContext | null = null;
  private src: MediaStreamAudioSourceNode | null = null;
  private node: AudioWorkletNode | null = null;
  private sink: GainNode | null = null;
  private stopping = false;
  private sentAudio = false;

  constructor(
    private sessionId: string,
    private cb: RelayCallbacks,
  ) {}

  async start(mic: MediaStream): Promise<boolean> {
    this.stopping = false;
    this.sentAudio = false;
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${window.location.host}/api/v1/sessions/${this.sessionId}/voice`;
    let ws: WebSocket;
    try {
      ws = new WebSocket(url);
    } catch {
      return false;
    }
    let failure = "Voice socket did not become ready.";
    const opened = await new Promise<boolean>((resolve) => {
      const to = window.setTimeout(() => resolve(false), 6500);
      const settle = (ok: boolean) => { window.clearTimeout(to); resolve(ok); };
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(String(event.data));
          if (message.kind === "hello") settle(true);
          else if (message.kind === "error") {
            failure = String(message.message ?? "voice relay unavailable");
            settle(false);
          }
        } catch { /* ignore non-JSON handshake data */ }
      };
      ws.onerror = () => { failure = "Voice WebSocket failed before recognition started."; settle(false); };
      ws.onclose = () => { failure = "Voice WebSocket closed before recognition started."; settle(false); };
    });
    if (!opened) {
      this.cb.onError(failure);
      try {
        ws.close();
      } catch {
        /* ignore */
      }
      return false;
    }
    this.ws = ws;
    ws.onmessage = (ev: MessageEvent) => {
      try {
        const m = JSON.parse(String(ev.data));
        if (m.kind === "hello") {
          this.cb.onNote(
            m.execution_mode === "mock"
              ? "Voice relay in mock mode — rehearsal turns, not billed."
              : "Live voice relay connected.",
          );
        } else if (m.kind === "partial") {
          this.cb.onPartial(String(m.text ?? ""), Number(m.turn ?? 0));
        } else if (m.kind === "final") {
          this.cb.onFinal(String(m.text ?? ""), Number(m.turn ?? 0));
        } else if (m.kind === "boundary" && m.phase === "start") {
          stopSpeaking(); // barge-in: expert started talking, yield the floor
        } else if (m.kind === "error") {
          this.cb.onError(String(m.message ?? "voice error"));
        }
      } catch {
        /* non-JSON frame: ignore */
      }
    };
    ws.onclose = () => {
      const wasStopping = this.stopping;
      this.stop();
      if (!wasStopping) {
        this.cb.onError("Voice relay disconnected.");
        this.cb.onClosed?.();
      }
    };
    try {
      const Ctx = window.AudioContext;
      this.ctx = primedContext ?? new Ctx();
      primedContext = null;
      await this.ctx.resume();
      const blob = new Blob([WORKLET], { type: "application/javascript" });
      const workletUrl = URL.createObjectURL(blob);
      try {
        await this.ctx.audioWorklet.addModule(workletUrl);
      } finally {
        URL.revokeObjectURL(workletUrl);
      }
      this.src = this.ctx.createMediaStreamSource(mic);
      this.node = new AudioWorkletNode(this.ctx, "pcm24k");
      this.node.port.onmessage = (e: MessageEvent) => {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          const arr = e.data as Int16Array;
          if (this.ws.bufferedAmount > 192_000) {
            this.cb.onError("Audio uplink stalled; switching recognition mode.");
            this.ws.close(4000, "audio uplink stalled");
          } else if (arr.length > 0) {
            this.ws.send(arr.buffer);
            if (!this.sentAudio) { this.sentAudio = true; this.cb.onAudioFrame?.(); }
          }
        }
      };
      this.src.connect(this.node);
      this.sink = this.ctx.createGain();
      this.sink.gain.value = 0;
      this.node.connect(this.sink);
      this.sink.connect(this.ctx.destination);
    } catch (error) {
      this.cb.onError(`Microphone stream could not start (${error instanceof Error ? error.name : "unknown"}).`);
      this.stop();
      return false;
    }
    return true;
  }

  stop(): void {
    this.stopping = true;
    try {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "endStream" }));
        this.ws.close();
      }
    } catch {
      /* already closing */
    }
    this.ws = null;
    try {
      this.node?.disconnect();
      this.src?.disconnect();
      this.sink?.disconnect();
      void this.ctx?.close();
    } catch {
      /* already stopped */
    }
    this.node = null;
    this.src = null;
    this.sink = null;
    this.ctx = null;
  }
}
