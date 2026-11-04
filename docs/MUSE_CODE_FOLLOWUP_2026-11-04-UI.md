# Muse Code follow-up — VEYTAC live UI (2026-11-04)

The live screen now uses a blue and white glass visual system. The video remains the main surface; observation status, the current question, and Start/Stop/Mute are readable without covering the center of the scene. The SVG VEYTAC mark has a repeating trace and beacon animation, plus a reduced-motion fallback. The same mark is used as the browser icon.

Changed: `apps/web/src/App.tsx`, `apps/web/src/styles.css`, `apps/web/public/veytac-logo.svg`, `apps/web/public/veytac-mark.svg`, and `apps/web/index.html`. No API, provider, schema, or consent contract changed. The scan uses transform/opacity animation and glass blur is confined to small panels to limit work over the live video.

Verification: `npm run build` **PASS**; existing Playwright flows **PASS** (3/3). Desktop 1280 × 720 and phone 390 × 844 standby/live screenshots inspected; 320 × 568 standby inspected and adjusted. SVG favicon fetched through the HTTPS dev server with HTTP 200. Real phone/iPad rendering and frame-rate impact remain **NOT_RUN**.

Next: inspect the actual iPhone/iPad with camera active. Check safe-area spacing, long Japanese questions, a long transcript, reduced-motion behavior, logo animation, and capture frame rate. Do not infer real device performance from the desktop browser screenshots. No paid runtime call was made for this UI change.
