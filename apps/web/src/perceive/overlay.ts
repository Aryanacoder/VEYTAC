/* Live detection overlay: pure track logic + canvas drawing.
   Colors are the owner's spec: humans and hands in blue, all other
   objects in red, with fading motion trails. Trails are suppressed when
   the user prefers reduced motion. Drawing stays in this module so the
   React component only owns a canvas element. */

import type { Box, FrameDesc } from "./events.js";

export const HUMAN_BLUE = "#79b6ff";
export const OBJECT_RED = "#ff7687";

export type TrackKind = "human" | "object";

export interface TrailPoint {
  x: number;
  y: number;
  atMs: number;
}

export interface Track {
  key: string;
  kind: TrackKind;
  label: string;
  box: Box;
  trail: TrailPoint[];
  updatedMs: number;
}

export function colorFor(kind: TrackKind): string {
  return kind === "human" ? HUMAN_BLUE : OBJECT_RED;
}

export function containProjection(canvasW: number, canvasH: number, srcW: number, srcH: number) {
  const scale = Math.min(canvasW / srcW, canvasH / srcH);
  const width = srcW * scale;
  const height = srcH * scale;
  return { width, height, x: (canvasW - width) / 2, y: (canvasH - height) / 2 };
}

/** A SAM-refined detection: precise box in source pixels + stable id. */
export interface SamBox {
  id: number;
  label: string;
  kind: TrackKind;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  frameW: number;
  frameH: number;
  confidence?: number;
  maskSvg?: string | null;
  maskW?: number;
  maskH?: number;
}

/** Normalize a SAM pixel box to 0..1 in frame space. */
export function samBoxNormalized(b: SamBox): Box {
  return {
    x: b.x1 / b.frameW,
    y: b.y1 / b.frameH,
    w: Math.max(0, (b.x2 - b.x1) / b.frameW),
    h: Math.max(0, (b.y2 - b.y1) / b.frameH),
  };
}

/** Draw SAM boxes: thicker frame + id badge so refined tracks read
 *  distinctly from the live on-device boxes. Same contain mapping. */
export function drawSamBoxes(
  ctx: CanvasRenderingContext2D,
  canvasW: number,
  canvasH: number,
  boxes: SamBox[],
  src: { w: number; h: number },
): void {
  const projected = containProjection(canvasW, canvasH, src.w, src.h);
  const sx = projected.width;
  const sy = projected.height;
  const ox = projected.x;
  const oy = projected.y;
  ctx.lineWidth = 3;
  ctx.font = "12px system-ui, sans-serif";
  for (const b of boxes) {
    const n = samBoxNormalized(b);
    const color = colorFor(b.kind);
    const x = ox + n.x * sx;
    const y = oy + n.y * sy;
    const w = n.w * sx;
    const h = n.h * sy;
    const pathText = b.maskSvg;
    let paintedMask = false;
    if (pathText && pathText.length < 120_000 && /^[MLZmlz0-9eE+.,\s-]+$/.test(pathText) &&
        b.maskW && b.maskH && typeof Path2D !== "undefined") {
      try {
        ctx.save();
        ctx.translate(x, y);
        ctx.scale(w / b.maskW, h / b.maskH);
        const path = new Path2D(pathText);
        ctx.fillStyle = b.kind === "human" ? "rgba(76, 181, 255, 0.32)" : "rgba(255, 89, 115, 0.32)";
        ctx.strokeStyle = color;
        ctx.lineWidth = Math.max(1, b.maskW / Math.max(w, 1));
        ctx.fill(path);
        ctx.stroke(path);
        ctx.restore();
        paintedMask = true;
      } catch { ctx.restore(); }
    }
    if (!paintedMask) {
      ctx.strokeStyle = color;
      ctx.strokeRect(x, y, Math.max(2, w), Math.max(2, h));
    }
    const tag = `#${b.id} ${b.label}`;
    const tw = ctx.measureText(tag).width;
    ctx.fillStyle = color;
    ctx.fillRect(x, Math.max(0, y - 18), tw + 12, 18);
    ctx.fillStyle = "#fff";
    ctx.fillText(tag, x + 6, Math.max(0, y - 18) + 13);
  }
  ctx.globalAlpha = 1;
}

function centroid(box: Box): { x: number; y: number } {
  return { x: box.x + box.w / 2, y: box.y + box.h / 2 };
}

function keyFor(kind: TrackKind, label: string, index: number): string {
  return `${kind}:${label}:${index}`;
}

/** Fold one analyzed frame into tracks: match by kind+label+index, push
 *  the centroid onto the trail, drop tracks older than maxAgeMs. */
export function updateTracks(
  prev: Track[],
  desc: FrameDesc,
  nowMs: number,
  maxAgeMs = 2500,
): Track[] {
  const next: Track[] = [];
  const seen = new Set<string>();
  const push = (key: string, kind: TrackKind, label: string, box: Box) => {
    seen.add(key);
    const old = prev.find((t) => t.key === key);
    const c = centroid(box);
    const trail = [...(old?.trail ?? []), { x: c.x, y: c.y, atMs: nowMs }].slice(-12);
    next.push({ key, kind, label, box, trail, updatedMs: nowMs });
  };
  desc.hands.forEach((box: Box, i: number) => push(keyFor("human", "hand", i), "human", "hand", box));
  const perLabel = new Map<string, number>();
  for (const o of desc.objects) {
    const label = o.label.toLowerCase();
    const kind: TrackKind = label === "person" ? "human" : "object";
    const n = perLabel.get(label) ?? 0;
    perLabel.set(label, n + 1);
    push(keyFor(kind, label, n), kind, label, o.box);
  }
  for (const t of prev) {
    if (!seen.has(t.key) && nowMs - t.updatedMs < maxAgeMs) next.push(t);
  }
  return next;
}

/** Draw tracks onto a canvas sized to the displayed video element.
 *  Pass the raw frame size (srcW/srcH) so boxes map through the same
 *  letterboxing the video element applies with object-fit: contain. */
export function drawOverlay(
  ctx: CanvasRenderingContext2D,
  canvasW: number,
  canvasH: number,
  tracks: Track[],
  opts: {
    showTrails?: boolean;
    reducedMotion?: boolean;
    srcW?: number;
    srcH?: number;
    /** Current-frame hand skeletons: 21 normalized dots per hand. */
    dots?: { x: number; y: number }[][];
  } = {},
): void {
  const showTrails = opts.showTrails ?? true;
  const trails = showTrails && !opts.reducedMotion;
  let sx = canvasW;
  let sy = canvasH;
  let ox = 0;
  let oy = 0;
  if (opts.srcW && opts.srcH) {
    const projected = containProjection(canvasW, canvasH, opts.srcW, opts.srcH);
    sx = projected.width;
    sy = projected.height;
    ox = projected.x;
    oy = projected.y;
  }
  const px = (nx: number) => ox + nx * sx;
  const py = (ny: number) => oy + ny * sy;
  ctx.clearRect(0, 0, canvasW, canvasH);
  ctx.lineWidth = 2;
  ctx.font = "12px system-ui, sans-serif";
  for (const t of tracks) {
    const color = colorFor(t.kind);
    const x = px(t.box.x);
    const y = py(t.box.y);
    const w = t.box.w * sx;
    const h = t.box.h * sy;
    if (trails && t.trail.length > 1) {
      for (let i = 1; i < t.trail.length; i++) {
        const a = i / t.trail.length;
        ctx.strokeStyle = color;
        ctx.globalAlpha = 0.15 + a * 0.5;
        ctx.beginPath();
        ctx.moveTo(px(t.trail[i - 1].x), py(t.trail[i - 1].y));
        ctx.lineTo(px(t.trail[i].x), py(t.trail[i].y));
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
    }
    ctx.strokeStyle = color;
    ctx.strokeRect(x, y, w, h);
    const tag = t.label;
    const tw = ctx.measureText(tag).width;
    ctx.fillStyle = color;
    ctx.fillRect(x, Math.max(0, y - 16), tw + 10, 16);
    ctx.fillStyle = "#fff";
    ctx.fillText(tag, x + 5, Math.max(0, y - 16) + 12);
  }
  // Hand anatomy as dots (no connecting lines): the model reads movement
  // from dot displacement across frames, which also feeds robot data.
  if (opts.dots) {
    ctx.fillStyle = HUMAN_BLUE;
    for (const hand of opts.dots) {
      hand.forEach((p, i) => {
        ctx.globalAlpha = i % 4 === 0 ? 1 : 0.75; // fingertips + wrist pop
        ctx.beginPath();
        ctx.arc(px(p.x), py(p.y), i % 4 === 0 ? 3.5 : 2.5, 0, Math.PI * 2);
        ctx.fill();
      });
    }
    ctx.globalAlpha = 1;
  }
  ctx.globalAlpha = 1;
}
