/* Overlay track tests (node --test, no DOM canvas needed for logic). */

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { colorFor, containProjection, drawSamBoxes, samBoxNormalized, updateTracks } from "./overlay.js";
import type { FrameDesc } from "./events.js";

const desc = (over: Partial<FrameDesc>): FrameDesc => ({
  hands: [],
  handPoints: [],
  objects: [],
  sceneHash: "a",
  motion: 0,
  atMs: 0,
  ...over,
});

describe("overlay tracks", () => {
  it("fits a landscape camera fully in a portrait phone without cropping", () => {
    const rect = containProjection(390, 844, 1280, 720);
    assert.equal(rect.width, 390);
    assert.equal(rect.height, 219.375);
    assert.equal(rect.x, 0);
    assert.equal(rect.y, (844 - 219.375) / 2);
  });
  it("colors humans blue and objects red", () => {
    assert.equal(colorFor("human"), "#79b6ff");
    assert.equal(colorFor("object"), "#ff7687");
  });

  it("persons are human tracks, cups are object tracks", () => {
    const tracks = updateTracks(
      [],
      desc({
        hands: [{ x: 0.1, y: 0.1, w: 0.1, h: 0.1 }],
        objects: [
          { label: "person", score: 0.9, box: { x: 0.5, y: 0.2, w: 0.2, h: 0.5 } },
          { label: "cup", score: 0.9, box: { x: 0.15, y: 0.15, w: 0.05, h: 0.05 } },
        ],
      }),
      1000,
    );
    const kinds = new Map(tracks.map((t) => [t.label, t.kind]));
    assert.equal(kinds.get("hand"), "human");
    assert.equal(kinds.get("person"), "human");
    assert.equal(kinds.get("cup"), "object");
  });

  it("trails grow on repeat sightings and stale tracks expire", () => {
    const box = { x: 0.1, y: 0.1, w: 0.1, h: 0.1 };
    const t1 = updateTracks([], desc({ hands: [box] }), 1000);
    assert.equal(t1[0].trail.length, 1);
    const moved = { ...box, x: 0.2 };
    const t2 = updateTracks(t1, desc({ hands: [moved] }), 1500);
    assert.equal(t2.length, 1);
    assert.equal(t2[0].trail.length, 2);
    const t3 = updateTracks(t2, desc({}), 6000);
    assert.equal(t3.length, 0);
  });

  it("normalizes SAM pixel boxes to frame space", () => {
    const n = samBoxNormalized({
      id: 2, label: "cup", kind: "object",
      x1: 32, y1: 24, x2: 96, y2: 72, frameW: 320, frameH: 240,
    });
    assert.equal(n.x, 0.1);
    assert.equal(n.y, 0.1);
    assert.equal(n.w, 0.2);
    assert.equal(n.h, 0.2);
  });

  it("fills decoded SAM mask geometry and falls back to a box without it", () => {
    const calls: string[] = [];
    const previous = (globalThis as unknown as { Path2D?: unknown }).Path2D;
    (globalThis as unknown as { Path2D: unknown }).Path2D = class {
      constructor(_path: string) { calls.push("path"); }
    };
    const ctx = {
      save: () => calls.push("save"), restore: () => calls.push("restore"),
      translate: () => calls.push("translate"), scale: () => calls.push("scale"),
      fill: () => calls.push("fill"), stroke: () => calls.push("stroke"),
      strokeRect: () => calls.push("box"),
      measureText: () => ({ width: 10 }), fillRect: () => {}, fillText: () => {},
    } as unknown as CanvasRenderingContext2D;
    const base = { id: 1, label: "person", kind: "human" as const,
      x1: 10, y1: 10, x2: 30, y2: 30, frameW: 100, frameH: 100 };
    try {
      drawSamBoxes(ctx, 100, 100, [{ ...base, maskSvg: "M0 0L20 0L20 20Z", maskW: 20, maskH: 20 }], { w: 100, h: 100 });
      assert.ok(calls.includes("fill"));
      assert.ok(!calls.includes("box"));
      calls.length = 0;
      drawSamBoxes(ctx, 100, 100, [{ ...base, maskSvg: null }], { w: 100, h: 100 });
      assert.ok(calls.includes("box"));
    } finally {
      (globalThis as unknown as { Path2D?: unknown }).Path2D = previous;
    }
  });

  it("keeps recent but unseen tracks (occlusion grace)", () => {
    const box = { x: 0.1, y: 0.1, w: 0.1, h: 0.1 };
    const t1 = updateTracks([], desc({ hands: [box] }), 1000);
    const t2 = updateTracks(t1, desc({}), 2000);
    assert.equal(t2.length, 1);
    assert.equal(t2[0].trail.length, 1);
  });
});
