# Muse Code follow-up: live observation and learning (2026-11-04)

## Current implementation

The Meta ASR handshake and 80 ms audio framing were corrected; socket errors now reach the UI and browser speech can recover. Local hand/object models run in a classic worker on the tested Chromium LAN browser. Start asks for a spoken task brief; later grounded observations trigger questions with a 45-second retry. Stop ends recording and mic use while camera preview remains live. A reviewer can enter their ID and approved scope, then build a visible, persisted learning card.

The earlier live observation HTTP 400 about missing `required` fields has a strict-schema transform in `src/veytac/providers/strict.py`. Its unit test confirms every object property appears in `required`; that only proves the outgoing schema shape, not a successful real-provider call.

## Next code work

1. Add a versioned, evidence-linked hand-landmark sample schema with source stream ID, frame timestamp, coordinate basis, detector/model version, confidence, and uncertainty. Save bounded samples and include them in canonical export as **derived visual tracks**. Keep `action_aligned` false until actual robot action/state trajectories and calibration pass the separate gate. Do not infer joints, forces, or expert actions from 2D phone points.
2. Add a reviewer timeline with original permitted clips and transcript correction. A learning card is useful now, but the full PRD learner flow needs a question before revealing the answer, a contrasting case, and source/version links. Any simulation clip must be labeled with its engine, inputs, assumptions, and validation status; a generated animation is not physical simulation.
3. Prove Meta voice with a consented, cost-gated real session: log sanitized handshake result, final transcripts, disconnection/reconnect behavior, language, latency, and reserved/actual cost. Test English and Japanese on the owner's phone/iPad; Mandarin is experimental. Do not expose secrets or transcripts from proprietary work.
4. Check classic-worker and `OffscreenCanvas` support on Safari/iPadOS. If unsupported, design a bounded fallback that preserves question/audio responsiveness. Test actual local model detections with a hand, pen, and iPad; generic object-detector labels may be insufficient. Record misses honestly and use the existing provider observation path for context under the cost gate.
5. Test Start/Stop/Mute repeatedly, camera facing changes, tab backgrounding, WiFi loss, 15-minute cap, and returning to preview. Preserve capture gap and idempotency semantics.

## Verification boundary

Current mocked/offline checks: backend `67 passed, 2 skipped`; Playwright `3 passed`; local model tracker reached `seeing:` in Chromium, and the video track remained live after Stop. Real Meta provider, real camera/mic, iOS, physical simulation, and robot training are **NOT_RUN**. No paid API call or training job was made in this change.
