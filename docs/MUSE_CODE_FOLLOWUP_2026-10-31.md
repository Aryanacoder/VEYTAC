# Muse Code follow-up — local run and next verification

## Fix completed

Vite failed at `src/perceive/detector.ts` because `@mediapipe/tasks-vision` was declared in `apps/web/package.json` but missing from both the local `node_modules` install and the lockfile. Installed version `0.10.20` with npm, which updated `apps/web/package-lock.json`. Vite now resolves the import and builds the vision bundle. The tracker still downloads pinned WASM and model assets at first use; their actual download, browser compatibility, and detection quality have not been tested.

The Playwright live-view test expected an insecure-context warning on localhost. Chromium treats localhost as a secure context, so `apps/web/e2e/live.spec.ts` now verifies secure-context status and the normal no-warning render.

## Checks observed on this machine

- `npm run build`: PASS; Vite transformed 39 modules and produced the vision bundle.
- `npm run test:perceive`: PASS, 5 tests.
- `npm run smoke:chromium`: PASS, Live and Review render.
- `npm run test:e2e`: PASS, 1 test after correcting its stale expectation.
- `python -m pytest tests/ -q -p no:cacheprovider`: PASS, 44 passed and 2 skipped. The skipped tests require live Meta access.
- `python -m veytac.cli doctor`: PASS, mock mode; Python 3.11.9, FFmpeg, Node, npm, and API dependencies found.
- Local FastAPI `GET /api/v1/health`: PASS, `execution_mode=mock`.
- Vite dev server transformed `/src/perceive/detector.ts`: HTTP 200; `/api/v1/health` proxy: HTTP 200.

## Muse Code next actions

1. From a fresh checkout, run `npm ci` in `apps/web`, then `npm run build` and `npm run test:e2e`. Confirm the lockfile contains `@mediapipe/tasks-vision@0.10.20` and that the package is installed. Do not rely on the current machine's `node_modules`.
2. Test the tracker on an actual approved camera session over HTTPS or localhost. Record whether both pinned model URLs and the WASM files load, whether GPU delegate initialization works on the target browser, and whether `NullTracker` reports failures honestly. This is needed for FR-02/FR-08 and V-CAP-02/V-ENV-02.
3. Run a consented real capture → Meta observation → question → spoken/typed answer → review → episode/lesson/export flow. Record mode, model, spend, timings, artifact IDs, and human review. Mocked tests do not satisfy G2 or G3. No paid call without the project cost gate.
4. Audit the review endpoint's authority before external use: `reviewer_id` is supplied in the request body. Confirm authenticated reviewer identity and permission checks at the API boundary (G1/G3); do not treat an arbitrary claimed reviewer ID as human authorization.
5. Update `docs/IMPLEMENTATION_STATUS.md` with current observed commands and results once the real device/provider checks run. Keep robot learning status separate until genuine action/state data and controlled evaluation exist.

## Question delivery fix (later on 2026-10-31)

The frontend sent `performance.now()` to `/questions/deliver`, while the API compares `now_ms` to a Unix wall-clock question-window expiry. The gate therefore rejected real browser delivery as expired. `apps/web/src/App.tsx` now sends `Date.now()`, only starts its 45-second cooldown after successful delivery, retries when a new observation arrives, and visibly closes the 30-second question window. A local mock API smoke flow produced an observation, candidate question, and `delivered=true`. Build, one Playwright UI test, and 44 backend tests pass; two paid-provider tests remain skipped. Verify the entire camera-to-spoken-question path in a real browser, then run a separately approved live Meta session. The current `.env` remains in mock mode, so model-generated live questions have not been verified.

## Handoff

Changed files: `apps/web/package-lock.json`, `apps/web/e2e/live.spec.ts`, this note. Requirement focus: FR-02, FR-08, FR-28 and verification G0/G2. Cost incurred by these checks: no paid API or training call; a local Playwright Chromium download and npm package install. Unresolved blockers: real camera/model asset smoke test, real Meta call, human review/auth gate, held-out evaluation, and robot learning evidence. No release claim follows from the mock checks.
