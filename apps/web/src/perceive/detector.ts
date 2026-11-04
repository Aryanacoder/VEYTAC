/* On-device perception tracker: hands + objects, no paid calls.
   MediaPipe Tasks-Vision (HandLandmarker + EfficientDet-Lite0) runs fully
   in the browser at ~5fps on 320px frames. Model bundles download once at
   first use from local, version-pinned assets (see HOSTING.md); analysis never
   leaves the device. If the library or models are unavailable, this
   reports NullTracker (ready=false) instead of inventing detections. */

import type { Box, FrameDesc } from "./events";

export const TASKS_VERSION = "0.10.20";
export const WASM_URL = "/vision/wasm";
export const HAND_MODEL_URL = "/vision/hand_landmarker.task";
export const OBJECT_MODEL_URL = "/vision/efficientdet_lite0.tflite";

const FRAME_W = 320;
const MIN_SCORE = 0.25;
const MAX_RESULTS = 10;

type HandDetector = {
  detectForVideo(v: HTMLCanvasElement, t: number): { landmarks: { x: number; y: number }[][] };
  close(): void;
};
type ObjectDetectorInstance = {
  detectForVideo(v: HTMLCanvasElement, t: number): {
    detections: { boundingBox: { originX: number; originY: number; width: number; height: number }; categories: { categoryName: string; score: number }[] }[];
  };
  close(): void;
};

export interface Tracker {
  readonly name: string;
  readonly ready: boolean;
  analyze(video: HTMLVideoElement): Promise<FrameDesc | null>;
  close(): void;
}

export class NullTracker implements Tracker {
  readonly name = "unavailable";
  readonly ready = false;
  constructor(public readonly reason: string) {}
  analyze(): Promise<FrameDesc | null> {
    return Promise.resolve(null);
  }
  close(): void {}
}

class WorkerTracker implements Tracker {
  readonly name = "mediapipe-worker";
  readonly ready = true;
  private pending: { resolve: (value: FrameDesc | null) => void; reject: (reason: Error) => void } | null = null;
  private closed = false;
  private failure: Error | null = null;
  constructor(private worker: Worker) {
    worker.onmessage = (event: MessageEvent) => {
      const message = event.data;
      if (message.kind === "result") this.pending?.resolve(message.result as FrameDesc);
      if (message.kind === "error") {
        this.failure = new Error(String(message.message));
        this.pending?.reject(this.failure);
      }
      if (message.kind === "result" || message.kind === "error") this.pending = null;
    };
    worker.onerror = (event) => {
      this.failure = new Error(event.message || "tracker worker stopped");
      this.pending?.reject(this.failure);
      this.pending = null;
    };
  }
  async analyze(video: HTMLVideoElement): Promise<FrameDesc | null> {
    if (this.failure) throw this.failure;
    if (this.closed || this.pending || !video.videoWidth) return null;
    const bitmap = await createImageBitmap(video);
    if (this.closed) { bitmap.close(); return null; }
    if (this.failure) { bitmap.close(); throw this.failure; }
    return new Promise<FrameDesc | null>((resolve, reject) => {
      this.pending = { resolve, reject };
      this.worker.postMessage({ kind: "frame", bitmap, atMs: performance.now() }, [bitmap]);
    });
  }
  close(): void {
    this.closed = true;
    this.pending?.resolve(null);
    this.pending = null;
    this.worker.terminate();
  }
}

async function createWorkerTracker(status: (s: string) => void): Promise<Tracker> {
  const worker = new Worker(new URL("./tracker.worker.ts", import.meta.url), { type: "classic" });
  try {
    const ready = await new Promise<{ hand: boolean; objects: boolean }>((resolve, reject) => {
      const timer = window.setTimeout(() => reject(new Error("model initialization timed out after 60s")), 60000);
      worker.onmessage = (event: MessageEvent) => {
        if (event.data.kind === "ready") { window.clearTimeout(timer); resolve(event.data); }
        if (event.data.kind === "error") { window.clearTimeout(timer); reject(new Error(String(event.data.message))); }
      };
      worker.onerror = (event) => { window.clearTimeout(timer); reject(new Error(event.message)); };
      worker.postMessage({ kind: "init" });
    });
    status(`on-device tracking live: ${ready.hand ? "hands" : "no hands"} + ${ready.objects ? "objects" : "no objects"}`);
    return new WorkerTracker(worker);
  } catch (e) {
    worker.terminate();
    const reason = `tracker worker failed: ${String(e)}`;
    status(reason);
    return new NullTracker(reason);
  }
}

class MediaPipeTracker implements Tracker {
  readonly name = "mediapipe-ondevice";
  readonly ready = true;
  private canvas: HTMLCanvasElement;
  private hand: HandDetector | null;
  private objects: ObjectDetectorInstance | null;
  private lastObjects: FrameDesc["objects"] = [];
  private lastObjectAt = 0;
  constructor(hand: HandDetector | null, objects: ObjectDetectorInstance | null, vw: number, vh: number) {
    this.hand = hand;
    this.objects = objects;
    this.canvas = document.createElement("canvas");
    this.canvas.width = FRAME_W;
    this.canvas.height = Math.max(1, Math.round((FRAME_W * vh) / Math.max(1, vw)));
  }

  private handBox(lm: { x: number; y: number }[]): Box {
    let x0 = 1;
    let y0 = 1;
    let x1 = 0;
    let y1 = 0;
    for (const p of lm) {
      x0 = Math.min(x0, p.x);
      y0 = Math.min(y0, p.y);
      x1 = Math.max(x1, p.x);
      y1 = Math.max(y1, p.y);
    }
    return { x: x0, y: y0, w: Math.max(0, x1 - x0), h: Math.max(0, y1 - y0) };
  }

  private prevTiny: number[] | null = null;

  private hashAndMotion(): { hash: string; motion: number } {
    const ctx = this.canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return { hash: "", motion: 0 };
    const w = 8;
    const h = 8;
    const tiny = document.createElement("canvas");
    tiny.width = w;
    tiny.height = h;
    tiny.getContext("2d")?.drawImage(this.canvas, 0, 0, w, h);
    const px = tiny.getContext("2d")?.getImageData(0, 0, w, h).data;
    if (!px) return { hash: "", motion: 0 };
    let bits = "";
    let total = 0;
    const vals: number[] = [];
    for (let i = 0; i < px.length; i += 4) {
      const g = (px[i] + px[i + 1] + px[i + 2]) / 3;
      vals.push(g);
      total += g;
    }
    const avg = total / vals.length;
    for (const v of vals) bits += v >= avg ? "1" : "0";
    let motion = 0;
    if (this.prevTiny && this.prevTiny.length === vals.length) {
      let diff = 0;
      for (let i = 0; i < vals.length; i++) diff += Math.abs(vals[i] - this.prevTiny[i]);
      motion = diff / vals.length / 255;
    }
    this.prevTiny = vals;
    return { hash: bits, motion };
  }

  async analyze(video: HTMLVideoElement): Promise<FrameDesc | null> {
    if (!video.videoWidth) return null;
    const ctx = this.canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return null;
    ctx.drawImage(video, 0, 0, this.canvas.width, this.canvas.height);
    const now = performance.now();
    let hands: Box[] = [];
    let handPoints: { x: number; y: number }[][] = [];
    let objects: FrameDesc["objects"] = this.lastObjects;
    if (this.hand) {
      try {
        const hr = this.hand.detectForVideo(this.canvas, now);
        const all = hr.landmarks ?? [];
        hands = all.map((lm) => this.handBox(lm));
        handPoints = all.map((lm) => lm.map((p) => ({ x: p.x, y: p.y })));
      } catch (e) {
        throw new Error(`hand detector failed: ${e instanceof Error ? e.message : "unknown error"}`);
      }
    }
    if (this.objects && now - this.lastObjectAt >= 1000) {
      try {
      const or = this.objects.detectForVideo(this.canvas, now);
      const W = this.canvas.width;
      const H = this.canvas.height;
      objects = (or.detections ?? [])
        .map((d) => ({
          label: d.categories?.[0]?.categoryName ?? "object",
          score: d.categories?.[0]?.score ?? 0,
          box: {
            x: d.boundingBox.originX / W,
            y: d.boundingBox.originY / H,
            w: d.boundingBox.width / W,
            h: d.boundingBox.height / H,
          },
        }))
        .filter((o) => o.score >= MIN_SCORE)
        .slice(0, MAX_RESULTS);
      this.lastObjects = objects;
      this.lastObjectAt = now;
      } catch (e) {
        throw new Error(`object detector failed: ${e instanceof Error ? e.message : "unknown error"}`);
      }
    }
    const { hash, motion } = this.hashAndMotion();
    return { hands, handPoints, objects, sceneHash: hash, motion, atMs: now };
  }

  close(): void {
    try {
      this.hand?.close();
      this.objects?.close();
    } catch {
      /* already closed */
    }
  }
}

export async function createTracker(
  video: HTMLVideoElement,
  status: (s: string) => void,
): Promise<Tracker> {
  status("checking local vision models…");
  const assets = [
    `${WASM_URL}/vision_wasm_internal.wasm`,
    "/vision/vision_bundle_classic.js",
    HAND_MODEL_URL,
    OBJECT_MODEL_URL,
  ];
  try {
    const checks = await Promise.all(assets.map((url) => fetch(url, { method: "HEAD" })));
    if (checks.some((res) => !res.ok || (res.headers.get("content-type") ?? "").includes("text/html"))) {
      throw new Error("local vision asset missing");
    }
  } catch {
    const reason = "vision assets unavailable; run python scripts/setup_vision_assets.py on this PC";
    status(reason);
    return new NullTracker(reason);
  }
  status("loading local vision models…");
  if (typeof Worker !== "undefined" && typeof OffscreenCanvas !== "undefined" && typeof createImageBitmap !== "undefined") {
    return createWorkerTracker(status);
  }
  let lib: typeof import("@mediapipe/tasks-vision");
  try {
    lib = await import("@mediapipe/tasks-vision");
  } catch {
    const reason = "tracker library not installed (run npm install on a dev machine)";
    status(reason);
    return new NullTracker(reason);
  }
  let timedOut = false;
  let timeoutId = 0;
  const timeout = new Promise<never>((_, reject) => {
    timeoutId = window.setTimeout(() => { timedOut = true; reject(new Error("model initialization timed out after 60s")); }, 60000);
  });
  const loadAll = (async () => {
    const fileset = await lib.FilesetResolver.forVisionTasks(WASM_URL);
    const vw = video.videoWidth || 640;
    const vh = video.videoHeight || 480;
    // Phones often reject the GPU delegate: try it, then fall back to CPU
    // so tracking still runs (slower) instead of dying silently.
    const delegates = ["GPU", "CPU"] as const;
    let hand: HandDetector | null = null;
    let objects: ObjectDetectorInstance | null = null;
    let handError: unknown = null;
    let objectError: unknown = null;
    for (const delegate of delegates) {
      try {
        hand = await lib.HandLandmarker.createFromOptions(fileset, {
          baseOptions: { modelAssetPath: HAND_MODEL_URL, delegate },
          numHands: 2,
          runningMode: "VIDEO",
        }) as HandDetector;
        break;
      } catch (e) { handError = e; }
    }
    for (const delegate of delegates) {
      try {
        objects = await lib.ObjectDetector.createFromOptions(fileset, {
          baseOptions: { modelAssetPath: OBJECT_MODEL_URL, delegate },
          maxResults: MAX_RESULTS,
          scoreThreshold: MIN_SCORE,
          runningMode: "VIDEO",
        }) as ObjectDetectorInstance;
        break;
      } catch (e) { objectError = e; }
    }
    if (timedOut) { hand?.close(); objects?.close(); throw new Error("model initialization exceeded 60s"); }
    if (!hand && !objects) {
      throw new Error(`hands: ${String(handError)}; objects: ${String(objectError)}`);
    }
    return { hand, objects, vw, vh };
  })();
  try {
    const { hand, objects, vw, vh } = await Promise.race([loadAll, timeout]);
    status(`on-device tracking live: ${hand ? "hands" : "no hands"} + ${objects ? "objects" : "no objects"}`);
    return new MediaPipeTracker(hand, objects, vw, vh);
  } catch (e) {
    const detail = e instanceof Error ? e.message : typeof e === "string" ? e : "model asset request failed";
    const reason = `tracker models failed to load: ${detail}`;
    status(reason);
    return new NullTracker(reason);
  } finally {
    window.clearTimeout(timeoutId);
  }
}
