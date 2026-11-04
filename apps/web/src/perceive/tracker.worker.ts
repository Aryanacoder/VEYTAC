import type { HandLandmarker as HandLandmarkerInstance, ObjectDetector as ObjectDetectorInstance } from "@mediapipe/tasks-vision";
import type { Box, FrameDesc } from "./events";

// MediaPipe's WASM loader calls importScripts(), which requires a classic worker.
const workerGlobal = self as unknown as { exports: typeof import("@mediapipe/tasks-vision"); importScripts: (url: string) => void };
workerGlobal.exports = {} as typeof import("@mediapipe/tasks-vision");
workerGlobal.importScripts("/vision/vision_bundle_classic.js");
const { FilesetResolver, HandLandmarker, ObjectDetector } = workerGlobal.exports;

const WIDTH = 320;
const wasm = "/vision/wasm";
let hand: HandLandmarkerInstance | null = null;
let objects: ObjectDetectorInstance | null = null;
let lastObjects: FrameDesc["objects"] = [];
let lastObjectAt = 0;
let previous: number[] | null = null;
const canvas = new OffscreenCanvas(WIDTH, 240);
const tiny = new OffscreenCanvas(8, 8);

function handBox(points: Array<{ x: number; y: number }>): Box {
  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);
  const x = Math.min(...xs);
  const y = Math.min(...ys);
  return { x, y, w: Math.max(0, Math.max(...xs) - x), h: Math.max(0, Math.max(...ys) - y) };
}

function hashAndMotion(): { hash: string; motion: number } {
  const ctx = tiny.getContext("2d", { willReadFrequently: true });
  if (!ctx) return { hash: "", motion: 0 };
  ctx.drawImage(canvas, 0, 0, 8, 8);
  const pixels = ctx.getImageData(0, 0, 8, 8).data;
  const values: number[] = [];
  for (let i = 0; i < pixels.length; i += 4) values.push((pixels[i] + pixels[i + 1] + pixels[i + 2]) / 3);
  const average = values.reduce((a, b) => a + b, 0) / values.length;
  const hash = values.map((value) => value >= average ? "1" : "0").join("");
  const motion = previous ? values.reduce((sum, value, i) => sum + Math.abs(value - previous![i]), 0) / values.length / 255 : 0;
  previous = values;
  return { hash, motion };
}

async function init() {
  try {
    const fileset = await FilesetResolver.forVisionTasks(wasm);
    let handError = "";
    let objectError = "";
    try {
      hand = await HandLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: "/vision/hand_landmarker.task", delegate: "CPU" },
        numHands: 2, runningMode: "VIDEO",
      });
    } catch (e) { handError = String(e); }
    try {
      objects = await ObjectDetector.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: "/vision/efficientdet_lite0.tflite", delegate: "CPU" },
        maxResults: 10, scoreThreshold: 0.25, runningMode: "VIDEO",
      });
    } catch (e) { objectError = String(e); }
    if (!hand && !objects) throw new Error(`hands: ${handError}; objects: ${objectError}`);
    self.postMessage({ kind: "ready", hand: !!hand, objects: !!objects });
  } catch (e) { self.postMessage({ kind: "error", message: String(e) }); }
}

function analyze(bitmap: ImageBitmap, atMs: number) {
  try {
    canvas.height = Math.max(1, Math.round(WIDTH * bitmap.height / bitmap.width));
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) throw new Error("offscreen canvas unavailable");
    ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    const landmarks = hand?.detectForVideo(canvas as unknown as HTMLCanvasElement, atMs).landmarks ?? [];
    const hands = landmarks.map(handBox);
    const handPoints = landmarks.map((points) => points.map((p) => ({ x: p.x, y: p.y })));
    let detected = lastObjects;
    if (objects && atMs - lastObjectAt >= 1000) {
      detected = objects.detectForVideo(canvas as unknown as HTMLCanvasElement, atMs).detections.map((d) => ({
        label: d.categories[0]?.categoryName ?? "object",
        score: d.categories[0]?.score ?? 0,
        box: { x: (d.boundingBox?.originX ?? 0) / canvas.width,
          y: (d.boundingBox?.originY ?? 0) / canvas.height,
          w: (d.boundingBox?.width ?? 0) / canvas.width,
          h: (d.boundingBox?.height ?? 0) / canvas.height },
      })).filter((item) => item.score >= 0.25);
      lastObjects = detected;
      lastObjectAt = atMs;
    }
    const { hash, motion } = hashAndMotion();
    const result: FrameDesc = { hands, handPoints, objects: detected, sceneHash: hash, motion, atMs };
    self.postMessage({ kind: "result", result });
  } catch (e) { self.postMessage({ kind: "error", message: String(e) }); }
  finally { bitmap.close(); }
}

self.onmessage = (event: MessageEvent) => {
  const message = event.data;
  if (message.kind === "init") void init();
  else if (message.kind === "frame") analyze(message.bitmap as ImageBitmap, message.atMs as number);
};
