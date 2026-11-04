/* Chromium verification without any listening socket: every request is
   fulfilled from disk (route interception). Screenshots to output/. */
import { readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const ROOT = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const BUILD = path.join(ROOT, "static-build");
const OUT = path.join(ROOT, "..", "..", "output", "playwright");

const MIME = {
  ".html": "text/html",
  ".js": "text/javascript",
  ".mjs": "text/javascript",
  ".css": "text/css",
  ".svg": "image/svg+xml",
};

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });

await page.route("**/*", async (route) => {
  const url = new URL(route.request().url());
  if (!url.hostname.endsWith("app.local")) return route.continue();
  let file = url.pathname === "/" ? "index.html" : url.pathname.slice(1);
  const disk = path.join(BUILD, file);
  if (!existsSync(disk) || disk.includes("..")) {
    return route.fulfill({ status: 404, body: "missing" });
  }
  const ext = path.extname(disk);
  return route.fulfill({
    contentType: MIME[ext] ?? "application/octet-stream",
    body: await readFile(disk),
  });
});

const errors = [];
page.on("response", (r) => {
  // /api/* has no backend in this offline smoke by design — not a failure.
  if (r.status() >= 400 && !r.url().includes("/api/")) {
    errors.push(`HTTP ${r.status()}: ${r.url()}`);
  }
});
page.on("pageerror", (e) => errors.push(String(e).slice(0, 300)));
page.on("console", (m) => {
  // /api/* has no backend in this offline smoke by design; bare resource
  // errors duplicate the response handler (which logs URLs) — skip both.
  if (
    (m.type() === "error" || m.type() === "warning") &&
    !m.text().includes("/api/") &&
    !m.text().startsWith("Failed to load resource")
  ) {
    errors.push(`${m.type()}: ${m.text().slice(0, 300)}`);
  }
});

await page.goto("http://app.local/", { waitUntil: "networkidle", timeout: 45000 });
try {
  await page.waitForSelector(".brand-logo", { timeout: 20000 });
} catch {
  console.error("NO BRAND. Early errors:", JSON.stringify(errors.slice(0, 6), null, 1));
  console.error("ROOT:", (await page.locator("#root").innerHTML().catch(() => "(none)")).slice(0, 200));
  await browser.close();
  process.exit(1);
}

const checks = {
  brand: await page.locator(".brand-logo").getAttribute("alt"),
  notice: await page.locator(".live-notice").innerText().catch(() => "(none)"),
  startBtn: await page.getByRole("button", { name: "Start" }).innerText(),
};
console.log(JSON.stringify(checks));

await page.screenshot({ path: path.join(OUT, "live.png") });
await page.setViewportSize({ width: 390, height: 844 });
await page.screenshot({ path: path.join(OUT, "live-mobile.png"), fullPage: true });
const mobileOverflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
if (mobileOverflow) errors.push("mobile layout overflows horizontally");

await browser.close();
if (errors.length > 0) {
  console.error("PAGE ERRORS:", errors);
  process.exit(1);
}
console.log("CHROMIUM PASS: single live screen renders, screenshots saved");
