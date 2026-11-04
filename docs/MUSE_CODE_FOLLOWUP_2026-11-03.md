# Muse Code follow-up — live UI and voice (2026-11-03)

## Implemented and checked

- Single live camera screen: blue-white glass controls (Start, Stop, Mute), VEYTAC SVG mark, red moving observation scan, recording timer, visible question and spoken-answer transcript. Capture stops at the 15-minute hard cap. After Stop, the existing decision review/episode path remains available.
- Start asks for capture and external-processing consent separately, then opens a human-approved 30-second question window. Start reopens it during capture; Mute revokes it; Unmute opens a fresh window; Stop closes it. Check this against PRD FR-01/FR-11 before changing semantics.
- Initial camera frame is sent for observation as soon as ready; local tracking checks once per second, and steady scenes avoid repeated model calls. Browser voice WebSocket URL and Vite upgrade proxy are corrected. Automatic voice answer send uses current question and transcript refs.
- Offline checks: `npm run build` PASS, `npm run test:e2e` PASS (2 synthetic browser tests), `npm run smoke:chromium` PASS, `npm run test:perceive` PASS (5 tests), `python -m pytest tests/ -q -p no:cacheprovider` PASS (47 passed, 2 skipped), `python -m veytac.cli doctor` PASS and reported `execution_mode=live` without a paid call. Both direct `GET http://localhost:8000/api/v1/health` and Vite-proxied `GET http://localhost:5173/api/v1/health` returned `{"status":"ok","execution_mode":"live"}`; health does not prove provider availability. No paid API call or training run was made for these checks.

## Next evidence and code work

1. On a consented safe task, run the real camera and microphone with backend and Vite together. Capture the actual Meta observation, delivered question, spoken answer, review, episode, timing, and provider spend. Confirm mute/stop prevent further voice samples and question delivery. Record browser/device/codec and any errors. This is **NOT_RUN**; the synthetic test is not live-provider proof.
2. Check first-frame latency and tracker loading on the owner's device, including CDN failure and no-hand scenes. Verify the MediaPipe asset loads rather than inferring success from the TypeScript build. Log frame-to-question and question-to-answer timing before further optimization.
3. Test actual voice WebSocket upgrade through Vite and production HTTPS/Tailscale, including relay close, browser speech fallback, reconnection, and interruption. The automated test currently stubs SpeechRecognition and does not exercise the Meta voice socket.
4. Validate the consent notice and actor identity against real expert/workplace authority. Test the 15-minute stop on a real device and across interruptions. Check reviewer edit/reject/correction flows and the full permissioned export gates before claiming release readiness.
5. Treat Fireworks and Baseten as candidate runtime routes, not an existing fast path. Current code has a Fireworks SFT client and a Baseten deployment planner, while live inference uses Meta. Compare actual eligible models, contractual data handling, latency, cost, and provider failures under one server-side interface before choosing a route. Preserve meaningful Meta runtime use and spend gates. Do not launch training or paid calls on this note alone.

Status: UI/mock flow **PASS**; real provider, real voice socket, device and latency evidence **NOT_RUN**; production/release **BLOCKED** on those gates and human review. Cost incurred by this implementation/check: $0 provider spend (local development only).
