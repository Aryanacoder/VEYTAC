/* Headless UI smoke: renders the live view in jsdom.
   No sockets, no server, no camera. jsdom has no mediaDevices, so the
   guidance notice must render instead of a crash, with the live controls
   present and the consent gate closed. */
import { JSDOM } from "jsdom";

const dom = new JSDOM("<!doctype html><html><body><div id='root'></div></body></html>", {
  url: "http://localhost/",
  pretendToBeVisual: true,
});

for (const key of ["window", "document", "HTMLElement", "Node", "Event"]) {
  globalThis[key] = dom.window[key];
}
try {
  Object.defineProperty(globalThis, "navigator", { value: dom.window.navigator });
} catch {
  /* navigator is enough as-is */
}
globalThis.requestAnimationFrame = (cb) => setTimeout(cb, 0);
globalThis.cancelAnimationFrame = (id) => clearTimeout(id);

await import("../static-build/main.js");
// Wait for the async support-check effect: buttons mount immediately but
// the no-camera notice only appears after the effect pass. Poll for the
// notice itself (jsdom never has mediaDevices, so it must always appear).
const doc0 = dom.window.document;
for (let i = 0; i < 150 && !doc0.querySelector(".live-notice"); i++) {
  await new Promise((r) => setTimeout(r, 100));
}

const doc = dom.window.document;
const assert = (cond, msg) => {
  if (!cond) {
    console.error(`SMOKE FAIL: ${msg}`);
    console.error(`DOM state: notice=${!!doc.querySelector(".live-notice")} buttons=${doc.querySelectorAll(".glass-button").length} root=${doc.querySelector("#root")?.innerHTML.length ?? -1} chars`);
    process.exit(1);
  }
};

assert(doc.querySelector('img.brand-logo[alt="VEYTAC"]'), "brand logo renders");
assert(
  doc.querySelector(".live-notice")?.textContent?.length > 0,
  "no-camera guidance renders instead of crashing",
);
const buttons = [...doc.querySelectorAll(".glass-button")].map((b) => b.textContent);
assert(buttons.includes("Start"), "Start control present");
assert(buttons.includes("Stop"), "Stop control present");
assert(buttons.includes("Rear"), "Rear/front camera flip present");
assert(
  buttons.includes("Mute") || buttons.includes("Unmute"),
  "Mute control present",
);
assert(doc.querySelector(".standby"), "standby panel renders pre-capture");
assert(!doc.querySelector(".consent-panel"), "consent gate closed on load");
assert(doc.querySelector("canvas.detect-overlay"), "detection overlay canvas present");

console.log("SMOKE PASS: logo, guidance, Start/Stop/Mute/Rear, standby, overlay canvas");
