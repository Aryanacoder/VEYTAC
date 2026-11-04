# Muse Code follow-up — live repair (2026-11-04)

## Confirmed fixes

- Original provider 400 came from sending a full Pydantic `Observation` to Meta strict output. The model now receives only `ObservationInference`; the server assigns IDs, timestamps, and evidence. Health reports `observation_contract=observation-inference-v2` so a stale listener is visible. Offline mocked provider integration reaches a candidate question, with no invented live result.
- Two stale API listeners and two old Vite listeners were stopped. The current API is on `127.0.0.1:8000`; the current HTTPS Vite server is on `0.0.0.0:5173`, with `/api` and WebSocket proxying. The verified LAN URL is `https://YOUR_WIFI_IP:5173` at this IP. The generated certificate and key are ignored by Git.
- Vite 5 rejected the old `--https` script. `npm run cert:lan` plus `npm run dev:https` now starts IP-bound HTTPS. On iPhone/iPad the owner must install `apps/web/.certs/lan-ca.crt` and explicitly enable full root trust before using camera/microphone. Never copy the private `.key` file.
- On-device detector inference failures now surface instead of becoming false zero detections; Meta observations remain a timed fallback. Visible model observation text is labeled unreviewed. The generic detector still only covers its supported classes; industrial tool boxes need a separately validated model. Recorder MIME selection now includes Safari MP4.

## Evidence and next gate

- `python -m pytest tests/ -q -p no:cacheprovider`: **PASS**, 56 passed, 2 skipped.
- `npm run test:perceive`: **PASS**, 10 tests. `npm run build`: **PASS**.
- Playwright browser tests on the HTTPS LAN IP with mocked API/camera: **PASS**, 2 tests.
- `ruff check` on modified Python files: **PASS**. A trusted-CA HTTPS request through Vite returned live health and the new contract version. These checks incurred **$0 provider spend**.
- **NOT_RUN:** a real Meta frame/question/voice round trip after this repair, physical iPhone/iPad CA installation and capture, and recognition of a real industrial object. Run one consented safe session with a visible tool, record the question, transcript, latency, model usage/cost, browser/device, and backend errors. Do not turn these mock tests into a live-performance claim.
