# VEYTAC implementation status

Track milestone state and evidence. A claimed completion without logs is not sufficient.

| Milestone | Status | Evidence |
|---|---|---|
| M0 reality check | IN_PROGRESS | Python 3.11.9, Node v24.19.0, ffmpeg 8.1 present. Demo: live task (flexible), expert answers live. Baseten/Fireworks/Modal credits available. $150 Meta for coding + SAM/smart models. UI: Playwright + Chromium. |
| M1 contracts + mocks | IN_PROGRESS | Scaffold + canonical schemas (this change). |
| M2 capture-to-question slice | NOT_STARTED | — |
| M3 review + persistent expertise | NOT_STARTED | — |
| M4 lesson + controlled sharing | NOT_STARTED | — |
| M5 learning + evaluation | NOT_STARTED | Stage 2 (after core). Robot/SFT via partner credits. |
| M6 release + rehearsal | NOT_STARTED | — |

## Verification state

- Backend: **28 passed** (`python -m pytest tests/`, observed 2026-10-31):
  schemas/budget/gates/mocks/verifiers/transfer/stage-2 (26) + capture→answer
  and review→episode→export→lesson flows (2 integration, route-direct since
  the sandbox forbids TestClient sockets).
- Export round-trip proven: API-written bundle validates via
  `veytac validate-episode` (checksums ok, caps honest).
- CLI dry-runs: `eval-apprentice` / `train-robot` refuse non-dry-run without
  an approval record; status `ROBOT_LEARNING_NOT_DEMONSTRATED` until G6/G7.
- Partner lanes (decision 0002, unlimited Glimmer LoRA + Baseten): SFT example
  builder with session-grouped splits, Fireworks LoRA plan/launch (approval +
  non-empty data required), Baseten scale-to-zero deployment plans.
  **31 passed.** Hosting runbook in `docs/HOSTING.md` (PC rehearsal, LAN phone
  via HTTPS/Tailscale, open-source self-host).
- Live Meta lane (option b): real Chat Completions adapter with structured
  output, per-session budget reserve/reconcile, no silent mock fallback
  (live failure → stored 502, budget holds the call). Frontend now sends real
  frame pixels. Contract tests skip without key (`VEYTAC_LIVE_CONTRACT=1`).
  **33 passed, 2 skipped (live).** Reviewed-session checklist in
  `docs/DEMO_DATASET_CHECKLIST.md` — yes to open-source data for
  commentary-structure and robot baselines, with attribution limits.
- Voice-first loop (S8): questions are spoken aloud, answers heard by mic
  with live interim text and auto-send on pause; typing stays as fallback.
  No more canned "action in this window" — gaps derive from each
  observation's own words (mock-labeled until the Meta key lands), and the
  app auto-asks while the question window is open. **36 passed, 2 skipped.**
- Live perception + voice (decision 0003): on-device MediaPipe tracker
  (hands + EfficientDet objects, ~5fps @320px, free) fires change events;
  frames reach the paid model only on events with a stored `trigger`
  (15s timed fallback when tracking is unavailable). Voice answers prefer
  the Meta realtime ASR relay (`/api/v1/sessions/{id}/voice`, ENDPOINTING,
  24kHz PCM, budget-reserved) with TTS barge-in; browser speech is
  fallback. **44 passed, 2 skipped; perceive 5/5; typecheck clean; jsdom
  smoke PASS.** Live relay + tracking NOT_RUN here (sandbox blocks
  sockets/browser launch) — owner's keyed rehearsal is the first live run.
  Owner runs `npm install` on a dev machine for `@mediapipe/tasks-vision`.
- Follow-up run (docs/MUSE_CODE_FOLLOWUP_2026-10-31.md, other machine):
  `npm run build`, `test:perceive` (5), `smoke:chromium`, and `test:e2e`
  (1, after fixing the spec's stale insecure-context expectation) all
  reported PASS there; lockfile now pins `@mediapipe/tasks-vision@0.10.20`
  (confirmed present in this tree). This session independently re-verified
  only the lockfile entry and the updated spec text — the build/e2e
  passes are single-source until reproduced. Still open: real-camera
  tracker smoke, first paid Meta call, human review, held-out
  evaluation, robot evidence.
- Review authority audit (this session, code-read): `POST
  /api/v1/decisions/{id}/reviews` accepts a free-text `reviewer_id` with
  no login, token, or permission check anywhere in the API. Anyone
  reaching the backend can approve as anyone. Acceptable for localhost
  rehearsal only. Do not expose :8000 beyond loopback without the TRD-8
  auth slice; serve the phone via the Vite HTTPS origin, never the API
  port directly.
- Backend rehearsal fix: no code ever loaded `.env`, so the server
  silently ignored the key/mode/paid-flags (always mock). `veytac serve`
  and `doctor` now load repo-root `.env` (explicit env wins);
  `python-dotenv` added to dependencies. Proven: `doctor` prints the
  loaded file + mode. **46 passed, 2 skipped.** UI untouched (Codex lane).
- Follow-up run (docs/MUSE_CODE_FOLLOWUP_2026-11-03.md, Codex/UI lane):
  single live screen (Start/Stop/Mute), separate capture + processing
  consent, 30s question window with Mute revoke, first-frame observation,
  1s tracking cadence, Vite `ws:true` proxy, refs-based auto-send. This
  session re-verified in-tree (2026-11-03): backend **47 passed, 2
  skipped**; `doctor` reports `mode=live` ($0 spend, no call made); `.env`
  holds key + live + paid-true; Mute/15-min-cap/separate-consent/1s-loop
  all present. Build/e2e/smoke/health-endpoint passes remain
  single-source (sandbox cannot run them). Real camera/mic run, voice
  socket upgrade, latency, and human review still **NOT_RUN**. Owner field
  report (phone): front camera by default, zero detections drawn, slow
  tracking. Fixed: rear camera default + Rear/Front flip on standby
  (session-safe), GPU→CPU delegate fallback so weak phones track slowly
  instead of dying silently, smoke harness fixed (it asserted the notice
  before the effect pass — polls for the notice now). **tsc clean;
  perceive 11/11; smoke PASS consecutive.** If highlights are still
  absent, the status line under the video names the cause (`tracker
  library not installed` = run `npm install`; model-download note = wait
  for the ~12MB fetch). 2026-11-03
  number superseded: **backend 66 passed/2 skipped; perceive 11/11** after
  the SAM lane (decision 0005): sam-3.1 Responses client, documented box
  grammar builder/parser, official meta-sam-parser decode when installed
  (opaque otherwise), event-frame wiring with budget guards, client box
  prompts + SAM overlay layer. Mask fills + video tracking await the
  first live run (placement and request keys flagged for verification).
- 2026-11-04 UI rework (docs/MUSE_CODE_FOLLOWUP_2026-11-04-UI.md, Codex
  lane): blue/white glass system, SVG mark + favicon, small-panel blur,
  transform/opacity scan, reduced-motion fallback. Re-verified here:
  typecheck clean, smoke PASS on fresh bundle, perceive 11/11, backend
  66/2, overlay wiring + legend intact, e2e spec holds 3 tests
  (Playwright run itself is single-source — no browser here). One fix
  from reconciliation: overlay box colors realigned to the restyled
  legend swatches. Device rendering, frame rate, safe-area, Japanese,
  long transcript remain owner-machine checks.
- Repeat 502 with identical message = stale server, not a new bug: the
  transform output is provably correct, so the running backend predates
  the fix. `serve` now logs `strict-schema=2026-11-04`; no marker means
  pull + restart. Same-WiFi phone/tablet path documented (relative URLs
  only; `npm run dev:https` + accept-cert + firewall). Tracker upgraded:
  21-dot hand skeletons, 0.25 threshold / 10 results for small objects,
  4fps overlay loop with 1s event throttle, cover-crop-aligned boxes.
  **Backend 53/2; perceive 10/10; typecheck clean; smoke PASS.**
- 2026-11-04 owner live report (screenshot): frames 502'd — provider HTTP
  400, strict schema missing `required`/unresolved `$ref`. Fixed in
  `src/veytac/providers/strict.py` at the `LiveMetaClient` choke point
  (decision 0004); structural tests prove raw-fail/transformed-pass.
  Same turn shipped the requested detection overlay (blue person/hand,
  red objects, motion trails, motion-burst events, cover-crop-aligned,
  reduced-motion aware) and rewrote the jsdom smoke for the current UI.
  **Backend 53 passed/2 skipped; perceive 10/10; typecheck clean; smoke
  PASS.** Live-provider proof of the fix is the owner's next run.
- Schemas: **17 JSON schemas exported** to `schemas/json`.
- `veytac doctor`: ok (python 3.11.9, ffmpeg/ffprobe/node/npm found, mock mode).
- Frontend typecheck: clean (`tsc --noEmit`).
- UI render smoke: **PASS** via jsdom (`apps/web/smoke/dom.smoke.mjs`):
  brand, secure-context notice (no crash without camera), single Start
  control, Review tab. UI slimmed to sleek glass per owner review.
- Real Chromium pass: **CHROMIUM PASS** (`npm run smoke:chromium`) — app
  served from disk via request interception (no sockets in sandbox), Live +
  Review render with zero page errors, screenshots in `output/playwright/`.
  UI reviewed against ui-ux-pro-max skill (single live region, visible
  focus rings, 44px targets, labeled answer input).
- Sandbox limits (this machine only, not product defects): listening sockets
  blocked (`bind` → PermissionError), so vite dev, python http.server, and the
  FastAPI server cannot start here; esbuild/vite fail scanning parents above
  the workspace. The Playwright Chromium spec (`apps/web/e2e/live.spec.ts`)
  is written but **NOT_RUN** here — run it on a dev machine/CI with
  `npm run test:e2e`. No paid provider call has been made. Execution: `mock`.
