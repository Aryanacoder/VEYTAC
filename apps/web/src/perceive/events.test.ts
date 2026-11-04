/* Pure track-event tests (node --test, no browser, no models). */

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { deriveEvents, heldLabels, type FrameDesc } from "./events.js";

const at = (over: Partial<FrameDesc>): FrameDesc => ({
  hands: [],
  handPoints: [],
  objects: [],
  sceneHash: "a",
  motion: 0,
  atMs: 0,
  ...over,
});

describe("deriveEvents", () => {
  it("first frame reports hands and held objects", () => {
    const curr = at({
      hands: [{ x: 0.4, y: 0.4, w: 0.2, h: 0.2 }],
      objects: [{ label: "cup", score: 0.9, box: { x: 0.45, y: 0.45, w: 0.1, h: 0.1 } }],
    });
    const ev = deriveEvents(null, curr);
    assert.ok(ev.some((e) => e.type === "hands_changed"));
    assert.ok(ev.some((e) => e.type === "held_object_new" && e.label === "cup"));
  });

  it("steady scene emits nothing (no paid call)", () => {
    const f = at({ sceneHash: "same" });
    assert.deepEqual(deriveEvents(f, at({ sceneHash: "same" })), []);
  });

  it("new held object fires once, put-down fires gone", () => {
    const hand = { x: 0.4, y: 0.4, w: 0.2, h: 0.2 };
    const empty = at({ hands: [hand], sceneHash: "s" });
    const holding = at({
      hands: [hand],
      objects: [{ label: "Cup", score: 0.9, box: { x: 0.45, y: 0.45, w: 0.1, h: 0.1 } }],
      sceneHash: "s",
    });
    const got = deriveEvents(empty, holding);
    assert.ok(got.some((e) => e.type === "held_object_new" && e.label === "cup"));
    const gone = deriveEvents(holding, empty);
    assert.ok(gone.some((e) => e.type === "held_object_gone" && e.label === "cup"));
  });

  it("unheld new object fires object_new, scene change alone fires scene_changed", () => {
    const base = at({ sceneHash: "s1" });
    const withObj = at({
      objects: [{ label: "laptop", score: 0.8, box: { x: 0.0, y: 0.0, w: 0.2, h: 0.2 } }],
      sceneHash: "s1",
    });
    assert.ok(deriveEvents(base, withObj).some((e) => e.type === "object_new"));
    assert.ok(
      deriveEvents(at({ sceneHash: "s1" }), at({ sceneHash: "s2" })).some(
        (e) => e.type === "scene_changed",
      ),
    );
  });

  it("motion burst fires on rising edge only", () => {
    const still = at({ motion: 0.01 });
    const moving = at({ motion: 0.2 });
    assert.ok(deriveEvents(still, moving).some((e) => e.type === "motion_burst"));
    assert.ok(!deriveEvents(moving, at({ motion: 0.3 })).some((e) => e.type === "motion_burst"));
    assert.ok(!deriveEvents(moving, at({ motion: 0.01 })).some((e) => e.type === "motion_burst"));
  });

  it("heldLabels lowercases and dedupes", () => {
    const d = at({
      hands: [{ x: 0, y: 0, w: 1, h: 1 }],
      objects: [
        { label: "Cup", score: 0.9, box: { x: 0.4, y: 0.4, w: 0.1, h: 0.1 } },
        { label: "cup", score: 0.8, box: { x: 0.5, y: 0.5, w: 0.1, h: 0.1 } },
      ],
    });
    assert.deepEqual(heldLabels(d), ["cup"]);
  });
});
