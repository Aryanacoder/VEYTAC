/* On-device track events (pure logic, no models, no DOM).
   A FrameDesc is one analyzed snapshot: hand boxes, object labels+boxes,
   and a coarse scene hash. deriveEvents compares consecutive descriptors
   and reports only what changed, so paid model calls fire on change
   events — never on a timer. All boxes are normalized 0..1. */

export interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface DetectedObject {
  label: string;
  score: number;
  box: Box;
}

export interface FrameDesc {
  hands: Box[];
  /** 21 normalized landmarks per detected hand (MediaPipe hand topology). */
  handPoints: { x: number; y: number }[][];
  objects: DetectedObject[];
  sceneHash: string;
  /** Mean frame-to-frame pixel energy, 0 (static) to ~1 (full motion). */
  motion: number;
  atMs: number;
}

export type TrackEventType =
  | "hands_changed"
  | "held_object_new"
  | "held_object_gone"
  | "object_new"
  | "scene_changed"
  | "motion_burst";

export const MOTION_BURST_THRESHOLD = 0.08;

export interface TrackEvent {
  type: TrackEventType;
  label?: string;
  detail: string;
}

function centerIn(b: Box, pad: number): { cx: boolean; cy: boolean; box: Box } {
  return {
    cx: true,
    cy: true,
    box: { x: b.x - pad, y: b.y - pad, w: b.w + pad * 2, h: b.h + pad * 2 },
  };
}

function heldBy(hand: Box, obj: Box): boolean {
  const pad = 0.08;
  const hx = centerIn(hand, pad).box;
  const cx = obj.x + obj.w / 2;
  const cy = obj.y + obj.h / 2;
  return cx >= hx.x && cx <= hx.x + hx.w && cy >= hx.y && cy <= hx.y + hx.h;
}

export function heldLabels(desc: FrameDesc): string[] {
  const out: string[] = [];
  for (const o of desc.objects) {
    if (desc.hands.some((h) => heldBy(h, o.box))) out.push(o.label.toLowerCase());
  }
  return [...new Set(out)].sort();
}

export function deriveEvents(prev: FrameDesc | null, curr: FrameDesc): TrackEvent[] {
  const events: TrackEvent[] = [];
  if (!prev) {
    if (curr.hands.length > 0)
      events.push({ type: "hands_changed", detail: `${curr.hands.length} hand(s) in view` });
    for (const h of heldLabels(curr))
      events.push({ type: "held_object_new", label: h, detail: `holding ${h}` });
    return events;
  }
  if (prev.hands.length !== curr.hands.length) {
    events.push({
      type: "hands_changed",
      detail: `hands ${prev.hands.length} → ${curr.hands.length}`,
    });
  }
  const was = new Set(heldLabels(prev));
  const now = new Set(heldLabels(curr));
  for (const h of now)
    if (!was.has(h))
      events.push({ type: "held_object_new", label: h, detail: `now holding ${h}` });
  for (const h of was)
    if (!now.has(h))
      events.push({ type: "held_object_gone", label: h, detail: `put down ${h}` });
  const seen = new Set(prev.objects.map((o) => o.label.toLowerCase()));
  for (const o of curr.objects) {
    const l = o.label.toLowerCase();
    if (!seen.has(l) && !now.has(l)) {
      events.push({ type: "object_new", label: l, detail: `${l} appeared` });
      seen.add(l);
    }
  }
  if (prev.sceneHash && curr.sceneHash && prev.sceneHash !== curr.sceneHash && events.length === 0) {
    events.push({ type: "scene_changed", detail: "view changed" });
  }
  // Rising edge on motion energy: catches hand waves, carried objects,
  // and body movement even when labels stay the same.
  if (prev.motion < MOTION_BURST_THRESHOLD && curr.motion >= MOTION_BURST_THRESHOLD) {
    events.push({ type: "motion_burst", detail: `motion energy ${curr.motion.toFixed(2)}` });
  }
  return events;
}
