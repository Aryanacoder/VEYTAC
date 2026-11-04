# Muse Code follow-up — voice and autonomous questions (2026-11-04)

## What changed

- Start now asks a spoken task-brief question before model follow-ups. The spoken answer is saved to `/sessions/{id}/task-brief` and becomes live Meta observation/question context.
- The consent sheet selects English, Japanese, or experimental Mandarin and explicitly approves up to 10 minutes of spoken questions. Mute/Stop revoke that gate. The backend still enforces question count/cooldown.
- Fixed immediate TTS cancellation, voice relay readiness handshake, AudioWorklet graph connection, visible speech errors, and duplicated interim transcripts.
- Listening now begins after each spoken prompt finishes, avoiding self-transcription; Mute/Stop invalidate the pending callback. A browser speech watchdog surfaces playback failure and resumes listening.
- Added an 8-second bounded model context refresh for small objects not recognized by the generic on-device detector. A 402/502 pauses frame requests for the session.

## Real evidence still needed

1. Run a consented safe English session with a real iPad or pen. Record screen video, audible opening question, original spoken task brief, unreviewed observation objects, a delivered follow-up, final transcript, model usage, cost, and timing. Do not infer arbitrary object detection from the colored generic boxes.
2. Repeat in Japanese on the owner's actual phone/iPad. Check browser TTS voice availability, Meta voice relay `hello` and finalized speech, generated Japanese follow-up, and reviewer-corrected transcript. Mandarin remains experimental until a separate smoke test.
3. Verify a muted or stopped session sends no further audio or audible questions. Measure whether the 8-second fallback fits the session budget; adjust only with spend data and the existing cost gate.
4. If the relay fails, capture the backend error without secrets and confirm whether browser speech fallback actually works on that device. A browser mock does not establish real Meta ASR support.

Current status: code/mock flow **PASS** after verification; real provider/device/language performance **NOT_RUN**. No paid provider call was made by this change.

## Verification on 2026-11-04

- `python -m pytest tests/ -q -p no:cacheprovider`: **PASS**, 56 passed, 2 skipped.
- `npm run build` in `apps/web`: **PASS**.
- `VEYTAC_TEST_BASE_URL=https://YOUR_WIFI_IP:5173 npm run test:e2e` in `apps/web`: **PASS**, 3 browser tests.
- `python -m ruff check` on changed Python modules and integration test: **PASS**.
- Restarted the local backend and fetched `/api/v1/health` through the LAN HTTPS proxy: `status=ok`, `execution_mode=live`, `observation_contract=observation-inference-v2`, `interaction_contract=task-briefing-v1`.
- The configured live mode and healthy proxy do not prove a real provider response, microphone capture, speaker playback, or iOS trust. Those remain **NOT_RUN**.
