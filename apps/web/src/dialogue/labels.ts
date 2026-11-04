import type { Track } from "../perceive/overlay";

/** Extract an arbitrary expert-given noun phrase, not a fixed object class. */
export function spokenObjectLabel(utterance: string, language: string): string | null {
  const text = utterance.trim().replace(/[.!?。！？]+$/u, "").trim();
  let value: string | null = null;
  if (language === "ja") {
    value = text.match(/^(?:これ|こちら|この物|それ)(?:は|が)(.+?)(?:です|だ|になります)?$/u)?.[1] ?? null;
  } else if (language === "zh") {
    value = text.match(/^(?:这|这个|这是|那是|那个是)(?:是)?(.+)$/u)?.[1] ?? null;
  } else {
    value = text.match(/^(?:(?:this|that) is called|(?:this|that|it) is|i(?: am|'m) holding|the object is)\s+(?:an?\s+)?(.+)$/i)?.[1] ?? null;
  }
  if (!value) return null;
  value = value.replace(/^(?:an?\s+|一个|一個)/iu, "").replace(/(?:です|だ)$/u, "").trim();
  if (!value || value.length > 80 || value.split(/\s+/u).length > 8) return null;
  return value;
}

/** Candidate only: a nearby detector box is not proof of the spoken identity. */
export function candidateNearHand(tracks: Track[]): Track | null {
  const hands = tracks.filter((track) => track.kind === "human" && track.label === "hand");
  const objects = tracks.filter((track) => track.kind === "object");
  if (!hands.length || !objects.length) return null;
  let best: { track: Track; distance: number } | null = null;
  for (const object of objects) {
    const ox = object.box.x + object.box.w / 2;
    const oy = object.box.y + object.box.h / 2;
    const distance = Math.min(...hands.map((hand) => {
      const hx = hand.box.x + hand.box.w / 2;
      const hy = hand.box.y + hand.box.h / 2;
      return Math.hypot(ox - hx, oy - hy);
    }));
    if (distance < 0.22 && (!best || distance < best.distance)) best = { track: object, distance };
  }
  return best?.track ?? null;
}
